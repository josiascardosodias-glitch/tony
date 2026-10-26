"""Testes de código da recuperação: a conversa que acabou sem resumo é achada pelo log.

    uv run python -m unittest discover testes
"""

import json
import tempfile
import unittest
from pathlib import Path

from tony.registro import anotar, conversa_sem_resumo


def log(pasta: Path, nome: str, *eventos: dict) -> Path:
    arquivo = pasta / f"{nome}.jsonl"
    arquivo.write_text("".join(json.dumps({"hora": "2026-10-26T09:40:00", **e}) + "\n" for e in eventos))
    return arquivo


INICIO = {"tipo": "inicio"}
TURNO_1 = {"tipo": "turno", "turno": 1, "usuario": "oi", "tony": "Oi!"}
TURNO_2 = {"tipo": "turno", "turno": 2, "usuario": "tudo bem?", "tony": "Tudo."}
RESUMO = {"tipo": "resumo", "texto": "..."}


class TestConversaSemResumo(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)

    def test_terminal_fechado_no_meio(self):
        arquivo = log(self.pasta, "2026-10-26_092929", INICIO, TURNO_1, TURNO_2)
        self.assertEqual(conversa_sem_resumo(self.pasta), (arquivo, [TURNO_1 | {"hora": "2026-10-26T09:40:00"},
                                                                     TURNO_2 | {"hora": "2026-10-26T09:40:00"}]))

    def test_conversa_encerrada_direito_nao_volta(self):
        log(self.pasta, "2026-10-26_092929", INICIO, TURNO_1, RESUMO)
        self.assertIsNone(conversa_sem_resumo(self.pasta))

    def test_depois_do_nova_so_o_que_ficou_sem_resumo(self):
        log(self.pasta, "2026-10-26_092929", INICIO, TURNO_1, RESUMO, {"tipo": "nova_conversa"}, TURNO_2)
        _, turnos = conversa_sem_resumo(self.pasta)
        self.assertEqual([t["usuario"] for t in turnos], ["tudo bem?"])

    def test_pula_sessao_vazia_e_o_resumo_do_dia(self):
        perdida = log(self.pasta, "2026-10-26_092929", INICIO, TURNO_1)
        log(self.pasta, "2026-10-26_100000", {"tipo": "inicio", "origem": "dia"}, {"tipo": "dia", "texto": "nada hoje"})
        log(self.pasta, "2026-10-26_110000", INICIO)
        self.assertEqual(conversa_sem_resumo(self.pasta)[0], perdida)

    def test_recuperada_uma_vez_so(self):
        arquivo = log(self.pasta, "2026-10-26_092929", INICIO, TURNO_1)
        anotar(arquivo, "resumo", texto="...", recuperado=True)
        self.assertIsNone(conversa_sem_resumo(self.pasta))

    def test_sem_pasta_de_logs(self):
        self.assertIsNone(conversa_sem_resumo(self.pasta / "nao-existe"))


if __name__ == "__main__":
    unittest.main()
