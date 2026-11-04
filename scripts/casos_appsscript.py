"""Gera `appsscript/testes/casos.json`: entradas e as respostas do Python, para o teste diferencial do
Tony no Apps Script (o JavaScript tem que responder igual).

    uv run python scripts/casos_appsscript.py
"""

import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from tony.coleta import juntar_repetidos
from tony.consulta import eh_de_agenda, linha, para_o_modelo, periodo, responder
from tony.datas import achar_datas, limpar_corpo

BRT = timezone(timedelta(hours=-3))
SAIDA = Path(__file__).resolve().parent.parent / "appsscript" / "testes" / "casos.json"

FRASES = [
    "A prova de Cálculo foi remarcada para 12/11, às 19h, na sala 204.", "Entrega do relatório: 05/01/2027.",
    "Prazo final 10/12/26.", "A entrega parcial do TCC é dia 20 de novembro, até 23h59, pelo portal.",
    "Reunião em 2 de dez. às 14:30.", "Matrícula até 15/02.", "Seu boleto vence amanhã.",
    "A palestra é depois de amanhã às 18h.", "A reunião fica para sexta que vem às 14h.",
    "A apresentação é na próxima terça.", "A aula de quinta-feira foi cancelada.",
    "Lembrete: a consulta é hoje às 16h.", "A prova 1 é dia 12/11. A prova 2 é dia 26/11.",
    "Quem faltou pode fazer a segunda chamada.", "Hoje segue em anexo o material da aula.",
    "Faltam 3/4 do conteúdo. Ligue 51 3333-4444.", "O plantão é das 19:30 às 21:00.",
    "A prova foi aplicada em 20/10/2026.", "Vaga publicada em 29/09. Prazo de inscrição: 15/02.",
    "Código 31/02 e 45/13.",
    "Combinado, obrigado.\n\nEm seg., 2 de nov. de 2026 às 18:03, Fulano <f@x.com> escreveu:\n> A prova é dia 12/11.",
    "Novo login na sua conta em 03/11/2026 às 09:12.", "Você compartilhou dados com o app em 3 de nov.",
    "A reunião é hoje às 16h.", "Para cancelar a inscrição até 30/11, clique aqui.", "A prova é dia 12/11 às 19h.",
    "Olha a foto de 12/11.", "Foto de 12/11. A prova é dia 12/11 às 19h.", "Oi\n> antigo\nTchau\n-- \nFulano\n",
    "Data: 05/11/2026 às 08:30", "O evento será dia 05/11/2026 às 08:30.", "Chegará entre 2 e 5 de Novembro.",
    "Em 5 de novembro de 2026, vamos fazer mudanças nos Termos de Serviço.", "AMANHÃ ÀS 10H TEM PROVA!",
    "Até amanhã às 23h59! Últimas vagas.", "Sábado tem evento. Domingo também.", "Na segunda-feira, 10h, reunião.",
    "Consulta marcada para 29/02/2028 às 7h.", "Entrega 29/02 sem ano.", "Prova dia 31/12 e recuperação 05/01.",
    "De: Fulano\nEnviado: segunda\nA prova é 12/11.", "Reunião às 9 horas do dia 14/11.", "Encontro 14/11 9hrs.",
    "© 2026 Todos os direitos reservados. 12/12/2026.", "Evento: 7 de dezembro, das 14h às 16h.",
    "Palestra no 1º de dezembro às 19h30.", "Aula pra quarta que vem.", "Inscrições até esta sexta!",
    "Prova dia 12/11 às 19h.", "Show 🎉 dia 20/11 às 21h — ingressos.", "",
]
PEDACOS = ["prova", "reunião", "entrega", "boleto", "foto", "promoção", "evento", "aula", "consulta", "olá",
           "12/11", "5/1", "05/01", "31/04", "20 de novembro", "1º de jan", "2 de dez.", "15 de março de 2027",
           "hoje", "amanhã", "depois de amanhã", "sexta", "próxima segunda", "quinta-feira", "sábado", "domingo que vem",
           "às 19h", "19:30", "8h15", "10 horas", "23h59", "às 7", "até", "na", "dia", ".", ",", "!", "\n", "segunda chamada"]


def frases_geradas(n: int) -> list[str]:
    sorteio = random.Random(42)
    return [" ".join(sorteio.choice(PEDACOS) for _ in range(sorteio.randint(2, 9))) for _ in range(n)]


BASES = [datetime(2026, 11, 3, 10, 0), datetime(2026, 11, 4, 23, 30), datetime(2026, 12, 28, 8, 0),
         datetime(2027, 2, 27, 12, 0), datetime(2026, 11, 8, 0, 5), datetime(2028, 2, 28, 18, 0)]

PERGUNTAS = ["e amanhã?", "e a semana que vem?", "e no dia 2?", "e o mês que vem?", "e quinta?", "e sexta?",
             "me explica o que é uma closure", "o que eu tenho hoje?", "o que tem essa semana", "o que tem esse mês?",
             "o que tenho amanhã?", "quem te criou?", "tem algo dia 12/11?", "tenho algo na quinta",
             "tenho algo no fim de semana?", "tenho alguma prova?", "20 de novembro", "e no dia 31?", "dia 30",
             "o que tem na próxima semana", "Próximos dias", "e pra segunda?", "e terça e quarta?", "estou livre?",
             "o que tem no final de semana", "próximo mês", "dia 5 de dezembro", "e depois de amanhã", "Tony",
             "tem reunião sexta que vem?", "agenda", "o que tem dia 29"]
HOJES = [date(2026, 11, 3), date(2026, 11, 30), date(2026, 12, 31), date(2027, 1, 31), date(2026, 11, 8),
         date(2028, 2, 29)]


def eventos(hoje: date) -> list[dict]:
    titulos = ["Prova de Cálculo", "Oktober Summit 🎉", "Entrega do TCC", "Consulta", "Reunião"]
    sorteio = random.Random(hoje.toordinal())
    lista = []
    for n in range(12):
        dia = hoje + timedelta(days=sorteio.randint(-3, 40))
        lista.append({"id": f"e{n}", "titulo": sorteio.choice(titulos), "data": dia.isoformat(),
                      "hora": sorteio.choice([None, "08:30", "19:00", "23:59"]),
                      "descricao": sorteio.choice(["a frase do e-mail.\n\nDe: x", "Data: 05/11 " * 30, "linha única"])})
    return lista


def bancos(n: int) -> list[dict]:
    sorteio = random.Random(7)
    casos = []
    for _ in range(n):
        def ev(i, secao):
            return {"id": f"{secao}{i}", "remetente": sorteio.choice(["a@x.com", "b@y.com", "classroom"]),
                    "titulo": sorteio.choice(["T1", "T2"]), "data": sorteio.choice(["2026-11-05", "2026-11-06"]),
                    "hora": sorteio.choice([None, "08:30"]), "recebido": sorteio.choice(["", "2026-11-01", "2026-11-02"]),
                    "evento_agenda": sorteio.choice([None, None, "g1", "g2", f"g{i}{secao}"])}
        banco = {"eventos": {}, "revisar": {}}
        for i in range(sorteio.randint(0, 6)):
            e = ev(i, "m")
            banco["eventos"][e["id"]] = e
        for i in range(sorteio.randint(0, 4)):
            e = ev(i, "r")
            banco["revisar"][e["id"]] = e
        casos.append(banco)
    return casos


def principal() -> None:
    datas = []
    for frase in FRASES + frases_geradas(400):
        for base in BASES:
            recebido = base.replace(tzinfo=BRT)
            for assunto in ("", frase[:40]):
                achadas = achar_datas(assunto, frase, recebido)
                datas.append({"assunto": assunto, "corpo": frase,
                              "recebido": {"data": base.date().isoformat(), "hora": f"{base:%H:%M}"},
                              "esperado": [{"data": d.data.isoformat(), "hora": d.hora, "frase": d.frase,
                                            "origem": d.origem, "confianca": d.confianca} for d in achadas]})
    limpeza = [{"texto": f, "esperado": limpar_corpo(f)} for f in FRASES]
    consultas = []
    for hoje in HOJES:
        lista = eventos(hoje)
        for pergunta in PERGUNTAS + frases_geradas(60):
            p = periodo(pergunta, hoje)
            consultas.append({"texto": pergunta, "hoje": hoje.isoformat(), "eventos": lista,
                              "periodo": [p[0].isoformat(), p[1].isoformat(), p[2]] if p else None,
                              "agenda": eh_de_agenda(pergunta, hoje), "resposta": responder(pergunta, lista, hoje)})
    linhas = [{"evento": e, "hoje": hoje.isoformat(), "linha": linha(e, hoje)} for hoje in HOJES for e in eventos(hoje)]
    modelo = [{"eventos": eventos(hoje), "hoje": hoje.isoformat(), "texto": para_o_modelo(eventos(hoje), hoje)}
              for hoje in HOJES]
    repetidos = []
    for banco in bancos(300):
        entrada = json.loads(json.dumps(banco))
        saiu = juntar_repetidos(banco)
        repetidos.append({"banco": entrada, "saiu": saiu, "depois": banco})
    SAIDA.write_text(json.dumps({"datas": datas, "limpeza": limpeza, "consultas": consultas, "linhas": linhas,
                                 "modelo": modelo, "repetidos": repetidos}, ensure_ascii=False), encoding="utf-8")
    print(f"{SAIDA}: {len(datas)} datas, {len(consultas)} consultas, {len(repetidos)} bancos")


if __name__ == "__main__":
    principal()
