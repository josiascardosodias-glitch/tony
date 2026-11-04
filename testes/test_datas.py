"""Testes de código do extrator de datas: cada formato de data que aparece em e-mail brasileiro.

    uv run python -m unittest discover testes
"""

import unittest
from datetime import date, datetime, timedelta, timezone

from tony.datas import achar_datas, datas_do_ics, limpar_corpo

# 03/11/2026 é uma terça-feira
RECEBIDO = datetime(2026, 11, 3, 10, 0)


def datas(corpo: str, assunto: str = "Aviso", recebido: datetime = RECEBIDO) -> list[tuple]:
    return [(d.data, d.hora) for d in achar_datas(assunto, corpo, recebido)]


class TestFormatos(unittest.TestCase):
    def test_numerica_com_hora(self):
        self.assertEqual(datas("A prova de Cálculo foi remarcada para 12/11, às 19h, na sala 204."),
                         [(date(2026, 11, 12), "19:00")])

    def test_numerica_com_ano(self):
        self.assertEqual(datas("Entrega do relatório: 05/01/2027."), [(date(2027, 1, 5), None)])

    def test_ano_com_dois_digitos(self):
        self.assertEqual(datas("Prazo final 10/12/26."), [(date(2026, 12, 10), None)])

    def test_por_extenso_com_hora_quebrada(self):
        self.assertEqual(datas("A entrega parcial do TCC é dia 20 de novembro, até 23h59, pelo portal."),
                         [(date(2026, 11, 20), "23:59")])

    def test_mes_abreviado(self):
        self.assertEqual(datas("Reunião em 2 de dez. às 14:30."), [(date(2026, 12, 2), "14:30")])

    def test_sem_ano_e_ja_passou_vai_para_o_ano_seguinte(self):
        self.assertEqual(datas("Matrícula até 15/02."), [(date(2027, 2, 15), None)])

    def test_amanha(self):
        self.assertEqual(datas("Seu boleto vence amanhã."), [(date(2026, 11, 4), None)])

    def test_depois_de_amanha(self):
        self.assertEqual(datas("A palestra é depois de amanhã às 18h."), [(date(2026, 11, 5), "18:00")])

    def test_sexta_que_vem_numa_terca(self):
        self.assertEqual(datas("A reunião fica para sexta que vem às 14h."), [(date(2026, 11, 6), "14:00")])

    def test_proxima_terca_numa_terca_pula_hoje(self):
        self.assertEqual(datas("A apresentação é na próxima terça."), [(date(2026, 11, 10), None)])

    def test_dia_da_semana_com_feira(self):
        self.assertEqual(datas("A aula de quinta-feira foi cancelada."), [(date(2026, 11, 5), None)])

    def test_hoje_com_hora(self):
        self.assertEqual(datas("Lembrete: a consulta é hoje às 16h."), [(date(2026, 11, 3), "16:00")])

    def test_duas_datas_na_mesma_mensagem(self):
        self.assertEqual(datas("A prova 1 é dia 12/11. A prova 2 é dia 26/11."),
                         [(date(2026, 11, 12), None), (date(2026, 11, 26), None)])


class TestNaoEhData(unittest.TestCase):
    def test_segunda_chamada_nao_e_segunda_feira(self):
        self.assertEqual(datas("Quem faltou pode fazer a segunda chamada."), [])

    def test_hoje_sem_hora(self):
        self.assertEqual(datas("Hoje segue em anexo o material da aula."), [])

    def test_fracao_e_telefone(self):
        self.assertEqual(datas("Faltam 3/4 do conteúdo. Ligue 51 3333-4444."), [])

    def test_hora_sozinha_nao_vira_dia(self):
        self.assertEqual(datas("O plantão é das 19:30 às 21:00."), [])

    def test_data_no_passado(self):
        self.assertEqual(datas("A prova foi aplicada em 20/10/2026."), [])

    def test_sem_ano_e_longe_demais_e_uma_data_que_passou(self):
        self.assertEqual(datas("Vaga publicada em 29/09. Prazo de inscrição: 15/02."), [(date(2027, 2, 15), None)])

    def test_data_invalida(self):
        self.assertEqual(datas("Código 31/02 e 45/13."), [])

    def test_resposta_citada_nao_conta(self):
        corpo = "Combinado, obrigado.\n\nEm seg., 2 de nov. de 2026 às 18:03, Fulano <f@x.com> escreveu:\n> A prova é dia 12/11."
        self.assertEqual(datas(corpo), [])

    def test_dia_do_proprio_aviso(self):
        self.assertEqual(datas("Novo login na sua conta em 03/11/2026 às 09:12."), [])
        self.assertEqual(datas("Você compartilhou dados com o app em 3 de nov."), [])

    def test_hoje_mais_tarde_conta(self):
        self.assertEqual(datas("A reunião é hoje às 16h."), [(date(2026, 11, 3), "16:00")])

    def test_rodape(self):
        self.assertEqual(datas("Para cancelar a inscrição até 30/11, clique aqui."), [])


class TestConfianca(unittest.TestCase):
    def confianca(self, corpo: str, assunto: str = "Aviso") -> float:
        return achar_datas(assunto, corpo, RECEBIDO)[0].confianca

    def test_compromisso_com_hora_e_alta(self):
        self.assertEqual(self.confianca("A prova é dia 12/11 às 19h."), 0.9)

    def test_data_solta_e_baixa(self):
        self.assertEqual(self.confianca("Olha a foto de 12/11."), 0.3)

    def test_no_assunto_soma(self):
        self.assertEqual(self.confianca("", assunto="Prova remarcada para 12/11"), 0.9)

    def test_mesma_data_fica_a_melhor_frase(self):
        achadas = achar_datas("Aviso", "Foto de 12/11. A prova é dia 12/11 às 19h.", RECEBIDO)
        self.assertEqual(len(achadas), 1)
        self.assertEqual(achadas[0].frase, "A prova é dia 12/11 às 19h.")


class TestLimparCorpo(unittest.TestCase):
    def test_assinatura_e_citacao(self):
        self.assertEqual(limpar_corpo("Oi\n> antigo\nTchau\n-- \nFulano\n"), "Oi\nTchau")


ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20261118T140000
SUMMARY:Entrevista de estágio
DESCRIPTION:Sala 3
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261120
SUMMARY:Feriado da empresa
END:VEVENT
END:VCALENDAR
"""


class TestIcs(unittest.TestCase):
    def test_convite_com_hora_e_dia_inteiro(self):
        eventos = datas_do_ics(ICS)
        self.assertEqual([(e.data, e.hora, e.titulo, e.confianca) for e in eventos], [
            (date(2026, 11, 18), "14:00", "Entrevista de estágio", 1.0),
            (date(2026, 11, 20), None, "Feriado da empresa", 1.0),
        ])
        self.assertEqual(eventos[0].frase, "Sala 3")



class TestNaoCompromisso(unittest.TestCase):
    """Avisos com data que foram aceitos e depois removidos (casos reais, 2026-11-04): caem abaixo de 0.3."""

    RECEBIDO = datetime(2026, 11, 3, 10, 0, tzinfo=timezone(timedelta(hours=-3)))

    def confianca(self, frase: str):
        return max((d.confianca for d in achar_datas("", frase, self.RECEBIDO)), default=None)

    def test_avisos_sao_descartados(self):
        for frase in ["Em 5 de novembro de 2026, vamos fazer mudanças nos Termos de Serviço do",
                      "Essa alteração será aplicada automaticamente a partir de 05/11/2026 .",
                      "Chegará entre 2 e 5 de Novembro.",
                      "A semana de 02 a 06 de novembro será marcada por uma agenda relevante para os mercados.",
                      "Se tiver algum problema, você pode devolver ou trocar grátis sua compra até 14 de novembro.",
                      "O desconto é válido para viagens feitas até 22/11/2026, e se aplica a 1 única viagem."]:
            with self.subTest(frase=frase):
                self.assertLess(self.confianca(frase), 0.3)

    def test_compromissos_continuam(self):
        for frase, esperada in [("A prova de Cálculo foi remarcada para 12/11, às 19h.", 0.9),
                                ("Entrega do trabalho até 20/11 pelo portal.", 0.7),
                                ("A fatura vence dia 10/11.", 0.7), ("Data: 05/11/2026 às 08:30", 0.5)]:
            with self.subTest(frase=frase):
                self.assertEqual(self.confianca(frase), esperada)


if __name__ == "__main__":
    unittest.main()
