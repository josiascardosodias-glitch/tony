"""Tony no terminal: `tony` conversa; `tony testar` roda as falas de teste; `tony dia` é o resumo do dia."""

import argparse
import readline  # noqa: F401 — só importar já dá setas e histórico ao input()
import time

from . import config
from . import ferramentas
from .cliente import Chamada, Cliente, ErroDoModelo
from .conversa import Conversa
from .memoria import carregar_personalidade, ler_inteligencia, versao_personalidade
from .registro import Registro

AJUDA = """Comandos:
  /bom              marca a última resposta como boa
  /ruim <motivo>    marca a última resposta como ruim (o motivo é o que mais ajuda a corrigir)
  /nova             começa uma conversa nova
  /prompt           mostra o prompt de sistema que o Tony está usando agora
  /sair             encerra (Ctrl+D também)"""


class Sessao:
    """Liga as peças: config, cliente, conversa e registro."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.cliente = Cliente(cfg)
        self.inteligencia = ler_inteligencia(config.caminho(cfg["memoria"]["inteligencia"]))
        ferramentas.ambiente.confirmar = self._confirmar
        self.ferramentas = ferramentas.descobrir()
        pasta_personalidade = config.caminho(cfg["personalidade"])
        self.personalidade = carregar_personalidade(pasta_personalidade)
        self.registro = Registro(
            config.caminho(cfg["logs"]),
            modelo=self.cliente.modelo,
            personalidade=versao_personalidade(pasta_personalidade),
        )
        self.conversa = self._nova_conversa()

    def _nova_conversa(self) -> Conversa:
        return Conversa(self.cliente, limite=self.cfg["contexto"]["limite"], personalidade=self.personalidade,
                        inteligencia=self.inteligencia, ferramentas=self.ferramentas)

    @staticmethod
    def _confirmar(pergunta: str) -> bool:
        """Pergunta de uma ferramenta que escreve: só um "s" explícito autoriza."""
        print(f"\n{pergunta}")
        try:
            return input("confirma? [s/N] ").strip().lower() == "s"
        except (EOFError, KeyboardInterrupt):
            print()
            return False

    def comando(self, texto: str) -> bool:
        """Executa um comando /. Devolve False quando é hora de sair."""
        nome, _, resto = texto.partition(" ")
        if nome == "/sair":
            return False
        if nome in ("/bom", "/ruim"):
            marcou = self.registro.marcar(nome[1:], resto.strip())
            print("marcado." if marcou else "ainda não há resposta para marcar.")
        elif nome == "/nova":
            self.conversa = self._nova_conversa()
            self.registro.anotar("nova_conversa")
            print("conversa nova.")
        elif nome == "/prompt":
            print(self.conversa.prompt_de_sistema())
            print(f"\n(≈ {self.conversa.tokens_estimados()} tokens na conversa até agora)")
        elif nome == "/ajuda":
            print(AJUDA)
        else:
            print("comando desconhecido. /ajuda mostra os comandos.")
        return True

    def falar(self, texto: str) -> None:
        print("tony > ", end="", flush=True)
        inicio = time.monotonic()
        pedacos, chamadas = [], []
        try:
            for item in self.conversa.responder(texto):
                if isinstance(item, Chamada):  # aparece antes de rodar: a confirmação vem logo depois
                    argumentos = ", ".join(f"{k}={v!r}" for k, v in item.argumentos.items())
                    print(f"\n  · {item.nome}({argumentos})", flush=True)
                    chamadas.append(item)
                    continue
                print(item, end="", flush=True)
                pedacos.append(item)
        except ErroDoModelo as e:
            print(f"\n[erro] {e}\n")
            self.registro.anotar("erro", mensagem=str(e))
            return
        except KeyboardInterrupt:
            print("\n[interrompido — essa fala foi descartada]\n")
            return
        print("\n")
        self.registro.turno_completo(texto, "".join(pedacos), time.monotonic() - inicio,
                                     ferramentas=[{"nome": c.nome, "argumentos": c.argumentos, "resultado": c.resultado[:500]}
                                                  for c in chamadas])


def conversar(cfg: dict) -> None:
    sessao = Sessao(cfg)
    print(f"Tony · {sessao.cliente.modelo} · /ajuda para os comandos\n")
    while True:
        try:
            texto = input("você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not texto:
            continue
        if texto.startswith("/"):
            if not sessao.comando(texto):
                break
        else:
            sessao.falar(texto)


def main() -> None:
    parser = argparse.ArgumentParser(prog="tony", description="Tony: agente de IA pessoal. Sem comando, abre a conversa.")
    comandos = parser.add_subparsers(dest="comando")
    testar = comandos.add_parser("testar", help="roda as falas de teste e mostra o placar")
    testar.add_argument("ids", nargs="*", help="só estas falas (padrão: todas)")
    testar.add_argument("--vezes", type=int, help="quantas vezes cada fala roda")
    dia = comandos.add_parser("dia", help="o Tony fala primeiro: o resumo do dia")
    dia.add_argument("--notificar", action="store_true", help="também mostra como notificação na área de trabalho")
    agendar = comandos.add_parser("agendar", help="instala um timer do systemd que roda `tony dia --notificar` todo dia")
    agendar.add_argument("--hora", default="08:00", help="HH:MM (padrão 08:00)")
    autorizar = comandos.add_parser("autorizar", help="abre o navegador para autorizar o Tony no Gmail e na Agenda")
    autorizar.add_argument("--conta", help="o nome da conta em coleta.contas (padrão: a primeira)")
    comandos.add_parser("coletar", help="busca os e-mails novos e guarda as datas em eventos.json (sem IA)")
    eventos = comandos.add_parser("eventos", help="mostra as datas guardadas (sem IA)")
    eventos.add_argument("--dias", type=int, default=30, help="quantos dias à frente (padrão 30)")
    eventos.add_argument("--revisar", action="store_true", help="mostra as datas de confiança média, para decidir")
    bloquear = comandos.add_parser("bloquear", help="nunca mais lê e-mails de um endereço (x@y.com) ou domínio (@y.com)")
    bloquear.add_argument("alvo")
    faccat = comandos.add_parser("faccat", help="configura a conta da Faccat (App da Web do Apps Script)")
    faccat.add_argument("--url", help="a URL /exec do App da Web, depois de implantar")
    comandos.add_parser("telegram", help="o Tony no Telegram, com a coleta de hora em hora")
    comandos.add_parser("agenda", help="leva os eventos para a agenda \"Tony\" do Google (o coletar já faz isso)")
    aceitar = comandos.add_parser("aceitar", help="uma data de revisar vira evento (e vai para a agenda)")
    aceitar.add_argument("id")
    descartar = comandos.add_parser("descartar", help="uma data de revisar é jogada fora")
    descartar.add_argument("id")
    args = parser.parse_args()

    cfg = config.carregar()
    try:
        if args.comando in ("dia", "agendar"):
            from . import dia

            dia.dia(cfg, args.notificar) if args.comando == "dia" else dia.agendar(args.hora)
        elif args.comando in ("autorizar", "coletar", "eventos", "bloquear", "agenda", "aceitar", "descartar", "faccat"):
            from . import contas

            contas.rodar(cfg, args)
        elif args.comando == "telegram":
            from .telegram import rodar as telegram

            telegram(cfg)
        elif args.comando == "testar":
            from .testes import rodar

            rodar(cfg, args.ids, args.vezes)
        else:
            conversar(cfg)
    except ErroDoModelo as e:
        raise SystemExit(f"\n[erro] {e}")


if __name__ == "__main__":
    main()
