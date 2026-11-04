"""Leva segredos e dados do PC para o Tony no Apps Script, pela rota de administração do App da Web
(`doPost` com `?admin=<ADMIN_SEGREDO>`). Nada passa pela tela: os valores saem de `~/.config/tony/` e
da pasta de produção, e a resposta traz só nomes e números.

    uv run python appsscript/configurar.py --segredos        # cliente OAuth, token da pessoal2, Faccat
    uv run python appsscript/configurar.py --faccat          # segredo da Faccat e a URL para o script dela
    uv run python appsscript/configurar.py --tokens          # só o token da pessoal2 (depois de renovar)
    uv run python appsscript/configurar.py --importar        # eventos e estados da produção (a virada)
    uv run python appsscript/configurar.py --acao conferir --acao contas
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

SEGREDOS = Path.home() / ".config" / "tony"
PRODUCAO = Path.home() / "projetos" / "tony-producao" / "dados"
VISTOS_GUARDADOS = 2000


def _ler_env(arquivo: Path) -> dict:
    valores = {}
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        if chave.strip():
            valores[chave.strip()] = valor.strip().strip("'\"")
    return valores


def url_admin() -> str:
    implantacao = (SEGREDOS / "appsscript-implantacao").read_text().strip()
    admin = (SEGREDOS / "appsscript-admin").read_text().strip()
    return f"https://script.google.com/macros/s/{implantacao}/exec?admin={admin}"


def pedir(pedido: dict) -> dict:
    """Manda o pedido. O App da Web responde com um redirecionamento; seguindo, vem o JSON."""
    r = httpx.post(url_admin(), json=pedido, follow_redirects=True, timeout=300)
    try:
        resposta = r.json()
    except ValueError:
        sys.exit(f"o App da Web não respondeu JSON (HTTP {r.status_code}): confira a implantação e o ADMIN_SEGREDO")
    if not resposta.get("ok"):
        sys.exit(f"o Tony recusou: {resposta.get('erro', resposta)}")
    return resposta


def segredos_do_pc(so_tokens: bool = False) -> dict:
    token = json.loads((SEGREDOS / "google-token-pessoal2.json").read_text())
    valores = {"TOKEN_PESSOAL2": token["refresh_token"]}
    if so_tokens:
        return valores
    cliente = json.loads((SEGREDOS / "google-cliente.json").read_text())
    cliente = cliente.get("installed") or cliente.get("web")
    valores |= {"GOOGLE_CLIENTE_ID": cliente["client_id"], "GOOGLE_CLIENTE_SEGREDO": cliente["client_secret"]}
    return valores


def segredo_da_faccat() -> dict:
    """O segredo que a Faccat põe na URL do Tony. Gera na primeira vez; a URL completa vai para um arquivo
    (chmod 600) para você copiar para as propriedades do script da Faccat, sem passar pela tela."""
    import secrets

    arquivo = SEGREDOS / "faccat-segredo"
    if not arquivo.is_file():
        arquivo.write_text(secrets.token_hex(24))
        arquivo.chmod(0o600)
    segredo = arquivo.read_text().strip()
    implantacao = (SEGREDOS / "appsscript-implantacao").read_text().strip()
    url = SEGREDOS / "faccat-url-do-tony"
    url.write_text(f"https://script.google.com/macros/s/{implantacao}/exec?faccat={segredo}\n")
    url.chmod(0o600)
    print(f"URL para a propriedade TONY_URL do script da Faccat: cat {url}", file=sys.stderr)
    return {"FACCAT_SEGREDO": segredo}


def dados_da_producao() -> dict:
    """Os dados da produção como o Apps Script guarda. A agenda "Tony" do Apps Script é outra (ele só mexe
    no que criou): todo evento perde o `evento_agenda` e é criado de novo na agenda nova."""
    def ler(nome: str, padrao: dict) -> dict:
        arquivo = PRODUCAO / nome
        return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.is_file() else padrao

    banco = ler("eventos.json", {"eventos": {}, "revisar": {}})
    for secao in ("eventos", "revisar"):
        for evento in banco.get(secao, {}).values():
            evento["evento_agenda"] = None
    banco.pop("apagar_no_google", None)
    dados = {"eventos": banco, "bloqueados": ler("bloqueados.json", {"enderecos": [], "dominios": []})}
    for arquivo, nome in (("coleta.json", "pessoal"), ("coleta-pessoal2.json", "pessoal2"), ("coleta-faccat.json", "faccat")):
        estado = ler(arquivo, {"ultima": None, "vistos": []})
        estado["vistos"] = estado["vistos"][-VISTOS_GUARDADOS:]
        dados[f"coleta-{nome}"] = estado
    telegram = ler("telegram.json", {"offset": 0, "avisados": []})
    dados["telegram"] = {"maior_update": max(telegram.get("offset", 0) - 1, 0), "avisados": telegram.get("avisados", [])}
    return dados


def principal() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--segredos", action="store_true")
    p.add_argument("--tokens", action="store_true")
    p.add_argument("--faccat", action="store_true")
    p.add_argument("--importar", action="store_true")
    p.add_argument("--acao", action="append", default=[])
    args = p.parse_args()
    pedido = {"acoes": args.acao}
    if args.segredos or args.tokens:
        pedido["segredos"] = segredos_do_pc(so_tokens=args.tokens and not args.segredos)
    if args.faccat:
        pedido.setdefault("segredos", {}).update(segredo_da_faccat())
    if args.importar:
        pedido["dados"] = dados_da_producao()
    resposta = pedir(pedido)
    print(json.dumps({k: v for k, v in resposta.items() if k != "ok"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    principal()
