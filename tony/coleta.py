"""`tony coletar`: busca os e-mails novos no Gmail, acha as datas e guarda no `eventos.json`. Sem IA.

O caminho de um e-mail:
1. A busca do Gmail já pede só o que chegou depois da última coleta, tira os remetentes de
   `bloqueados.json` (`-from:`) e aplica o `coleta.filtro` (por padrão, sem Promoções e Social).
   E-mail bloqueado nem é baixado.
2. O cabeçalho From é conferido de novo contra os bloqueados (a busca do Gmail é por palavra).
3. As datas saem do assunto, do corpo e dos convites `.ics` (`datas.py`).
4. Confiança alta vira evento; média vai para `revisar`, para você decidir; baixa é descartada.
"""

import base64
import html
import json
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from email.utils import parseaddr
from pathlib import Path

from . import config
from .datas import Data, achar_datas, datas_do_ics

VISTOS_GUARDADOS = 5000  # ids de e-mails já processados que o estado guarda (os mais recentes)
PENALIDADE_EM_MASSA = 0.4  # e-mail em massa perde confiança: "até amanhã às 23h59!" (0.9) cai para revisar (0.5)
SALVAR_A_CADA = 25       # e-mails: uma coleta que cai no meio recomeça daqui, sem baixar tudo de novo
ESPERAS = (2, 5, 15, 30, 60, 60)  # segundos entre as tentativas quando o Gmail pede calma (limite por minuto)


def executar(pedido, esperar=time.sleep):
    """`pedido.execute()`, esperando e tentando de novo quando o Gmail recusa por limite (429, ou 403
    com rateLimitExceeded) ou falha do lado dele (5xx)."""
    from googleapiclient.errors import HttpError

    for espera in (*ESPERAS, None):
        try:
            return pedido.execute()
        except HttpError as e:
            limite = e.resp.status == 429 or (e.resp.status == 403 and "rateLimitExceeded" in str(e.content))
            if espera is None or not (limite or e.resp.status >= 500):
                raise
            esperar(espera)


@dataclass
class Mensagem:
    id: str
    de: str          # o endereço, em minúsculas
    nome: str        # o nome de quem mandou, se veio
    assunto: str
    recebido: datetime
    texto: str
    trecho: str      # o snippet que o próprio Gmail entrega
    convites: list[str] = field(default_factory=list)  # o texto de cada .ics
    email_da_conta: str = ""  # para o link abrir na conta certa quando há mais de uma
    em_massa: bool = False  # tem List-Unsubscribe ou Precedence: bulk (newsletter, marketing, alerta de vaga)

    @property
    def link(self) -> str:
        if self.email_da_conta:
            return f"https://mail.google.com/mail/u/?authuser={self.email_da_conta}#all/{self.id}"
        return f"https://mail.google.com/mail/u/0/#all/{self.id}"


# --- Bloqueados -----------------------------------------------------------------------------------

def ler_bloqueados(arquivo: Path) -> dict:
    """{"enderecos": [...], "dominios": [...]}; cria o arquivo vazio na primeira vez."""
    if not arquivo.is_file():
        salvar_json(arquivo, {"enderecos": [], "dominios": []})
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    return {"enderecos": [e.lower() for e in dados.get("enderecos", [])],
            "dominios": [d.lower().lstrip("@") for d in dados.get("dominios", [])]}


def bloqueado(endereco: str, bloqueados: dict) -> bool:
    endereco = endereco.lower()
    dominio = endereco.rpartition("@")[2]
    return endereco in bloqueados["enderecos"] or any(
        dominio == d or dominio.endswith("." + d) for d in bloqueados["dominios"])


def bloquear(arquivo: Path, alvo: str) -> str:
    """Acrescenta um endereço (fulano@x.com) ou um domínio (@x.com) aos bloqueados."""
    dados = ler_bloqueados(arquivo)
    alvo = alvo.strip().lower()
    if alvo.startswith("@") or "@" not in alvo:
        chave, valor = "dominios", alvo.lstrip("@")
    else:
        chave, valor = "enderecos", alvo
    if valor in dados[chave]:
        return f"{valor} já estava bloqueado."
    dados[chave].append(valor)
    salvar_json(arquivo, dados)
    return f"bloqueado: {valor} ({'domínio' if chave == 'dominios' else 'endereço'})."


def consulta(filtro: str, bloqueados: dict, depois_de: datetime) -> str:
    """A busca do Gmail: depois da data, com o filtro e sem os bloqueados."""
    partes = [f"after:{int(depois_de.timestamp())}", filtro]
    partes += [f"-from:{e}" for e in bloqueados["enderecos"]]
    partes += [f"-from:{d}" for d in bloqueados["dominios"]]
    return " ".join(p for p in partes if p)


# --- Gmail ----------------------------------------------------------------------------------------

def _decodificar(dados: str) -> str:
    return base64.urlsafe_b64decode(dados + "=" * (-len(dados) % 4)).decode("utf-8", errors="replace")


def _sem_html(texto: str) -> str:
    texto = re.sub(r"<(script|style).*?</\1>", " ", texto, flags=re.S | re.I)
    texto = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", texto, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", texto))


def _partes(parte: dict):
    yield parte
    for filha in parte.get("parts", []):
        yield from _partes(filha)


def ler_mensagem(servico, bruta: dict) -> Mensagem:
    """Uma mensagem do Gmail (formato `full`) em texto: o text/plain, ou o HTML sem as tags."""
    cabecalhos = {c["name"].lower(): c["value"] for c in bruta["payload"].get("headers", [])}
    nome, endereco = parseaddr(cabecalhos.get("from", ""))
    texto = {"text/plain": "", "text/html": ""}
    convites = []
    for parte in _partes(bruta["payload"]):
        tipo, corpo = parte.get("mimeType", ""), parte.get("body", {})
        dados = corpo.get("data")
        if not dados and corpo.get("attachmentId") and tipo == "text/calendar":
            dados = executar(servico.users().messages().attachments().get(
                userId="me", messageId=bruta["id"], id=corpo["attachmentId"]))["data"]
        if not dados:
            continue
        if tipo == "text/calendar" or parte.get("filename", "").lower().endswith(".ics"):
            convites.append(_decodificar(dados))
        elif tipo in texto and not texto[tipo]:
            texto[tipo] = _decodificar(dados)
    corpo = texto["text/plain"] or _sem_html(texto["text/html"])
    return Mensagem(
        id=bruta["id"], de=endereco.lower(), nome=nome, assunto=cabecalhos.get("subject", "").strip(),
        recebido=datetime.fromtimestamp(int(bruta["internalDate"]) / 1000, tz=timezone.utc).astimezone(),
        texto=re.sub(r"[ \t\r\f\v]+", " ", corpo).strip(), trecho=html.unescape(bruta.get("snippet", "")),
        convites=convites,
        em_massa="list-unsubscribe" in cabecalhos or cabecalhos.get("precedence", "").lower() in ("bulk", "list"),
    )


def buscar(servico, q: str) -> list[str]:
    """Os ids de todas as mensagens da busca, página por página."""
    ids, pagina = [], None
    while True:
        r = executar(servico.users().messages().list(userId="me", q=q, pageToken=pagina, maxResults=100))
        ids += [m["id"] for m in r.get("messages", [])]
        pagina = r.get("nextPageToken")
        if not pagina:
            return ids


# --- Eventos --------------------------------------------------------------------------------------

def titulo(assunto: str) -> str:
    """O assunto sem Re:/Fwd:/[etiqueta]: é o que aparece na agenda."""
    limpo = re.sub(r"^\s*((re|res|fw|fwd|enc|tr)\s*:\s*|\[[^\]]*\]\s*)+", "", assunto, flags=re.I).strip()
    return limpo or "(sem assunto)"


def evento(msg: Mensagem, data: Data, n: int, conta: str, prefixo: str = "") -> dict:
    descricao = data.frase
    if msg.trecho and msg.trecho not in data.frase:
        descricao += f"\n\n{msg.trecho}"
    return {
        "id": f"{prefixo}{msg.id}-{n}", "email": msg.id, "conta": conta, "remetente": msg.de, "nome": msg.nome,
        "titulo": data.titulo or titulo(msg.assunto), "data": data.data.isoformat(), "hora": data.hora,
        "descricao": descricao, "origem": data.origem, "confianca": data.confianca, "link": msg.link,
        "recebido": msg.recebido.isoformat(timespec="seconds"),
        "criado_em": datetime.now().isoformat(timespec="seconds"), "evento_agenda": None,
    }


def processar(msg: Mensagem, conta: str, aceitar: float, revisar: float,
              hoje: date | None = None, prefixo: str = "") -> tuple[list[dict], list[dict]]:
    """(eventos, para revisar) de uma mensagem. Data antes de `hoje` não interessa à agenda."""
    datas = achar_datas(msg.assunto, msg.texto, msg.recebido)
    if msg.em_massa:
        for data in datas:
            data.confianca = round(max(data.confianca - PENALIDADE_EM_MASSA, 0), 2)
    for convite in msg.convites:  # convite vale mesmo em massa: a data vem pronta
        try:
            datas += datas_do_ics(convite)
        except ValueError:
            pass  # convite quebrado: ficam as datas do texto
    hoje = hoje or date.today()
    aceitos, duvidosos = [], []
    for n, data in enumerate(datas, 1):
        if data.data < hoje:
            continue
        if data.confianca >= aceitar:
            aceitos.append(evento(msg, data, n, conta, prefixo))
        elif data.confianca >= revisar:
            duvidosos.append(evento(msg, data, n, conta, prefixo))
    return aceitos, duvidosos


# --- Arquivos -------------------------------------------------------------------------------------

def ler_json(arquivo: Path, padrao: dict) -> dict:
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.is_file() else padrao


def salvar_json(arquivo: Path, dados: dict) -> None:
    """Grava num arquivo temporário e troca: uma coleta que cai no meio não deixa o JSON pela metade."""
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(arquivo.suffix + ".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(arquivo)


def arquivo_de_estado(cfg: dict, conta: dict) -> Path:
    """O estado da primeira conta é o `coleta.estado`; o das outras, `coleta-<nome>.json` ao lado."""
    base = config.caminho(cfg["coleta"]["estado"])
    primeira = cfg["coleta"]["contas"][0]["nome"]
    return base if conta["nome"] == primeira else base.with_name(f"{base.stem}-{conta['nome']}{base.suffix}")


class FonteGmail:
    """Os e-mails pela API do Gmail: a busca roda lá, e só os ids que o Tony não viu são baixados."""

    def __init__(self, servico):
        self.servico = servico

    def mensagens(self, depois_de: datetime, filtro: str, vistos: set):
        for id_ in buscar(self.servico, f"after:{int(depois_de.timestamp())} {filtro}".strip()):
            if id_ not in vistos:
                yield ler_mensagem(self.servico, executar(self.servico.users().messages().get(
                    userId="me", id=id_, format="full")))

    def prazos(self) -> list[dict]:
        return []


def coletar(cfg: dict, fonte, agora: datetime | None = None, conta: dict | None = None) -> dict:
    """Uma rodada da coleta numa conta (sem conta: a primeira). `fonte` é uma `FonteGmail` (ou o serviço
    do Gmail direto) ou a `FonteAppsScript` da Faccat. Devolve o que aconteceu:
    {"emails", "eventos", "revisar", "bloqueados"}."""
    if not hasattr(fonte, "prazos"):  # o serviço do Gmail direto
        fonte = FonteGmail(fonte)
    c = cfg["coleta"]
    conta = conta or c["contas"][0]
    primeira = conta["nome"] == c["contas"][0]["nome"]
    prefixo = "" if primeira else f"{conta['nome']}."  # ids do Gmail são por conta: o prefixo evita colisão
    agora = agora or datetime.now().astimezone()
    arquivo_eventos, arquivo_estado = config.caminho(c["eventos"]), arquivo_de_estado(cfg, conta)
    banco = ler_json(arquivo_eventos, {"eventos": {}, "revisar": {}})
    estado = ler_json(arquivo_estado, {"ultima": None, "vistos": []})
    bloqueados = ler_bloqueados(config.caminho(c["bloqueados"]))

    # Uma hora de folga para trás: o `after:` do Gmail arredonda, e e-mail repetido é barrado pelos `vistos`.
    depois_de = (datetime.fromisoformat(estado["ultima"]) - timedelta(hours=1) if estado["ultima"]
                 else agora - timedelta(days=c["primeira_vez_dias"]))
    filtro = consulta(c["filtro"], bloqueados, depois_de).split(" ", 1)[1] if (c["filtro"] or any(bloqueados.values())) else ""
    vistos = set(estado["vistos"])
    fora = set(banco.get("descartados", [])) | set(banco.get("removidos", []))  # você tirou: não volta
    resumo = {"emails": 0, "eventos": 0, "revisar": 0, "bloqueados": 0}
    if hasattr(fonte, "preparar"):  # a Faccat traz prazos e e-mails numa chamada só
        fonte.preparar(depois_de, filtro)
    for prazo in fonte.prazos():  # prazos do Classroom: a data vem pronta, confiança 1
        evento_do_prazo = {**prazo, "id": f"{prefixo}{prazo['id']}", "conta": conta["nome"],
                           "criado_em": agora.isoformat(timespec="seconds"), "evento_agenda": None}
        if (evento_do_prazo["id"] not in banco["eventos"] and evento_do_prazo["id"] not in fora
                and evento_do_prazo["data"] >= agora.date().isoformat()):
            banco["eventos"][evento_do_prazo["id"]] = evento_do_prazo
            resumo["eventos"] += 1
    for msg in fonte.mensagens(depois_de, filtro, vistos):
        if msg.id in vistos:
            continue
        if not primeira:
            msg.email_da_conta = conta.get("email", "")
        estado["vistos"].append(msg.id)
        vistos.add(msg.id)
        if bloqueado(msg.de, bloqueados):
            resumo["bloqueados"] += 1
            continue
        resumo["emails"] += 1
        aceitos, duvidosos = processar(msg, conta["nome"], c["aceitar_a_partir_de"], c["revisar_a_partir_de"],
                                       agora.date(), prefixo)
        aceitos = [e for e in aceitos if e["id"] not in fora]
        duvidosos = [e for e in duvidosos if e["id"] not in fora]
        for e in aceitos:
            banco["eventos"].setdefault(e["id"], e)
        for e in duvidosos:
            banco["revisar"].setdefault(e["id"], e)
        resumo["eventos"] += len(aceitos)
        resumo["revisar"] += len(duvidosos)
        if len(estado["vistos"]) % SALVAR_A_CADA == 0:
            salvar_json(arquivo_eventos, banco)
            salvar_json(arquivo_estado, estado)  # sem mexer na `ultima`: ela só avança quando a rodada termina

    estado["ultima"] = agora.isoformat(timespec="seconds")
    estado["vistos"] = estado["vistos"][-VISTOS_GUARDADOS:]
    salvar_json(arquivo_eventos, banco)
    salvar_json(arquivo_estado, estado)
    return resumo


def proximos(cfg: dict, dias: int = 30, hoje: datetime | None = None) -> list[dict]:
    """Os eventos de hoje até `dias` à frente, em ordem de data e hora."""
    banco = ler_json(config.caminho(cfg["coleta"]["eventos"]), {"eventos": {}})
    inicio = (hoje or datetime.now()).date()
    fim = inicio + timedelta(days=dias)
    return sorted((e for e in banco["eventos"].values() if inicio.isoformat() <= e["data"] <= fim.isoformat()),
                  key=lambda e: (e["data"], e["hora"] or ""))
