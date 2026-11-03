"""Os comandos da v4 que mexem com o e-mail: `autorizar`, `coletar`, `eventos` e `bloquear`. Nenhum usa IA."""

from datetime import date

from . import config, google
from .coleta import bloquear, coletar, ler_json, proximos
from .conversa import DIAS


def linha(e: dict) -> str:
    dia = date.fromisoformat(e["data"])
    hora = f" {e['hora']}" if e["hora"] else ""
    return f"{DIAS[dia.weekday()][:3]} {dia:%d/%m}{hora:6}  {e['titulo']}  ({e['remetente']}, {e['confianca']:.1f})"


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
        print("\n".join(linha(e) for e in lista) or "nada por aqui.")
    else:
        try:
            servico = google.servico(cfg, "gmail", "v1")
        except google.AutorizacaoVencida as e:
            raise SystemExit(f"[autorização] {e}")
        r = coletar(cfg, servico)
        bloqueados = f", {r['bloqueados']} bloqueado(s)" if r["bloqueados"] else ""
        print(f"{r['emails']} e-mail(s) lido(s), {r['eventos']} evento(s) novo(s), "
              f"{r['revisar']} para revisar{bloqueados}.")
