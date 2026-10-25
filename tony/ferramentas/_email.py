"""Leitura de e-mail por IMAP, só leitura: a caixa é aberta em modo somente leitura e as mensagens
são buscadas com BODY.PEEK, então nada é apagado nem marcado como lido.

`caixa_imap` devolve a função que a ferramenta `ler_emails` usa. Nos testes, ela é trocada por uma
caixa de exemplo — a ferramenta não sabe a diferença.
"""

import email
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from typing import Callable

# O IMAP quer o mês em inglês (SINCE 24-Oct-2026); o %b do Python segue o idioma do sistema.
MESES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MAX_MENSAGENS = 30
CARACTERES_POR_MENSAGEM = 800


def caixa_imap(servidor: str, usuario: str, senha: str, filtro: str = "") -> Callable[[int], list[dict]]:
    """Função que devolve os e-mails dos últimos `dias` (os mais recentes primeiro).

    `filtro` é um critério IMAP extra (ex.: 'FROM "faculdade.edu.br"'): só esses e-mails vão para o modelo.
    """
    def buscar(dias: int) -> list[dict]:
        desde = datetime.now() - timedelta(days=dias)
        criterio = f"(SINCE {desde.day:02d}-{MESES[desde.month - 1]}-{desde.year}{' ' + filtro if filtro else ''})"
        with imaplib.IMAP4_SSL(servidor) as imap:
            imap.login(usuario, senha)
            imap.select("INBOX", readonly=True)
            _, encontrados = imap.search(None, criterio)
            mensagens = []
            for numero in reversed(encontrados[0].split()[-MAX_MENSAGENS:]):
                _, dados = imap.fetch(numero, "(BODY.PEEK[])")
                mensagens.append(_resumir(email.message_from_bytes(dados[0][1])))
        return mensagens
    return buscar


def _resumir(mensagem: email.message.Message) -> dict:
    return {
        "data": parsedate_to_datetime(mensagem["Date"]).strftime("%d/%m/%Y %H:%M") if mensagem["Date"] else "",
        "de": str(make_header(decode_header(mensagem["From"] or ""))),
        "assunto": str(make_header(decode_header(mensagem["Subject"] or ""))),
        "texto": _texto(mensagem)[:CARACTERES_POR_MENSAGEM],
    }


def _texto(mensagem: email.message.Message) -> str:
    """O texto puro da mensagem; se ela só tiver HTML, o HTML sem as tags."""
    partes = list(mensagem.walk()) if mensagem.is_multipart() else [mensagem]
    for tipo in ("text/plain", "text/html"):
        for parte in partes:
            if parte.get_content_type() == tipo and not parte.get_filename():
                texto = parte.get_payload(decode=True).decode(parte.get_content_charset() or "utf-8", "replace")
                if tipo == "text/html":
                    texto = re.sub(r"<(script|style).*?</\1>|<[^>]+>", " ", texto, flags=re.S)
                return re.sub(r"\s+", " ", texto).strip()
    return ""
