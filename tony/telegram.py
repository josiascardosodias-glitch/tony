"""`tony telegram`: o Tony no Telegram, e a coleta de hora em hora no mesmo processo.

- Só responde ao seu chat (`TELEGRAM_CHAT_ID`); mensagem de qualquer outro é ignorada.
- Pergunta de agenda ("o que tenho sexta?") é respondida pelo código (`consulta.py`): zero token.
- Pergunta livre vai ao modelo, com a personalidade e a agenda dos próximos 30 dias (nunca o e-mail).
- Data de confiança média chega com os botões Aceitar e Descartar.
- Se a autorização do Google vencer, avisa (uma vez por dia) como renovar.

A API do Telegram é chamada direto por HTTP (`httpx`): long polling no `getUpdates`, sem biblioteca de
bot. O token vai na URL, então nenhum erro mostra a URL: `ErroDoTelegram` tira o token da mensagem.
"""

import time
from datetime import date, datetime, timedelta

import httpx

from . import config, google
from .agenda import decidir, sincronizar
from .cliente import Cliente, ErroDoModelo
from .coleta import coletar, ler_json, salvar_json
from .consulta import eh_de_agenda, para_o_modelo, responder
from .conversa import Conversa
from .memoria import carregar_personalidade, ler_inteligencia
from .registro import Registro

AJUDA = """Pode perguntar do jeito que quiser: "o que tenho amanhã?", "e sexta?", "semana que vem".

/hoje · /semana · /proximos — o que está marcado
/revisar — as datas que eu não tive certeza
/coletar — olhar os e-mails agora
/nova — esquecer esta conversa"""


class ErroDoTelegram(Exception):
    pass


class Telegram:
    def __init__(self, token: str, chat_id: int, http: httpx.Client | None = None):
        self._token = token
        self.chat_id = chat_id
        self.http = http or httpx.Client(timeout=70)

    def chamar(self, metodo: str, **dados):
        try:
            r = self.http.post(f"https://api.telegram.org/bot{self._token}/{metodo}", json=dados)
            resposta = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise ErroDoTelegram(str(e).replace(self._token, "<token>")) from None
        if not resposta.get("ok"):
            raise ErroDoTelegram(f"{metodo}: {resposta.get('description', 'erro sem descrição')}")
        return resposta["result"]

    def enviar(self, texto: str, botoes: list | None = None) -> dict:
        dados = {"chat_id": self.chat_id, "text": texto[:4000]}
        if botoes:
            dados["reply_markup"] = {"inline_keyboard": botoes}
        return self.chamar("sendMessage", **dados)


def credenciais(cfg: dict) -> tuple[str, int]:
    t = cfg["telegram"]
    token = config.caminho(t["token_arquivo"]).read_text(encoding="utf-8").strip()
    valores = {}
    for linha in config.caminho(t["contas_arquivo"]).read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip().strip("'\"")
    if not valores.get("TELEGRAM_CHAT_ID"):
        raise SystemExit("falta o TELEGRAM_CHAT_ID: rode scripts/assistente-telegram.sh")
    return token, int(valores["TELEGRAM_CHAT_ID"])


MAXIMO_DE_UMA_VEZ = 3  # mais datas novas que isso numa coleta viram uma mensagem só


def botoes(id_: str) -> list:
    return [[{"text": "✅ Aceitar", "callback_data": f"aceitar:{id_}"},
             {"text": "🗑 Descartar", "callback_data": f"descartar:{id_}"}]]


class Bot:
    def __init__(self, cfg: dict, telegram: Telegram, gmail=None, agenda=None, cliente=None):
        self.cfg = cfg
        self.telegram = telegram
        self._gmail, self._agenda, self._cliente = gmail, agenda, cliente  # nos testes, falsos
        t = cfg["telegram"]
        self.arquivo_estado = config.caminho(t["estado"])
        self.estado = ler_json(self.arquivo_estado, {"offset": 0, "avisados": [], "avisos_autorizacao": {},
                                                     "ultima_coleta": None})
        self.coletar_a_cada = timedelta(minutes=t["coletar_a_cada_min"])
        self.esquecer_apos = timedelta(minutes=t["conversa_esquece_apos_min"])
        self.conversa: Conversa | None = None
        self.ultima_fala: datetime | None = None
        self.registro = Registro(config.caminho(cfg["logs"]), origem="telegram")

    # --- Serviços do Google: criados na hora, porque a autorização pode ter vencido -------------------

    def fonte(self, conta: dict):
        if self._gmail:
            return self._gmail
        from .contas import fonte_da_conta

        return fonte_da_conta(self.cfg, conta)

    def agenda(self):
        return self._agenda or google.servico(self.cfg, "calendar", "v3")

    def salvar(self) -> None:
        self.estado["avisados"] = self.estado["avisados"][-2000:]
        salvar_json(self.arquivo_estado, self.estado)

    def eventos(self) -> dict:
        return ler_json(config.caminho(self.cfg["coleta"]["eventos"]), {"eventos": {}, "revisar": {}})

    # --- Coleta ------------------------------------------------------------------------------------

    def hora_de_coletar(self, agora: datetime) -> bool:
        ultima = self.estado["ultima_coleta"]
        return not ultima or agora - datetime.fromisoformat(ultima) >= self.coletar_a_cada

    def rodar_coleta(self, agora: datetime, avisar_vazio: bool = False) -> None:
        """Coleta todas as contas e leva para a agenda. Uma conta com problema não para as outras."""
        self.estado["ultima_coleta"] = agora.isoformat(timespec="seconds")
        self.salvar()
        antes = set(self.eventos()["eventos"])
        lidos = 0
        for conta in google.contas(self.cfg):
            try:
                lidos += coletar(self.cfg, self.fonte(conta), conta=conta)["emails"]
            except google.AutorizacaoVencida as e:
                self.avisar_autorizacao(conta["nome"], e, agora, sempre=avisar_vazio)
            except Exception as e:  # sem rede ou erro do Google: a próxima coleta tenta de novo
                print(f"[aviso] a coleta de {conta['nome']} falhou: {e}")
                if avisar_vazio:
                    self.telegram.enviar(f"A coleta de {conta['nome']} falhou agora ({e}). Tento de novo na próxima.")
        try:
            sincronizar(self.cfg, self.agenda())
        except google.AutorizacaoVencida as e:
            self.avisar_autorizacao(google.contas(self.cfg)[0]["nome"], e, agora, sempre=avisar_vazio)
        except Exception as e:
            print(f"[aviso] a agenda falhou: {e}")
        banco = self.eventos()
        novos = [e for i, e in banco["eventos"].items() if i not in antes]
        if novos:
            linhas = "\n".join(f"• {e['data'][8:]}/{e['data'][5:7]}{', ' + e['hora'] if e['hora'] else ''} — {e['titulo']}"
                               for e in sorted(novos, key=lambda e: (e["data"], e["hora"] or "")))
            self.telegram.enviar(f"Pus na agenda:\n{linhas}")
        self.avisar_revisar(banco)
        if avisar_vazio and not novos:
            self.telegram.enviar(f"Olhei {lidos} e-mail(s) novo(s): nada para a agenda.")

    def avisar_autorizacao(self, conta: str, erro: Exception, agora: datetime, sempre: bool = False) -> None:
        """Uma vez por dia por conta (ou sempre, num /coletar): como renovar a autorização."""
        avisos = self.estado.setdefault("avisos_autorizacao", {})
        if avisos.get(conta) == agora.date().isoformat() and not sempre:
            return
        self.telegram.enviar(f"Não consegui olhar os e-mails de {conta}: {erro}.\n\nNo PC, na pasta de produção "
                             "(cd ~/projetos/tony-producao), rode o comando acima.")
        avisos[conta] = agora.date().isoformat()
        self.salvar()

    def avisar_revisar(self, banco: dict | None = None, todas: bool = False) -> None:
        """Cada data de confiança média chega uma vez, com os botões. Muitas de uma vez (a primeira coleta,
        uma leva de marketing) viram uma mensagem só, e o /revisar mostra uma por uma."""
        banco = banco or self.eventos()
        hoje = date.today().isoformat()
        novas = [(i, e) for i, e in sorted(banco["revisar"].items(), key=lambda par: par[1]["data"])
                 if i not in self.estado["avisados"] and e["data"] >= hoje]
        if len(novas) > MAXIMO_DE_UMA_VEZ and not todas:
            self.telegram.enviar(f"Tenho {len(novas)} datas que não sei se são compromisso. Mande /revisar para ver "
                                 "uma por uma (se for só propaganda de um remetente, dá para bloquear no PC: uv run tony bloquear @dominio).")
            self.estado["avisados"] += [i for i, _ in novas]
            self.salvar()
            return
        for id_, e in novas:
            hora = f" às {e['hora']}" if e["hora"] else ""
            self.telegram.enviar(f"Isto é compromisso?\n\n{e['titulo']}\n{e['data'][8:]}/{e['data'][5:7]}{hora}\n"
                                 f"{e['descricao'].splitlines()[0][:200]}\n(de {e['remetente']})", botoes(id_))
            self.estado["avisados"].append(id_)
            self.salvar()

    # --- Mensagens ---------------------------------------------------------------------------------

    def tratar(self, atualizacao: dict, agora: datetime) -> None:
        if "callback_query" in atualizacao:
            return self.botao(atualizacao["callback_query"])
        mensagem = atualizacao.get("message") or {}
        if mensagem.get("chat", {}).get("id") != self.telegram.chat_id:
            self.registro.anotar("ignorado", chat=mensagem.get("chat", {}).get("id"))
            return
        texto = (mensagem.get("text") or "").strip()
        if not texto:
            return
        resposta = self.responder(texto, agora)
        if resposta:
            self.telegram.enviar(resposta)
            self.registro.turno_completo(texto, resposta, 0)

    def responder(self, texto: str, agora: datetime) -> str:
        hoje = agora.date()
        eventos = list(self.eventos()["eventos"].values())
        comando = texto.split()[0].split("@")[0].lower() if texto.startswith("/") else ""
        if comando in ("/start", "/ajuda", "/help"):
            return AJUDA
        if comando in ("/hoje", "/semana", "/proximos"):
            return responder({"/hoje": "hoje", "/semana": "essa semana", "/proximos": "o mês"}[comando], eventos, hoje)
        if comando == "/revisar":
            pendentes = [i for i, e in self.eventos()["revisar"].items() if e["data"] >= hoje.isoformat()]
            self.estado["avisados"] = [i for i in self.estado["avisados"] if i not in pendentes]
            self.avisar_revisar(todas=True)
            return "" if pendentes else "Nada para revisar."
        if comando == "/coletar":
            self.rodar_coleta(agora, avisar_vazio=True)
            return ""
        if comando == "/nova":
            self.conversa = None
            return "Conversa nova."
        if comando:
            return "Não conheço esse comando. /ajuda mostra o que eu faço."
        if eh_de_agenda(texto, hoje):
            return responder(texto, eventos, hoje)
        return self.conversar(texto, eventos, agora)

    def conversar(self, texto: str, eventos: list[dict], agora: datetime) -> str:
        """O único caminho que gasta token: pergunta que não é de agenda."""
        if not self.conversa or not self.ultima_fala or agora - self.ultima_fala > self.esquecer_apos:
            self.conversa = Conversa(
                self._cliente or Cliente(self.cfg), self.cfg["contexto"]["limite"],
                carregar_personalidade(config.caminho(self.cfg["personalidade"])),
                ler_inteligencia(config.caminho(self.cfg["memoria"]["inteligencia"])),
                agenda=para_o_modelo(eventos, agora.date()))
        self.ultima_fala = agora
        try:
            return "".join(p for p in self.conversa.responder(texto) if isinstance(p, str)).strip()
        except ErroDoModelo as e:
            return f"Não consegui falar com o modelo agora ({e}). Perguntas de agenda continuam funcionando."

    def botao(self, clique: dict) -> None:
        mensagem = clique.get("message") or {}
        if mensagem.get("chat", {}).get("id") != self.telegram.chat_id:
            return
        acao, _, id_ = clique.get("data", "").partition(":")
        resultado = decidir(self.cfg, id_, acao == "aceitar")
        if acao == "aceitar" and resultado.startswith("aceito"):
            try:
                sincronizar(self.cfg, self.agenda())
                resultado += " Está na agenda."
            except google.AutorizacaoVencida:
                resultado += " Vai para a agenda quando a autorização do Google for renovada."
        self.telegram.chamar("answerCallbackQuery", callback_query_id=clique["id"], text=resultado[:190])
        self.telegram.chamar("editMessageText", chat_id=self.telegram.chat_id, message_id=mensagem["message_id"],
                             text=f"{mensagem.get('text', '')}\n\n→ {resultado}")

    # --- Laço --------------------------------------------------------------------------------------

    def uma_volta(self) -> None:
        agora = datetime.now().astimezone()
        if self.hora_de_coletar(agora):
            self.rodar_coleta(agora)
        for atualizacao in self.telegram.chamar("getUpdates", offset=self.estado["offset"], timeout=50,
                                                allowed_updates=["message", "callback_query"]):
            self.estado["offset"] = atualizacao["update_id"] + 1
            self.salvar()  # antes de tratar: uma mensagem que derruba o Tony não volta em loop
            self.tratar(atualizacao, datetime.now().astimezone())


def rodar(cfg: dict) -> None:
    token, chat_id = credenciais(cfg)
    bot = Bot(cfg, Telegram(token, chat_id))
    print(f"Tony no Telegram: respondendo só ao chat {chat_id}. Ctrl+C para parar.")
    while True:
        try:
            bot.uma_volta()
        except (ErroDoTelegram, httpx.HTTPError) as e:  # sem rede: espera e tenta de novo
            print(f"[aviso] {e}; tento de novo em 30 s")
            time.sleep(30)
        except KeyboardInterrupt:
            return
