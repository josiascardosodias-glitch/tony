"""Responde perguntas de agenda sem IA: entende o período ("hoje", "sexta", "semana que vem", "12/11") e
monta a resposta com o que está no `eventos.json`.

O modelo só entra quando a mensagem não é uma pergunta de agenda (`eh_de_agenda` devolve False).
"""

import re
from datetime import date, timedelta

from .conversa import DIAS
from .datas import _datas_da_frase

MESES_NOMES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
               "outubro", "novembro", "dezembro"]
SOBRE_AGENDA = re.compile(r"\b(agenda|compromisso|marcad[oa]s?|tenho|tem algo|tem alguma|o que tem|prova|"
                          r"entrega|evento|reuni[ãa]o|prazo|pr[óo]xim[oa]s dias|livre)\b", re.I)
PADRAO_DIAS = 7  # "o que eu tenho?" sem período: a próxima semana


def periodo(texto: str, hoje: date) -> tuple[date, date, str] | None:
    """(início, fim, nome do período) que a mensagem pede, ou None se ela não fala de um período."""
    t = texto.lower()
    domingo = hoje + timedelta(days=6 - hoje.weekday())
    if re.search(r"fim de semana|final de semana", t):
        sabado = hoje + timedelta(days=(5 - hoje.weekday()) % 7)
        return sabado, sabado + timedelta(days=1), "no fim de semana"
    if re.search(r"semana que vem|pr[óo]xima semana", t):
        segunda = domingo + timedelta(days=1)
        return segunda, segunda + timedelta(days=6), "na semana que vem"
    if re.search(r"\b(ess?a|nesta|nessa|esta) semana\b|\bsemana\b", t):
        return hoje, domingo, "até domingo"
    if re.search(r"m[êe]s que vem|pr[óo]ximo m[êe]s", t):
        inicio = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
        fim = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return inicio, fim, f"em {MESES_NOMES[inicio.month - 1]}"
    if re.search(r"\b(ess?e|neste|nesse|este) m[êe]s\b|\bm[êe]s\b", t):
        fim = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return hoje, fim, "até o fim do mês"
    dia = re.search(r"\bdia (\d{1,2})\b", t)
    if dia and not re.search(r"\bdia \d{1,2}\s*(/|de )", t):
        n = int(dia.group(1))
        try:
            alvo = hoje.replace(day=n)
            if alvo < hoje:
                alvo = (hoje.replace(day=1) + timedelta(days=32)).replace(day=n)
            return alvo, alvo, _nome_do_dia(alvo, hoje)
        except ValueError:
            pass
    # "hoje", "amanhã", "sexta", "12/11", "20 de novembro": o mesmo leitor das datas dos e-mails
    datas = sorted(set(_datas_da_frase(re.sub(r"\b(e|na|no|pra|para) (?=segunda|terça|terca|quarta|quinta|sexta)",
                                              "na ", t), hoje) + _dias_soltos(t, hoje)))
    if datas:
        return datas[0], datas[-1], _nome_do_dia(datas[0], hoje) if datas[0] == datas[-1] else "nesses dias"
    if re.search(r"hoje", t):  # "o que tenho hoje" (sem hora, o leitor de e-mail ignora o "hoje")
        return hoje, hoje, "hoje"
    return None


def _dias_soltos(texto: str, hoje: date) -> list[date]:
    """Na pergunta, "e sexta?" é a sexta: aqui não há "segunda chamada" para confundir."""
    nomes = {"segunda": 0, "terça": 1, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4}
    return [hoje + timedelta(days=(n - hoje.weekday()) % 7)
            for nome, n in nomes.items() if re.search(rf"\b{nome}\b", texto)]


def _nome_do_dia(dia: date, hoje: date) -> str:
    if dia == hoje:
        return "hoje"
    if dia == hoje + timedelta(days=1):
        return "amanhã"
    return f"{DIAS[dia.weekday()].split('-')[0]}, {dia:%d/%m}"


def eh_de_agenda(texto: str, hoje: date) -> bool:
    return bool(periodo(texto, hoje) or SOBRE_AGENDA.search(texto))


def linha(evento: dict, hoje: date) -> str:
    dia = date.fromisoformat(evento["data"])
    quando = _nome_do_dia(dia, hoje) if (dia - hoje).days < 2 else f"{DIAS[dia.weekday()][:3]} {dia:%d/%m}"
    hora = f", {evento['hora']}" if evento["hora"] else ""
    resumo = evento["descricao"].split("\n")[0][:140]
    return f"• {quando}{hora} — {evento['titulo']}\n  {resumo}"


def responder(texto: str, eventos: list[dict], hoje: date) -> str:
    """A resposta para uma pergunta de agenda, só com os eventos do período."""
    achado = periodo(texto, hoje)
    inicio, fim, nome = achado or (hoje, hoje + timedelta(days=PADRAO_DIAS), "nos próximos 7 dias")
    no_periodo = sorted((e for e in eventos if inicio.isoformat() <= e["data"] <= fim.isoformat()),
                        key=lambda e: (e["data"], e["hora"] or ""))
    if not no_periodo:
        return f"Nada marcado {nome}."
    cabeca = f"{'Marcado' if len(no_periodo) == 1 else f'{len(no_periodo)} coisas marcadas'} {nome}:"
    return cabeca + "\n\n" + "\n".join(linha(e, hoje) for e in no_periodo)


def para_o_modelo(eventos: list[dict], hoje: date, dias: int = 30) -> str:
    """A agenda dos próximos dias, curta, para o prompt (título, data, hora e a frase: nunca o e-mail)."""
    fim = (hoje + timedelta(days=dias)).isoformat()
    linhas = [f"- {DIAS[date.fromisoformat(e['data']).weekday()]}, {date.fromisoformat(e['data']):%d/%m/%Y}"
              f"{' às ' + e['hora'] if e['hora'] else ''}: {e['titulo']} ({e['descricao'].splitlines()[0][:120]})"
              for e in sorted(eventos, key=lambda e: (e["data"], e["hora"] or ""))
              if hoje.isoformat() <= e["data"] <= fim]
    return "\n".join(linhas) or "(nada marcado)"
