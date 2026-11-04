"""Acesso às APIs do Google (Gmail e Agenda) com OAuth de app para computador.

O cliente OAuth e o token ficam em `google.pasta` (padrão `~/.config/tony/`), fora do repositório, com
chmod 600. Os escopos são os menores que servem: o Gmail só leitura e, na Agenda, só as agendas que o
próprio Tony criar (`calendar.app.created`): ele não enxerga nem mexe nas suas outras agendas.

Com o app "Em teste" no Google Cloud, a autorização vence a cada 7 dias: aí `credenciais()` avisa
com `AutorizacaoVencida`, e `uv run tony autorizar` abre o navegador para autorizar de novo.
"""

import os
from pathlib import Path

from . import config

ESCOPOS = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.app.created",
]


class AutorizacaoVencida(Exception):
    """O token não vale mais (ou nunca existiu) e não dá para renovar sem você no navegador."""


def contas(cfg: dict) -> list[dict]:
    return cfg["coleta"]["contas"]


def conta(cfg: dict, nome: str | None = None) -> dict:
    """A conta pelo nome; sem nome, a primeira (a que guarda a agenda)."""
    if nome is None:
        return contas(cfg)[0]
    for c in contas(cfg):
        if c["nome"] == nome:
            return c
    raise SystemExit(f"não há a conta {nome!r} em coleta.contas (há: {', '.join(c['nome'] for c in contas(cfg))})")


def _arquivos(cfg: dict, nome: str | None = None) -> tuple[Path, Path]:
    """O cliente OAuth é um só; o token é um por conta (o da primeira conta não tem sufixo)."""
    pasta = config.caminho(cfg["google"]["pasta"])
    c = conta(cfg, nome)
    sufixo = "" if c is contas(cfg)[0] else f"-{c['nome']}"
    return pasta / "google-cliente.json", pasta / f"google-token{sufixo}.json"


def autorizar(cfg: dict, nome: str | None = None) -> None:
    """Abre o navegador para você autorizar o Tony numa conta e guarda o token dela."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    c = conta(cfg, nome)
    cliente, token = _arquivos(cfg, nome)
    if not cliente.is_file():
        raise SystemExit(f"falta o cliente OAuth em {cliente}: rode scripts/assistente-google.sh")
    fluxo = InstalledAppFlow.from_client_secrets_file(str(cliente), ESCOPOS)
    print(f"Conta: {c['nome']}" + (f" ({c['email']}): entre com ela no Google." if c.get("email") else "."))
    extras = {"login_hint": c["email"]} if c.get("email") else {}
    credenciais_novas = fluxo.run_local_server(port=0, open_browser=True, **extras,
                                               authorization_prompt_message="Abra este link para autorizar o Tony "
                                                                            "(se o navegador não abriu sozinho):\n{url}\n",
                                               success_message="Pronto: o Tony está autorizado. Pode fechar esta aba.")
    _salvar(token, credenciais_novas)
    print(f"autorizado. Token em {token} (chmod 600).")


def credenciais(cfg: dict, nome: str | None = None):
    """As credenciais válidas, renovadas se preciso. Sem você por perto: nunca abre o navegador."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    _, token = _arquivos(cfg, nome)
    comando = "uv run tony autorizar" + (f" --conta {nome}" if nome and nome != contas(cfg)[0]["nome"] else "")
    if not token.is_file():
        raise AutorizacaoVencida(f"o Tony ainda não foi autorizado nessa conta do Google: rode `{comando}`")
    atuais = Credentials.from_authorized_user_file(str(token), ESCOPOS)
    if atuais.valid:
        return atuais
    if not atuais.refresh_token:
        raise AutorizacaoVencida(f"o token do Google não tem renovação: rode `{comando}`")
    try:
        atuais.refresh(Request())
    except RefreshError as e:
        raise AutorizacaoVencida("a autorização do Google venceu (no modo de teste, ela dura 7 dias): "
                                 f"rode `{comando}` ({e})") from e
    _salvar(token, atuais)
    return atuais


def servico(cfg: dict, nome: str, versao: str, conta_nome: str | None = None):
    """Um cliente da API (`gmail`/`v1`, `calendar`/`v3`) de uma conta (sem conta: a primeira)."""
    from googleapiclient.discovery import build

    return build(nome, versao, credentials=credenciais(cfg, conta_nome), cache_discovery=False)


def _salvar(arquivo: Path, credenciais_validas) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    descritor = os.open(arquivo, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descritor, "w", encoding="utf-8") as f:
        f.write(credenciais_validas.to_json())
    os.chmod(arquivo, 0o600)
