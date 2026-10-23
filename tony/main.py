"""Tony no terminal: o loop da conversa e os comandos /."""

import readline  # noqa: F401 — só importar já dá setas e histórico ao input()
import time

from . import config
from .cliente import Cliente, ErroDoModelo
from .conversa import Conversa
from .memoria import carregar_personalidade, ler_inteligencia, salvar_resumo, ultimo_resumo, versao_personalidade
from .registro import Registro

AJUDA = """Comandos:
  /bom              marca a última resposta como boa
  /ruim <motivo>    marca a última resposta como ruim (o motivo é o que mais ajuda a corrigir)
  /nova             encerra esta conversa (com resumo) e começa outra
  /prompt           mostra o prompt de sistema que o Tony está usando agora
  /sair             encerra (Ctrl+D também)"""


class Sessao:
    """Liga as peças: config, cliente, memória, conversa e registro."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.cliente = Cliente(cfg)
        self.pasta_resumos = config.caminho(cfg["memoria"]["resumos"])
        pasta_personalidade = config.caminho(cfg["personalidade"])
        self.personalidade = carregar_personalidade(pasta_personalidade)
        self.registro = Registro(
            config.caminho(cfg["logs"]),
            modelo=self.cliente.modelo,
            personalidade=versao_personalidade(pasta_personalidade),
        )
        self.conversa = self._nova_conversa()

    def _nova_conversa(self) -> Conversa:
        return Conversa(
            self.cliente,
            limite=self.cfg["contexto"]["limite"],
            personalidade=self.personalidade,
            inteligencia=ler_inteligencia(config.caminho(self.cfg["memoria"]["inteligencia"])),
            ultima_conversa=ultimo_resumo(self.pasta_resumos),
        )

    def encerrar_conversa(self) -> None:
        if not self.conversa.mensagens:
            return
        print("(guardando um resumo para a próxima conversa...)")
        try:
            resumo = self.conversa.resumir_para_proxima()
        except ErroDoModelo as e:
            print(f"[erro] não consegui resumir: {e}")
            return
        salvar_resumo(self.pasta_resumos, resumo)
        self.registro.anotar("resumo", texto=resumo)

    def comando(self, texto: str) -> bool:
        """Executa um comando /. Devolve False quando é hora de sair."""
        nome, _, resto = texto.partition(" ")
        if nome == "/sair":
            return False
        if nome in ("/bom", "/ruim"):
            marcou = self.registro.marcar(nome[1:], resto.strip())
            print("marcado." if marcou else "ainda não há resposta para marcar.")
        elif nome == "/nova":
            self.encerrar_conversa()
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
        pedacos = []
        try:
            for pedaco in self.conversa.responder(texto):
                print(pedaco, end="", flush=True)
                pedacos.append(pedaco)
        except ErroDoModelo as e:
            print(f"\n[erro] {e}\n")
            self.registro.anotar("erro", mensagem=str(e))
            return
        except KeyboardInterrupt:
            print("\n[interrompido — essa fala foi descartada]\n")
            return
        print("\n")
        self.registro.turno_completo(texto, "".join(pedacos), time.monotonic() - inicio)


def main() -> None:
    sessao = Sessao(config.carregar())
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
    sessao.encerrar_conversa()


if __name__ == "__main__":
    main()
