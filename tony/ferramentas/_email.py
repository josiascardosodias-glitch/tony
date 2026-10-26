"""Leitura de e-mail por IMAP, só leitura: a caixa é aberta em modo somente leitura e as mensagens
são buscadas com BODY.PEEK, então nada é apagado nem marcado como lido.

`caixa_imap` devolve a função que a ferramenta `ler_emails` usa. Nos testes, ela é trocada por uma
caixa de exemplo — a ferramenta não sabe a diferença.
"""

import email
import html
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
ESPERA = 30  # segundos; sem isso, um servidor mudo prende o resumo do dia para sempre


def caixa_imap(servidor: str, usuario: str, senha: str, filtro: str = "") -> Callable[[int], list[dict]]:
    """Função que devolve os e-mails dos últimos `dias` (os mais recentes primeiro).

    `filtro` é um critério IMAP extra (ex.: 'FROM "faculdade.edu.br"'): só esses e-mails vão para o modelo.
    """
    def buscar(dias: int) -> list[dict]:
        desde = datetime.now() - timedelta(days=dias)
        criterio = f"(SINCE {desde.day:02d}-{MESES[desde.month - 1]}-{desde.year}{' ' + filtro if filtro else ''})"
        with imaplib.IMAP4_SSL(servidor, timeout=ESPERA) as imap:
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
        "data": _data(mensagem["Date"]),
        "de": _cabecalho(mensagem["From"]),
        "assunto": _cabecalho(mensagem["Subject"]),
        "texto": _texto(mensagem)[:CARACTERES_POR_MENSAGEM],
    }


def _cabecalho(valor: str | None) -> str:
    """Remetente ou assunto legível (`=?utf-8?q?Aula_de_C=C3=A1lculo?=` vira "Aula de Cálculo")."""
    try:
        return str(make_header(decode_header(valor or "")))
    except (LookupError, ValueError, UnicodeError):  # charset desconhecido: fica o texto como veio
        return str(valor or "")


def _data(cabecalho: str | None) -> str:
    """A data do cabeçalho; vazia se ele faltar ou vier quebrado (um e-mail torto não derruba a caixa)."""
    try:
        return parsedate_to_datetime(cabecalho).strftime("%d/%m/%Y %H:%M") if cabecalho else ""
    except (TypeError, ValueError):
        return ""


def _texto(mensagem: email.message.Message) -> str:
    """O texto puro da mensagem; se ela só tiver HTML, o HTML sem as tags."""
    partes = list(mensagem.walk()) if mensagem.is_multipart() else [mensagem]
    for tipo in ("text/plain", "text/html"):
        for parte in partes:
            if parte.get_content_type() == tipo and not parte.get_filename():
                bruto = parte.get_payload(decode=True) or b""
                try:
                    texto = bruto.decode(parte.get_content_charset() or "utf-8", "replace")
                except LookupError:  # charset que o Python não conhece
                    texto = bruto.decode("utf-8", "replace")
                if tipo == "text/html":
                    texto = html.unescape(re.sub(r"<(script|style).*?</\1>|<[^>]+>", " ", texto, flags=re.S))
                return re.sub(r"\s+", " ", texto).strip()
    return ""
