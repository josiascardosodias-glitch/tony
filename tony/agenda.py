"""A agenda "Tony" no Google Agenda: cada evento do `eventos.json` vira um evento lá, sem duplicar.

O Tony só tem o acesso `calendar.app.created`: cria e mexe só nas agendas que ele mesmo criou, e não
consegue nem listar as suas. Por isso o id da agenda fica guardado em `agenda.arquivo` depois de criada.

Sem duplicar, em três camadas:
1. o evento já sincronizado guarda o id do Google em `evento_agenda`;
2. no Google, cada evento leva o id do Tony em `extendedProperties.private.tony_id`, e antes de criar o
   Tony procura por ele (para o caso de o `eventos.json` ter se perdido);
3. dois e-mails do mesmo remetente sobre o mesmo dia e hora (confirmação e lembrete) viram um evento só.
"""

from datetime import date, datetime, timedelta

from . import config
from .coleta import executar, ler_json, salvar_json

NOME = "Tony"
DESCRICAO = "Datas encontradas pelo Tony nos seus e-mails. Pode apagar a agenda inteira se quiser recomeçar."
FUSO = "America/Sao_Paulo"
DURACAO = timedelta(hours=1)  # o e-mail diz quando começa, quase nunca quando termina


def id_da_agenda(cfg: dict, servico) -> str:
    """A agenda "Tony": a guardada, ou uma nova (e guardada) na primeira vez."""
    arquivo = config.caminho(cfg["agenda"]["arquivo"])
    guardada = ler_json(arquivo, {}).get("id")
    if guardada:
        return guardada
    nova = executar(servico.calendars().insert(body={"summary": NOME, "description": DESCRICAO, "timeZone": FUSO}))
    salvar_json(arquivo, {"id": nova["id"], "criada_em": datetime.now().isoformat(timespec="seconds")})
    return nova["id"]


def corpo(evento: dict) -> dict:
    """O evento como a API da Agenda espera. Título e data aparecem; a descrição fica no corpo."""
    descricao = f"{evento['descricao']}\n\nDe: {evento['nome'] or evento['remetente']} <{evento['remetente']}>\n" \
                f"E-mail: {evento['link']}"
    if evento["hora"]:
        inicio = datetime.fromisoformat(f"{evento['data']}T{evento['hora']}")
        quando = {"start": {"dateTime": inicio.isoformat(), "timeZone": FUSO},
                  "end": {"dateTime": (inicio + DURACAO).isoformat(), "timeZone": FUSO}}
    else:  # dia inteiro: o fim é o dia seguinte (exclusivo)
        dia = date.fromisoformat(evento["data"])
        quando = {"start": {"date": dia.isoformat()}, "end": {"date": (dia + timedelta(days=1)).isoformat()}}
    return {"summary": evento["titulo"], "description": descricao, **quando,
            "extendedProperties": {"private": {"tony_id": evento["id"]}}}


def _ja_existe(servico, agenda: str, tony_id: str) -> str | None:
    r = executar(servico.events().list(calendarId=agenda, privateExtendedProperty=f"tony_id={tony_id}",
                                       maxResults=1, showDeleted=False))
    itens = r.get("items", [])
    return itens[0]["id"] if itens else None


def chave(evento: dict) -> tuple:
    """O mesmo compromisso, mesmo vindo em dois e-mails."""
    return evento["remetente"], evento["data"], evento["hora"]


def sincronizar(cfg: dict, servico, hoje: date | None = None) -> dict:
    """Leva os eventos de hoje em diante para a agenda. Devolve {"criados", "repetidos", "ja_estavam"}."""
    arquivo = config.caminho(cfg["coleta"]["eventos"])
    banco = ler_json(arquivo, {"eventos": {}, "revisar": {}})
    hoje = (hoje or date.today()).isoformat()
    agenda = id_da_agenda(cfg, servico)
    resumo = {"criados": 0, "repetidos": 0, "ja_estavam": 0}
    no_google = {chave(e): e["evento_agenda"] for e in banco["eventos"].values() if e.get("evento_agenda")}
    for evento in sorted(banco["eventos"].values(), key=lambda e: e["id"]):
        if evento.get("evento_agenda") or evento["data"] < hoje:
            continue
        if chave(evento) in no_google:  # outro e-mail do mesmo compromisso já está lá
            evento["evento_agenda"] = no_google[chave(evento)]
            resumo["repetidos"] += 1
        elif existente := _ja_existe(servico, agenda, evento["id"]):
            evento["evento_agenda"] = existente
            resumo["ja_estavam"] += 1
        else:
            criado = executar(servico.events().insert(calendarId=agenda, body=corpo(evento)))
            evento["evento_agenda"] = criado["id"]
            resumo["criados"] += 1
        no_google[chave(evento)] = evento["evento_agenda"]
        salvar_json(arquivo, banco)  # a cada evento: se cair no meio, não cria de novo o que já criou
    return resumo


def decidir(cfg: dict, id_: str, aceitar: bool) -> str:
    """Tira uma data de "revisar": para os eventos (aceitar) ou para fora (descartar, sem volta na coleta)."""
    arquivo = config.caminho(cfg["coleta"]["eventos"])
    banco = ler_json(arquivo, {"eventos": {}, "revisar": {}})
    banco.setdefault("descartados", [])
    evento = banco["revisar"].pop(id_, None)
    if not evento:
        return f"não há {id_} em revisar (veja os ids com `tony eventos --revisar`)."
    if aceitar:
        banco["eventos"][id_] = evento
    else:
        banco["descartados"].append(id_)
    salvar_json(arquivo, banco)
    return f"{'aceito' if aceitar else 'descartado'}: {evento['titulo']} ({evento['data']})."


def remover(cfg: dict, servico, id_: str) -> str:
    """Apaga o evento da agenda "Tony" e do `eventos.json`, e guarda o id em `removidos`, para a coleta
    não trazer de volta. Os eventos que dividem o mesmo evento do Google (o mesmo compromisso vindo em
    dois e-mails) saem juntos: senão ficariam apontando para um evento que não existe mais."""
    from googleapiclient.errors import HttpError

    arquivo = config.caminho(cfg["coleta"]["eventos"])
    banco = ler_json(arquivo, {"eventos": {}, "revisar": {}})
    evento = banco["eventos"].get(id_)
    if not evento:
        return f"não há {id_} nos eventos (veja os ids com `tony eventos --ids`)."
    juntos = [i for i, e in banco["eventos"].items()
              if i == id_ or (evento.get("evento_agenda") and e.get("evento_agenda") == evento["evento_agenda"])]
    if evento.get("evento_agenda"):
        try:
            executar(servico.events().delete(calendarId=id_da_agenda(cfg, servico), eventId=evento["evento_agenda"]))
        except HttpError as e:
            if e.resp.status not in (404, 410):  # já apagado à mão na agenda: segue
                raise
    banco.setdefault("removidos", [])
    for i in juntos:
        banco["eventos"].pop(i)
        banco["removidos"].append(i)
    salvar_json(arquivo, banco)
    extra = f" (e mais {len(juntos) - 1} e-mail(s) do mesmo compromisso)" if len(juntos) > 1 else ""
    return f"removido: {evento['titulo']} ({evento['data']}){extra}."
