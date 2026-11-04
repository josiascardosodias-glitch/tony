"""Os comandos da v4 que mexem com e-mail e agenda: `autorizar`, `coletar`, `eventos`, `bloquear`,
`agenda`, `aceitar` e `descartar`. Nenhum usa IA."""

from datetime import date

from . import config, google
from .agenda import decidir, remover, sincronizar
from .coleta import bloquear, coletar, ler_json, proximos
from .conversa import DIAS


def linha(e: dict, com_id: bool = False) -> str:
    dia = date.fromisoformat(e["data"])
    hora = f" {e['hora']}" if e["hora"] else ""
    id_ = f"{e['id']}  " if com_id else ""
    return f"{id_}{DIAS[dia.weekday()][:3]} {dia:%d/%m}{hora:6}  {e['titulo']}  ({e['remetente']}, {e['confianca']:.1f})"


def fonte_da_conta(cfg: dict, conta: dict):
    """De onde vêm os e-mails da conta: a API do Gmail (OAuth) ou o App da Web da Faccat."""
    if conta.get("tipo") == "apps-script":
        from .faccat import FonteAppsScript

        return FonteAppsScript(conta)
    from .coleta import FonteGmail

    return FonteGmail(google.servico(cfg, "gmail", "v1", conta["nome"]))


def _servico(cfg: dict, nome: str, versao: str, conta: str | None = None):
    try:
        return google.servico(cfg, nome, versao, conta)
    except google.AutorizacaoVencida as e:
        raise SystemExit(f"[autorização] {e}")


def _agenda(cfg: dict) -> str:
    r = sincronizar(cfg, _servico(cfg, "calendar", "v3"))
    extra = "".join(f", {r[k]} {nome}" for k, nome in (("repetidos", "repetido(s)"), ("ja_estavam", "que já estava(m) lá"))
                    if r[k])
    return f"agenda: {r['criados']} evento(s) criado(s){extra}."


def rodar(cfg: dict, args) -> None:
    if args.comando == "autorizar":
        if google.conta(cfg, args.conta).get("tipo") == "apps-script":
            raise SystemExit("essa conta usa o App da Web da Faccat, não o OAuth: rode `uv run tony faccat`")
        google.autorizar(cfg, args.conta)
    elif args.comando == "faccat":
        from .faccat import configurar

        contas_faccat = [c for c in google.contas(cfg) if c.get("tipo") == "apps-script"]
        if not contas_faccat:
            raise SystemExit("não há conta com tipo: apps-script em coleta.contas (no config.local.yaml)")
        print(configurar(contas_faccat[0], args.url))
    elif args.comando == "bloquear":
        print(bloquear(config.caminho(cfg["coleta"]["bloqueados"]), args.alvo))
    elif args.comando == "eventos":
        if args.revisar:
            duvidosos = ler_json(config.caminho(cfg["coleta"]["eventos"]), {"revisar": {}})["revisar"].values()
            lista = sorted(duvidosos, key=lambda e: e["data"])
        else:
            lista = proximos(cfg, args.dias)
        print("\n".join(linha(e, args.revisar or args.ids) for e in lista) or "nada por aqui.")
        if args.revisar and lista:
            print("\npara decidir: uv run tony aceitar <id>  ·  uv run tony descartar <id>")
    elif args.comando in ("aceitar", "descartar"):
        print(decidir(cfg, args.id, args.comando == "aceitar"))
        if args.comando == "aceitar":
            print(_agenda(cfg))
    elif args.comando == "remover":
        print(remover(cfg, _servico(cfg, "calendar", "v3"), args.id))
    elif args.comando == "agenda":
        print(_agenda(cfg))
    else:
        for conta in google.contas(cfg):  # uma conta com a autorização vencida não para as outras
            from .faccat import ErroDaFaccat

            try:
                r = coletar(cfg, fonte_da_conta(cfg, conta), conta=conta)
            except (google.AutorizacaoVencida, ErroDaFaccat) as e:
                print(f"{conta['nome']}: [conta] {e}")
                continue
            bloqueados = f", {r['bloqueados']} bloqueado(s)" if r["bloqueados"] else ""
            print(f"{conta['nome']}: {r['emails']} e-mail(s) lido(s), {r['eventos']} evento(s) novo(s), "
                  f"{r['revisar']} para revisar{bloqueados}.")
        print(_agenda(cfg))
