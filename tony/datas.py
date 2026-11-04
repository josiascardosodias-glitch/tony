"""Acha datas em e-mails, sem IA: expressões regulares para o jeito brasileiro de escrever datas e uma
pontuação que separa compromisso de data qualquer.

Cada data achada vem com a frase onde apareceu e uma `confianca` de 0 a 1:
- convite `.ics`: 1.0 (a data vem pronta);
- no texto: 0.3 de base, +0.4 se a frase tem palavra de compromisso (prova, entrega, prazo, até…),
  +0.2 se tem hora, +0.2 se a data está no assunto, e -0.5 se a frase é de aviso que não é compromisso
  (termos de serviço, mudança na conta, entrega e devolução de compra, desconto, newsletter): ela cai
  abaixo de 0.3 e nem vira pergunta.
Data no passado, mais de um ano à frente, em citação de resposta ("Em ... escreveu:") ou em rodapé
não conta, nem o dia do próprio e-mail sem uma hora depois da chegada ("novo login hoje às 13:54"). O `dateparser` foi testado antes e errou "12/11, às 19h" e "20 de novembro" (DECISOES.md).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

MESES = {"janeiro": 1, "jan": 1, "fevereiro": 2, "fev": 2, "março": 3, "marco": 3, "mar": 3, "abril": 4,
         "abr": 4, "maio": 5, "mai": 5, "junho": 6, "jun": 6, "julho": 7, "jul": 7, "agosto": 8, "ago": 8,
         "setembro": 9, "set": 9, "outubro": 10, "out": 10, "novembro": 11, "nov": 11, "dezembro": 12, "dez": 12}
SEMANA = {"segunda": 0, "terça": 1, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sábado": 5, "sabado": 5,
          "domingo": 6}
COMPROMISSO = re.compile(
    r"\b(prova|avalia[çc][ãa]o|exame|entrega|entregar|prazo|vencimento|vence|vencer|reuni[ãa]o|encontro|"
    r"consulta|apresenta[çc][ãa]o|semin[áa]rio|aula|palestra|evento|inscri[çc][ãa]o|inscri[çc][õo]es|"
    r"matr[íi]cula|pagamento|boleto|fatura|até|data limite|agendad[oa]|marcad[oa]|remarcad[oa]|adiad[oa]|"
    r"in[íi]cio|come[çc]a|termina|encerra|deadline|defesa|entrevista|agendamento|hor[áa]rio|compromisso|"
    r"lembrete|confirmad[oa]|confirma[çc][ãa]o)\b", re.I)
# Avisos com data que não são compromisso, tirados dos que foram aceitos e depois removidos (DECISOES.md).
NAO_COMPROMISSO = re.compile(
    r"termos de (servi[çc]o|uso)|pol[íi]tica de (privacidade|uso)|vamos (fazer )?mudan[çc]as|"
    r"altera[çc](ão|ões) (ser[áa]|ser[ãa]o) aplicad|atualizar (alguns |os |seus )?limites|"
    r"\bchegar[áa]\b|\bentrega prevista|previs[ãa]o de entrega|a caminho|foi (enviad|despachad)[oa]|"
    r"\b(devolver|trocar|devolu[çc][ãa]o|reembolso)\b|"
    r"\b(desconto|cupom|promo[çc][ãa]o|oferta|cashback|frete gr[áa]tis)\b|"
    r"\bagenda da semana\b|\ba semana de \d|\bnewsletter\b", re.I)
PENALIDADE_NAO_COMPROMISSO = 0.5
RODAPE = re.compile(r"escreveu:|wrote:|enviado (em|do)|cancelar (a )?inscri|descadastr|unsubscribe|"
                    r"pol[íi]tica de privacidade|todos os direitos|©", re.I)
CITACAO = re.compile(r"^(Em .{5,120}escreveu:|On .{5,120}wrote:|-{2,} ?Mensagem original|-{2,} ?Original Message|"
                     r"De: .+\n(Enviado|Enviada|Data|Sent):)", re.M | re.I)

_MES = "|".join(sorted(MESES, key=len, reverse=True))
_DIA_DA_SEMANA = "|".join(SEMANA)
NUMERICA = re.compile(r"(?<![\d/.:])(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?(?![\d/])")
EXTENSO = re.compile(rf"\b(\d{{1,2}})º?\s+de\s+({_MES})\.?(?:\s+de\s+(\d{{4}}))?\b", re.I)
RELATIVA = re.compile(r"\b(depois de amanhã|amanhã|hoje)\b", re.I)
SEMANAL = re.compile(rf"(?:\b(na|no|nesta|neste|esta|este|até|até a|para|pra)\s+)?(?:\b(pr[óo]xim[oa])\s+)?"
                     rf"\b({_DIA_DA_SEMANA})(-feira)?(?:\s+(que vem))?\b", re.I)
HORA = re.compile(r"(?<![\d/])([01]?\d|2[0-3])(?:h([0-5]\d)?|:([0-5]\d))(?:\s*h(?:oras|rs)?)?(?![\d/])"
                  r"|(?<![\d/])([01]?\d|2[0-3])\s*horas\b", re.I)

FRASE = re.compile(r"(?<=[.!?])\s+|\n+")
# "2 de dez. às 14h" é uma frase só: o ponto da abreviação sai antes de cortar as frases
ABREVIACAO = re.compile(r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|seg|ter|qua|qui|sex|s[áa]b|dom)\.", re.I)
LIMITE_FUTURO = timedelta(days=400)
ANO_SEGUINTE_ATE = timedelta(days=183)  # sem ano, só vira o ano que vem se cair em até 6 meses


@dataclass
class Data:
    data: date
    hora: str | None   # "HH:MM", ou None se a frase não tem hora
    frase: str
    origem: str        # "assunto", "corpo" ou "ics"
    confianca: float
    titulo: str = ""   # só nos convites .ics, que trazem o próprio título


def limpar_corpo(texto: str) -> str:
    """Tira o que não é deste e-mail: a mensagem citada numa resposta, linhas com > e a assinatura."""
    citacao = CITACAO.search(texto)
    if citacao:
        texto = texto[:citacao.start()]
    texto = texto.split("\n-- \n")[0]
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith(">"))


def _ano(dia: int, mes: int, ano: str | None, base: date) -> date | None:
    """A data com o ano escrito ou, sem ano, a próxima vez que esse dia/mês acontece a partir da base."""
    try:
        if ano:
            return date(int(ano) + (2000 if len(ano) == 2 else 0), mes, dia)
        candidata = date(base.year, mes, dia)
        if candidata >= base - timedelta(days=1):
            return candidata
        seguinte = date(base.year + 1, mes, dia)
        # "29/09" escrito em novembro é uma data que passou, não setembro do ano que vem
        return seguinte if seguinte - base <= ANO_SEGUINTE_ATE else None
    except ValueError:  # 31/02, 45/13...
        return None


def _semana(dia_da_semana: int, proxima: bool, base: date) -> date:
    """"sexta" é a próxima sexta (hoje, se hoje é sexta); "próxima sexta"/"sexta que vem" pula hoje."""
    falta = (dia_da_semana - base.weekday()) % 7
    return base + timedelta(days=falta or (7 if proxima else 0))


def _hora(frase: str) -> str | None:
    m = HORA.search(frase)
    if not m:
        return None
    hora = m.group(1) or m.group(4)
    minutos = m.group(2) or m.group(3) or "00"
    return f"{int(hora):02d}:{minutos}"


def _datas_da_frase(frase: str, base: date) -> list[date]:
    datas = []
    sem_hora = HORA.sub(" ", frase)  # "19:30" não é dia 19 do mês 30, e "12/11, às 19h" não vira dia 19
    for m in NUMERICA.finditer(sem_hora):
        dia, mes = int(m.group(1)), int(m.group(2))
        if not m.group(3) and len(m.group(1)) == len(m.group(2)) == 1:
            continue  # "3/4" sem ano é fração mais vezes que data; "3/04" e "12/11" contam
        if 1 <= dia <= 31 and 1 <= mes <= 12:
            datas.append(_ano(dia, mes, m.group(3), base))
    for m in EXTENSO.finditer(frase):
        datas.append(_ano(int(m.group(1)), MESES[m.group(2).lower()], m.group(3), base))
    for m in RELATIVA.finditer(frase):
        if m.group(1).lower() == "hoje" and not HORA.search(frase):
            continue  # "hoje segue o material" não é compromisso; "hoje às 14h" é
        datas.append(base + timedelta(days={"hoje": 0, "amanhã": 1}.get(m.group(1).lower(), 2)))
    for m in SEMANAL.finditer(frase):
        antes, proxima, nome, feira, que_vem = m.groups()
        # "segunda chamada" e "quarta parte" não são dias: sem uma marca, só sábado e domingo contam
        if feira or proxima or que_vem or antes or SEMANA[nome.lower()] >= 5:
            datas.append(_semana(SEMANA[nome.lower()], bool(proxima or que_vem), base))
    return [d for d in datas if d]


def achar_datas(assunto: str, corpo: str, recebido: datetime) -> list[Data]:
    """Todas as datas de compromisso do assunto e do corpo, uma por data (fica a de maior confiança)."""
    base = recebido.date()
    achadas: dict[date, Data] = {}
    frases = [(assunto, "assunto")] + [(f, "corpo") for f in FRASE.split(ABREVIACAO.sub(r"\1", limpar_corpo(corpo)))]
    for frase, origem in frases:
        frase = re.sub(r"\s+", " ", frase).strip()
        if not frase or RODAPE.search(frase):
            continue
        for dia in _datas_da_frase(frase, base):
            if dia < base or dia - base > LIMITE_FUTURO:
                continue
            hora = _hora(frase)
            if dia == base and (not hora or hora <= f"{recebido:%H:%M}"):
                continue  # o próprio aviso ("novo login em 03/11 13:54"), não um compromisso depois dele
            confianca = (0.3 + 0.4 * bool(COMPROMISSO.search(frase)) + 0.2 * bool(hora)
                         + 0.2 * (origem == "assunto"))
            confianca = min(confianca, 1.0) - PENALIDADE_NAO_COMPROMISSO * bool(NAO_COMPROMISSO.search(frase))
            nova = Data(dia, hora, frase[:300], origem, round(max(confianca, 0.0), 2))
            atual = achadas.get(dia)
            if not atual or nova.confianca > atual.confianca:
                if atual and not nova.hora:
                    nova.hora = atual.hora
                achadas[dia] = nova
    return sorted(achadas.values(), key=lambda d: (d.data, d.hora or ""))


def datas_do_ics(texto: str) -> list[Data]:
    """Os eventos de um convite .ics (o que o Gmail anexa quando alguém manda um convite de agenda)."""
    from icalendar import Calendar

    datas = []
    for evento in Calendar.from_ical(texto).walk("VEVENT"):
        inicio = evento.get("DTSTART")
        if not inicio:
            continue
        valor = inicio.dt
        hora = f"{valor:%H:%M}" if isinstance(valor, datetime) else None
        dia = valor.date() if isinstance(valor, datetime) else valor
        titulo = str(evento.get("SUMMARY", "")).strip()
        descricao = str(evento.get("DESCRIPTION", "")).strip()
        datas.append(Data(dia, hora, (descricao or titulo)[:300], "ics", 1.0, titulo))
    return datas
