"""Os comandos da v4 que mexem com e-mail e agenda: `autorizar`, `coletar`, `eventos`, `bloquear`,
`agenda`, `aceitar` e `descartar`. Nenhum usa IA."""

from datetime import date

from . import config, google
from .agenda import decidir, sincronizar
from .coleta import bloquear, coletar, ler_json, proximos
from .conversa import DIAS


def linha(e: dict, com_id: bool = False) -> str:
    dia = date.fromisoformat(e["data"])
    hora = f" {e['hora']}" if e["hora"] else ""
    id_ = f"{e['id']}  " if com_id else ""
    return f"{id_}{DIAS[dia.weekday()][:3]} {dia:%d/%m}{hora:6}  {e['titulo']}  ({e['remetente']}, {e['confianca']:.1f})"


def _servico(cfg: dict, nome: str, versao: str):
    try:
        return google.servico(cfg, nome, versao)
    except google.AutorizacaoVencida as e:
        raise SystemExit(f"[autorização] {e}")


def _agenda(cfg: dict) -> str:
    r = sincronizar(cfg, _servico(cfg, "calendar", "v3"))
    extra = "".join(f", {r[k]} {nome}" for k, nome in (("repetidos", "repetido(s)"), ("ja_estavam", "que já estava(m) lá"))
                    if r[k])
    return f"agenda: {r['criados']} evento(s) criado(s){extra}."


def rodar(cfg: dict, args) -> None:
    if args.comando == "autorizar":
        google.autorizar(cfg)
    elif args.comando == "bloquear":
        print(bloquear(config.caminho(cfg["coleta"]["bloqueados"]), args.alvo))
    elif args.comando == "eventos":
        if args.revisar:
            duvidosos = ler_json(config.caminho(cfg["coleta"]["eventos"]), {"revisar": {}})["revisar"].values()
            lista = sorted(duvidosos, key=lambda e: e["data"])
        else:
            lista = proximos(cfg, args.dias)
        print("\n".join(linha(e, args.revisar) for e in lista) or "nada por aqui.")
        if args.revisar and lista:
            print("\npara decidir: uv run tony aceitar <id>  ·  uv run tony descartar <id>")
    elif args.comando in ("aceitar", "descartar"):
        print(decidir(cfg, args.id, args.comando == "aceitar"))
        if args.comando == "aceitar":
            print(_agenda(cfg))
    elif args.comando == "agenda":
        print(_agenda(cfg))
    else:
        r = coletar(cfg, _servico(cfg, "gmail", "v1"))
        bloqueados = f", {r['bloqueados']} bloqueado(s)" if r["bloqueados"] else ""
        print(f"{r['emails']} e-mail(s) lido(s), {r['eventos']} evento(s) novo(s), "
              f"{r['revisar']} para revisar{bloqueados}.")
        print(_agenda(cfg))
