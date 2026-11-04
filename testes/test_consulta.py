"""Testes de código das perguntas de agenda respondidas sem IA.

    uv run python -m unittest discover testes
"""

import unittest
from datetime import date

from tony.consulta import eh_de_agenda, para_o_modelo, periodo, responder

HOJE = date(2026, 11, 3)  # terça


def ev(data: str, titulo: str, hora: str | None = None) -> dict:
    return {"data": data, "hora": hora, "titulo": titulo, "descricao": f"{titulo}: a frase do e-mail.\n\nDe: x"}


EVENTOS = [ev("2026-11-03", "Consulta", "16:00"), ev("2026-11-05", "Oktober Summit", "08:30"),
           ev("2026-11-12", "Prova de Cálculo", "19:00"), ev("2026-12-02", "Entrega do TCC")]


class TestPeriodo(unittest.TestCase):
    def dias(self, texto):
        p = periodo(texto, HOJE)
        return (p[0], p[1]) if p else None

    def test_hoje_e_amanha(self):
        self.assertEqual(self.dias("o que eu tenho hoje?"), (HOJE, HOJE))
        self.assertEqual(self.dias("e amanhã?"), (date(2026, 11, 4), date(2026, 11, 4)))

    def test_dia_da_semana_solto(self):
        self.assertEqual(self.dias("e sexta?"), (date(2026, 11, 6), date(2026, 11, 6)))
        self.assertEqual(self.dias("tenho algo na quinta"), (date(2026, 11, 5), date(2026, 11, 5)))

    def test_semana(self):
        self.assertEqual(self.dias("o que tem essa semana"), (HOJE, date(2026, 11, 8)))
        self.assertEqual(self.dias("e a semana que vem?"), (date(2026, 11, 9), date(2026, 11, 15)))

    def test_mes(self):
        self.assertEqual(self.dias("o que tem esse mês"), (HOJE, date(2026, 11, 30)))
        self.assertEqual(self.dias("e o mês que vem?"), (date(2026, 12, 1), date(2026, 12, 31)))

    def test_data_e_dia(self):
        self.assertEqual(self.dias("tem algo dia 12/11?"), (date(2026, 11, 12), date(2026, 11, 12)))
        self.assertEqual(self.dias("e no dia 2?"), (date(2026, 12, 2), date(2026, 12, 2)))
        self.assertEqual(self.dias("20 de novembro"), (date(2026, 11, 20), date(2026, 11, 20)))

    def test_fim_de_semana(self):
        self.assertEqual(self.dias("tenho algo no fim de semana?"), (date(2026, 11, 7), date(2026, 11, 8)))

    def test_sem_periodo(self):
        self.assertIsNone(periodo("me explica o que é uma closure", HOJE))


class TestResponder(unittest.TestCase):
    def test_um_evento(self):
        r = responder("e quinta?", EVENTOS, HOJE)
        self.assertTrue(r.startswith("Marcado quinta, 05/11:"))
        self.assertIn("Oktober Summit", r)
        self.assertNotIn("Prova", r)

    def test_varios_em_ordem(self):
        r = responder("o que tem esse mês?", EVENTOS, HOJE)
        self.assertTrue(r.startswith("3 coisas marcadas até o fim do mês:"))
        self.assertLess(r.index("Consulta"), r.index("Oktober"))
        self.assertLess(r.index("Oktober"), r.index("Prova"))

    def test_nada(self):
        self.assertEqual(responder("e sexta?", EVENTOS, HOJE), "Nada marcado sexta, 06/11.")

    def test_sem_periodo_olha_a_semana(self):
        r = responder("tenho alguma prova?", EVENTOS, HOJE)
        self.assertIn("nos próximos 7 dias", r)
        self.assertNotIn("Prova de Cálculo", r)  # 12/11 passa dos 7 dias


class TestEhDeAgenda(unittest.TestCase):
    def test_agenda_e_conversa(self):
        self.assertTrue(eh_de_agenda("o que tenho amanhã?", HOJE))
        self.assertTrue(eh_de_agenda("tenho alguma prova marcada?", HOJE))
        self.assertFalse(eh_de_agenda("me explica o que é uma closure", HOJE))
        self.assertFalse(eh_de_agenda("quem te criou?", HOJE))


class TestParaOModelo(unittest.TestCase):
    def test_curto_e_so_do_periodo(self):
        texto = para_o_modelo(EVENTOS + [ev("2026-10-01", "Passou")], HOJE, dias=10)
        self.assertIn("quinta-feira, 05/11/2026 às 08:30: Oktober Summit", texto)
        self.assertNotIn("Passou", texto)
        self.assertNotIn("Entrega do TCC", texto)
        self.assertNotIn("De: x", texto)  # só a primeira linha da descrição
