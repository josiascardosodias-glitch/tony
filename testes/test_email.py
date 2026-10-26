"""Testes de código do e-mail: o `caixa_imap` de verdade conversando com um servidor IMAP falso.

As falas de teste trocam a caixa por uma lista pronta; aqui é o contrário: o que se testa é o IMAP —
o comando que sai, o filtro, a leitura sem marcar como lido e os e-mails tortos. Sem Gmail e sem
modelo: roda em poucos segundos.

    uv run python -m unittest discover testes
"""

import imaplib
import re
import socketserver
import threading
import unittest
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime
from unittest import mock

from tony import ferramentas
from tony.ferramentas import ErroDaFerramenta
from tony.ferramentas._email import MAX_MENSAGENS, caixa_imap
from tony.ferramentas.ler_emails import ler_emails

MESES = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


class ServidorFalso(socketserver.ThreadingTCPServer):
    """Um IMAP mínimo: LOGIN, EXAMINE/SELECT, SEARCH (SINCE e FROM), FETCH e LOGOUT. Guarda cada
    comando recebido, para o teste conferir o que o Tony pediu."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, mensagens: list[tuple[datetime, bytes, str]], senha: str = "certa"):
        super().__init__(("127.0.0.1", 0), Atendente)
        self.mensagens, self.senha, self.comandos = mensagens, senha, []


class Atendente(socketserver.StreamRequestHandler):
    def responder(self, linha: str) -> None:
        self.wfile.write(linha.encode() + b"\r\n")

    def handle(self) -> None:
        servidor = self.server
        self.responder("* OK [CAPABILITY IMAP4rev1] servidor falso pronto")
        for bruto in self.rfile:
            tag, _, resto = bruto.decode().strip().partition(" ")
            comando, _, args = resto.partition(" ")
            comando = comando.upper()
            servidor.comandos.append(f"{comando} {args}".strip())
            if comando == "CAPABILITY":
                self.responder("* CAPABILITY IMAP4rev1")
                self.responder(f"{tag} OK pronto")
            elif comando == "LOGIN":
                certo = args.split(" ", 1)[1].strip('"') == servidor.senha
                self.responder(f"{tag} OK logado" if certo else f"{tag} NO [AUTHENTICATIONFAILED] senha errada")
            elif comando in ("EXAMINE", "SELECT"):
                self.responder(f"* {len(servidor.mensagens)} EXISTS")
                self.responder(f"{tag} OK [{'READ-ONLY' if comando == 'EXAMINE' else 'READ-WRITE'}] aberta")
            elif comando == "SEARCH":
                self.responder("* SEARCH " + " ".join(str(n) for n in self.buscar(args)))
                self.responder(f"{tag} OK busca feita")
            elif comando in ("FETCH", "STORE", "EXPUNGE", "COPY"):
                if comando == "FETCH":
                    numero = int(args.split()[0])
                    corpo = servidor.mensagens[numero - 1][1]
                    self.wfile.write(f"* {numero} FETCH (BODY[] {{{len(corpo)}}}\r\n".encode() + corpo + b")\r\n")
                self.responder(f"{tag} OK feito")
            elif comando == "LOGOUT":
                self.responder("* BYE até mais")
                self.responder(f"{tag} OK saindo")
                return
            else:
                self.responder(f"{tag} BAD comando desconhecido")

    def buscar(self, criterio: str) -> list[int]:
        """Números das mensagens que passam no SINCE (pela data de chegada) e no FROM, se houver."""
        desde = re.search(r"SINCE (\d{2})-(\w{3})-(\d{4})", criterio)
        de = re.search(r'FROM "([^"]+)"', criterio)
        limite = datetime(int(desde[3]), MESES[desde[2]], int(desde[1])) if desde else datetime.min
        return [n for n, (chegada, _, remetente) in enumerate(self.server.mensagens, 1)
                if chegada >= limite and (not de or de[1] in remetente)]


def mensagem(de: str, assunto: str, chegada: datetime, texto: str = "", html: str = "",
             data: str | None = None) -> tuple[datetime, bytes, str]:
    m = EmailMessage()
    m["From"], m["Subject"] = de, assunto
    m["Date"] = data if data is not None else format_datetime(chegada.astimezone())
    if texto:
        m.set_content(texto)
    if html:
        m.add_alternative(html, subtype="html") if texto else m.set_content(html, subtype="html")
    return chegada, m.as_bytes(), de


def bruta(de: str, chegada: datetime, cabecalhos_e_corpo: str) -> tuple[datetime, bytes, str]:
    """Mensagem escrita à mão, para os casos que o EmailMessage não deixa montar (charset estranho)."""
    return chegada, f"From: {de}\r\n{cabecalhos_e_corpo}".encode("latin-1"), de


HOJE = datetime.now().replace(microsecond=0)
FACULDADE = "Secretaria <avisos@faculdade.edu.br>"


class TestCaixaImap(unittest.TestCase):
    def ligar(self, mensagens, senha="certa"):  # a senha que o Tony usa; a do servidor é "certa"
        """Sobe o servidor falso e devolve a caixa do Tony apontada para ele."""
        servidor = ServidorFalso(mensagens)
        threading.Thread(target=servidor.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        self.addCleanup(servidor.server_close)
        self.addCleanup(servidor.shutdown)
        porta = servidor.server_address[1]
        # O Tony abre IMAP4_SSL na porta 993; o falso fala IMAP sem TLS numa porta qualquer.
        sem_tls = mock.patch("imaplib.IMAP4_SSL", lambda host, **kw: imaplib.IMAP4("127.0.0.1", porta, **kw))
        sem_tls.start()
        self.addCleanup(sem_tls.stop)
        self.servidor = servidor
        return caixa_imap("imap.gmail.com", "voce@gmail.com", senha, 'FROM "faculdade.edu.br"')

    def test_le_so_os_recentes_da_faculdade_e_o_mais_novo_primeiro(self):
        caixa = self.ligar([
            mensagem(FACULDADE, "Calendário antigo", HOJE - timedelta(days=20), "nada"),
            mensagem(FACULDADE, "Prova de Cálculo I", HOJE - timedelta(days=2), "A prova é dia 12/11, sala 204."),
            mensagem("Loja <ofertas@loja.com>", "50% de desconto", HOJE - timedelta(days=1), "compre"),
            mensagem(FACULDADE, "Entrega do trabalho", HOJE, "Entregar até sexta."),
        ])
        emails = caixa(7)
        self.assertEqual([m["assunto"] for m in emails], ["Entrega do trabalho", "Prova de Cálculo I"])
        self.assertEqual(emails[1]["de"], FACULDADE)
        self.assertEqual(emails[1]["texto"], "A prova é dia 12/11, sala 204.")
        self.assertEqual(emails[0]["data"], f"{HOJE:%d/%m/%Y %H:%M}")

    def test_nao_mexe_na_caixa(self):
        """Só leitura: abre com EXAMINE, busca com BODY.PEEK e nunca marca, move nem apaga."""
        self.ligar([mensagem(FACULDADE, "Aviso", HOJE, "oi")])(7)
        comandos = self.servidor.comandos
        self.assertIn("EXAMINE INBOX", comandos)
        self.assertFalse([c for c in comandos if c.split()[0] in ("SELECT", "STORE", "EXPUNGE", "COPY", "MOVE")])
        self.assertTrue(all("BODY.PEEK[]" in c for c in comandos if c.startswith("FETCH")))
        self.assertEqual(comandos[-1], "LOGOUT")

    def test_busca_com_mes_em_ingles_e_o_filtro(self):
        self.ligar([])(3)
        desde = HOJE - timedelta(days=3)
        mes = list(MESES)[desde.month - 1]
        self.assertIn(f'SEARCH (SINCE {desde:%d}-{mes}-{desde.year} FROM "faculdade.edu.br")', self.servidor.comandos)

    def test_html_sem_tags_e_assunto_codificado(self):
        caixa = self.ligar([mensagem(
            FACULDADE, "Reposição de aula — Física", HOJE,
            html="<html><style>p{color:red}</style><body><p>Reposi&ccedil;&atilde;o no <b>sábado</b>,"
                 "&nbsp;8h.</p><script>rastrear()</script></body></html>")])
        [aviso] = caixa(1)
        self.assertEqual(aviso["assunto"], "Reposição de aula — Física")
        self.assertEqual(aviso["texto"], "Reposição no sábado , 8h.")

    def test_prefere_o_texto_puro_e_ignora_anexo(self):
        m = EmailMessage()
        m["From"], m["Subject"], m["Date"] = FACULDADE, "Ementa", format_datetime(HOJE.astimezone())
        m.add_attachment(b"conteudo do anexo", maintype="text", subtype="plain", filename="ementa.txt")
        m.add_attachment("Segue a ementa.")  # o anexo vem antes do corpo: tem que ser pulado
        m.add_attachment("<p>Segue a <i>ementa</i>.</p>", subtype="html")
        [ementa] = self.ligar([(HOJE, m.as_bytes(), FACULDADE)])(1)
        self.assertEqual(ementa["texto"], "Segue a ementa.")

    def test_email_torto_nao_derruba_a_caixa(self):
        caixa = self.ligar([
            bruta(FACULDADE, HOJE, "Subject: =?x-desconhecido?q?Aviso?=\r\nDate: ontem de tarde\r\n"
                                   "Content-Type: text/plain; charset=x-desconhecido\r\n\r\nSem data certa.\r\n"),
            bruta(FACULDADE, HOJE, "Subject: Sem corpo\r\n\r\n"),
            mensagem(FACULDADE, "Normal", HOJE, "ok"),
        ])
        torto, vazio, normal = reversed(caixa(1))
        self.assertEqual((torto["data"], torto["texto"]), ("", "Sem data certa."))
        self.assertEqual(vazio["texto"], "")
        self.assertEqual(normal["texto"], "ok")

    def test_texto_cortado_e_no_maximo_30_mensagens(self):
        caixa = self.ligar([mensagem(FACULDADE, f"Aviso {n}", HOJE, "x" * 2000) for n in range(1, 41)])
        emails = caixa(1)
        self.assertEqual(len(emails), MAX_MENSAGENS)
        self.assertEqual(emails[0]["assunto"], "Aviso 40")
        self.assertEqual(len(emails[0]["texto"]), 800)

    def test_senha_errada_vira_erro_para_o_modelo(self):
        ferramentas.ambiente.caixa_de_email = self.ligar([], senha="errada")
        self.addCleanup(setattr, ferramentas.ambiente, "caixa_de_email", None)
        with self.assertRaisesRegex(ErroDaFerramenta, "AUTHENTICATIONFAILED"):
            ler_emails(7)

    def test_ferramenta_sobre_a_caixa_de_verdade(self):
        ferramentas.ambiente.caixa_de_email = self.ligar([
            mensagem(FACULDADE, "Prova de Cálculo I", HOJE, "Dia 12/11."),
            mensagem(FACULDADE, "Festa junina", HOJE, "Traga um prato."),
        ])
        self.addCleanup(setattr, ferramentas.ambiente, "caixa_de_email", None)
        resposta = ler_emails(7, termos="prova")
        self.assertIn("Assunto: Prova de Cálculo I", resposta)
        self.assertNotIn("Festa", resposta)
        self.assertIn("nenhum e-mail", ler_emails(7, termos="rematrícula"))


if __name__ == "__main__":
    unittest.main()
