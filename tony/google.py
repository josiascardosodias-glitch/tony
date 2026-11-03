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


def _arquivos(cfg: dict) -> tuple[Path, Path]:
    pasta = config.caminho(cfg["google"]["pasta"])
    return pasta / "google-cliente.json", pasta / "google-token.json"


def autorizar(cfg: dict) -> None:
    """Abre o navegador para você autorizar o Tony e guarda o token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    cliente, token = _arquivos(cfg)
    if not cliente.is_file():
        raise SystemExit(f"falta o cliente OAuth em {cliente}: rode scripts/assistente-google.sh")
    fluxo = InstalledAppFlow.from_client_secrets_file(str(cliente), ESCOPOS)
    credenciais_novas = fluxo.run_local_server(port=0, open_browser=True,
                                               authorization_prompt_message="Abra este link para autorizar o Tony "
                                                                            "(se o navegador não abriu sozinho):\n{url}\n",
                                               success_message="Pronto: o Tony está autorizado. Pode fechar esta aba.")
    _salvar(token, credenciais_novas)
    print(f"autorizado. Token em {token} (chmod 600).")


def credenciais(cfg: dict):
    """As credenciais válidas, renovadas se preciso. Sem você por perto: nunca abre o navegador."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    _, token = _arquivos(cfg)
    if not token.is_file():
        raise AutorizacaoVencida("o Tony ainda não foi autorizado no Google: rode `uv run tony autorizar`")
    atuais = Credentials.from_authorized_user_file(str(token), ESCOPOS)
    if atuais.valid:
        return atuais
    if not atuais.refresh_token:
        raise AutorizacaoVencida("o token do Google não tem renovação: rode `uv run tony autorizar`")
    try:
        atuais.refresh(Request())
    except RefreshError as e:
        raise AutorizacaoVencida("a autorização do Google venceu (no modo de teste, ela dura 7 dias): "
                                 f"rode `uv run tony autorizar` ({e})") from e
    _salvar(token, atuais)
    return atuais


def servico(cfg: dict, nome: str, versao: str):
    """Um cliente da API (`gmail`/`v1`, `calendar`/`v3`)."""
    from googleapiclient.discovery import build

    return build(nome, versao, credentials=credenciais(cfg), cache_discovery=False)


def _salvar(arquivo: Path, credenciais_validas) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    descritor = os.open(arquivo, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descritor, "w", encoding="utf-8") as f:
        f.write(credenciais_validas.to_json())
    os.chmod(arquivo, 0o600)
