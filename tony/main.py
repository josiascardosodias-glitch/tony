"""Tony no terminal: `tony` conversa; `tony testar` roda as falas de teste."""

import argparse
import readline  # noqa: F401 — só importar já dá setas e histórico ao input()
import time

from . import config
from .cliente import Cliente, ErroDoModelo
from .conversa import TEMPERATURA_MEMORIA, Conversa, consolidar_memoria
from .memoria import (carregar_personalidade, data_do_resumo, lembrar, ler_inteligencia, ler_memoria, resumos_pendentes,
                      salvar_memoria, salvar_resumo, ultimo_resumo, versao_personalidade)
from .registro import Registro

AJUDA = """Comandos:
  /bom              marca a última resposta como boa
  /ruim <motivo>    marca a última resposta como ruim (o motivo é o que mais ajuda a corrigir)
  /lembrar <fato>   guarda um fato na nota de lembretes da Inteligência (pede confirmação)
  /nova             encerra esta conversa (com resumo) e começa outra
  /prompt           mostra o prompt de sistema que o Tony está usando agora
  /sair             encerra (Ctrl+D também)"""


class Sessao:
    """Liga as peças: config, cliente, memória, conversa e registro."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.cliente = Cliente(cfg)
        self.pasta_resumos = config.caminho(cfg["memoria"]["resumos"])
        self.arquivo_memoria = config.caminho(cfg["memoria"]["memoria"])
        self.pasta_inteligencia = config.caminho(cfg["memoria"]["inteligencia"])
        self.organizador = Cliente(cfg, temperatura=TEMPERATURA_MEMORIA)
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
            inteligencia=ler_inteligencia(self.pasta_inteligencia),
            ultima_conversa=ultimo_resumo(self.pasta_resumos),
            memoria=ler_memoria(self.arquivo_memoria)[0],
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
        self.atualizar_memoria()

    def atualizar_memoria(self) -> None:
        """O resumo que deixou de ser o último entra na memória das conversas antigas."""
        memoria, ate = ler_memoria(self.arquivo_memoria)
        for resumo in resumos_pendentes(self.pasta_resumos, ate):
            try:
                memoria = consolidar_memoria(self.organizador, memoria, resumo.read_text(encoding="utf-8"),
                                             data_do_resumo(resumo))
            except ErroDoModelo as e:
                print(f"[aviso] não consegui atualizar a memória ({e}); tento de novo na próxima conversa.")
                return
            salvar_memoria(self.arquivo_memoria, memoria, resumo.stem)
            self.registro.anotar("memoria", resumo=resumo.stem, texto=memoria)

    def lembrar(self, fato: str) -> None:
        if not fato:
            print("uso: /lembrar <fato>  (ex.: /lembrar minha prova de cálculo é dia 12/11)")
            return
        if not self.pasta_inteligencia or not self.pasta_inteligencia.is_dir():
            print("não há pasta de Inteligência configurada (memoria.inteligencia no config.local.yaml).")
            return
        arquivo = self.pasta_inteligencia / self.cfg["memoria"]["lembretes"]
        print(f"vou guardar em {arquivo.name} (essa pasta vai para o modelo na nuvem):\n  - {fato}")
        try:
            confirma = input("confirma? [s/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirma = ""
            print()
        if confirma != "s":
            print("não guardei.")
            return
        lembrar(arquivo, fato)
        self.conversa.lembrados.append(fato)
        self.registro.anotar("lembrete", fato=fato)
        print("guardado.")

    def comando(self, texto: str) -> bool:
        """Executa um comando /. Devolve False quando é hora de sair."""
        nome, _, resto = texto.partition(" ")
        if nome == "/sair":
            return False
        if nome in ("/bom", "/ruim"):
            marcou = self.registro.marcar(nome[1:], resto.strip())
            print("marcado." if marcou else "ainda não há resposta para marcar.")
        elif nome == "/lembrar":
            self.lembrar(resto.strip())
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
    sessao.encerrar_conversa()


def main() -> None:
    parser = argparse.ArgumentParser(prog="tony", description="Tony: agente de IA pessoal. Sem comando, abre a conversa.")
    comandos = parser.add_subparsers(dest="comando")
    testar = comandos.add_parser("testar", help="roda as falas de teste e mostra o placar")
    testar.add_argument("ids", nargs="*", help="só estas falas (padrão: todas)")
    testar.add_argument("--vezes", type=int, help="quantas vezes cada fala roda")
    revisar = comandos.add_parser("revisar", help="propõe uma mudança na personalidade a partir das marcações /ruim")
    revisar.add_argument("--logs", type=config.caminho, help="pasta de logs (padrão: a do config)")
    args = parser.parse_args()

    cfg = config.carregar()
    if args.comando in ("testar", "revisar"):
        from .revisao import revisar
        from .testes import rodar

        try:
            if args.comando == "testar":
                rodar(cfg, args.ids, args.vezes)
            else:
                revisar(cfg, args.logs)
        except ErroDoModelo as e:
            raise SystemExit(f"\n[erro] {e}")
    else:
        conversar(cfg)


if __name__ == "__main__":
    main()
