"""Testes de código da coleta: um Gmail falso, em memória, no lugar da API.

    uv run python -m unittest discover testes
"""

import base64
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tony import config
from tony.coleta import bloqueado, bloquear, coletar, consulta, executar, ler_bloqueados, proximos, titulo

# 03/11/2026 10:00, horário de Brasília
AGORA = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc).astimezone()


def b64(texto: str) -> str:
    return base64.urlsafe_b64encode(texto.encode()).decode()


def mensagem(id_: str, de: str, assunto: str, corpo: str, html: bool = False, ics: str = "",
             em_massa: bool = False) -> dict:
    partes = [{"mimeType": "text/html" if html else "text/plain", "body": {"data": b64(corpo)}}]
    if ics:
        partes.append({"mimeType": "text/calendar", "filename": "invite.ics", "body": {"attachmentId": "anexo-1"}})
    return {"id": id_, "internalDate": str(int(AGORA.timestamp() * 1000)), "snippet": corpo[:40],
            "payload": {"mimeType": "multipart/mixed", "headers": [{"name": "From", "value": de},
                                                                  {"name": "Subject", "value": assunto}]
                        + ([{"name": "List-Unsubscribe", "value": "<mailto:sair@x.com>"}] if em_massa else []),
                        "parts": partes}, "_ics": ics}


class GmailFalso:
    """Imita users().messages().list/get/attachments().get(...).execute() com uma lista de mensagens."""

    def __init__(self, mensagens: list[dict]):
        self.mensagens = {m["id"]: m for m in mensagens}
        self.buscas: list[str] = []
        self.baixadas: list[str] = []

    def users(self):
        return self

    def messages(self):
        return self

    def attachments(self):
        return self

    def list(self, userId, q, pageToken=None, maxResults=100):
        self.buscas.append(q)
        bloqueados = [p[len("-from:"):] for p in q.split() if p.startswith("-from:")]
        ids = [{"id": i} for i, m in self.mensagens.items()
               if not any(b in m["payload"]["headers"][0]["value"] for b in bloqueados)]
        return Executar({"messages": ids})

    def get(self, userId, messageId=None, id=None, format=None):
        if messageId:  # anexo
            return Executar({"data": b64(self.mensagens[messageId]["_ics"])})
        self.baixadas.append(id)
        return Executar(copy.deepcopy(self.mensagens[id]))


class Executar:
    def __init__(self, resposta):
        self.resposta = resposta

    def execute(self):
        return self.resposta


ICS = "BEGIN:VCALENDAR\nBEGIN:VEVENT\nDTSTART:20261118T140000\nSUMMARY:Entrevista de estágio\nEND:VEVENT\nEND:VCALENDAR\n"


class TestColeta(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.cfg = config.carregar()
        self.cfg["coleta"] = {**self.cfg["coleta"], "eventos": str(self.pasta / "eventos.json"),
                              "estado": str(self.pasta / "coleta.json"), "bloqueados": str(self.pasta / "bloqueados.json"),
                              "contas": [{"nome": "pessoal", "email": ""}]}
        self.gmail = GmailFalso([
            mensagem("m1", "Secretaria <secretaria@faculdade.edu.br>", "Prova remarcada",
                     "A prova de Cálculo foi remarcada para 12/11, às 19h."),
            mensagem("m2", "Loja <ofertas@loja.com>", "Promoção até 30/11", "Compre já, a oferta vai até 30/11."),
            mensagem("m3", "RH <rh@empresa.com>", "Convite: Entrevista", "Você foi convidado.", ics=ICS),
            mensagem("m4", "Amigo <amigo@gmail.com>", "Fotos", "<p>Olha a foto de <b>15/11</b>.</p>", html=True),
        ])

    def banco(self) -> dict:
        return json.loads((self.pasta / "eventos.json").read_text(encoding="utf-8"))

    def test_eventos_revisar_e_estado(self):
        r = coletar(self.cfg, self.gmail, AGORA)
        self.assertEqual(r, {"emails": 4, "eventos": 2, "revisar": 2, "bloqueados": 0, "repetidos": 0})  # a promoção vai para revisar
        eventos = self.banco()["eventos"]
        prova = eventos["m1-1"]
        self.assertEqual((prova["titulo"], prova["data"], prova["hora"]), ("Prova remarcada", "2026-11-12", "19:00"))
        self.assertEqual(prova["link"], "https://mail.google.com/mail/u/0/#all/m1")
        entrevista = [e for e in eventos.values() if e["origem"] == "ics"][0]
        self.assertEqual((entrevista["titulo"], entrevista["data"], entrevista["hora"]),
                         ("Entrevista de estágio", "2026-11-18", "14:00"))
        self.assertEqual(sorted(e["data"] for e in self.banco()["revisar"].values()), ["2026-11-15", "2026-11-30"])  # a foto e a promoção
        estado = json.loads((self.pasta / "coleta.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(estado["vistos"]), ["m1", "m2", "m3", "m4"])

    def test_segunda_rodada_nao_baixa_de_novo(self):
        coletar(self.cfg, self.gmail, AGORA)
        self.gmail.baixadas.clear()
        r = coletar(self.cfg, self.gmail, AGORA)
        self.assertEqual(r["emails"], 0)
        self.assertEqual(self.gmail.baixadas, [])

    def test_bloqueado_sai_da_busca_e_nem_e_baixado(self):
        bloquear(self.pasta / "bloqueados.json", "@loja.com")
        r = coletar(self.cfg, self.gmail, AGORA)
        self.assertIn("-from:loja.com", self.gmail.buscas[0])
        self.assertNotIn("m2", self.gmail.baixadas)
        self.assertEqual(r["eventos"], 2)

    def test_bloqueado_que_escapou_da_busca_e_barrado_pelo_cabecalho(self):
        (self.pasta / "bloqueados.json").write_text(json.dumps({"enderecos": ["OFERTAS@loja.com"], "dominios": []}))
        self.gmail.list = lambda **k: Executar({"messages": [{"id": i} for i in self.gmail.mensagens]})
        r = coletar(self.cfg, self.gmail, AGORA)
        self.assertEqual(r["bloqueados"], 1)
        self.assertFalse(any(e["remetente"] == "ofertas@loja.com" for e in self.banco()["eventos"].values()))

    def test_primeira_vez_olha_30_dias_e_depois_desde_a_ultima(self):
        coletar(self.cfg, self.gmail, AGORA)
        primeira, = [p for p in self.gmail.buscas[0].split() if p.startswith("after:")]
        self.assertEqual(int(primeira[len("after:"):]), int(AGORA.timestamp()) - 30 * 86400)
        coletar(self.cfg, self.gmail, AGORA)
        segunda, = [p for p in self.gmail.buscas[1].split() if p.startswith("after:")]
        self.assertEqual(int(segunda[len("after:"):]), int(AGORA.timestamp()) - 3600)

    def test_em_massa_perde_confianca_e_passado_sai(self):
        self.gmail = GmailFalso([
            mensagem("n1", "Curso <oi@curso.com>", "Últimos dias", "As inscrições vão até 12/11 às 23h59.", em_massa=True),
            mensagem("n2", "Barbearia <nao@barbearia.com>", "Lembrete", "Seu horário é dia 12/11 às 15h."),
            mensagem("n3", "Amigo <a@gmail.com>", "Prova", "A prova foi 01/11/2026, a entrega é 05/11 às 10h."),
        ])
        coletar(self.cfg, self.gmail, AGORA)
        banco = self.banco()
        self.assertEqual(banco["revisar"]["n1-1"]["confianca"], 0.5)  # 0.9 de compromisso com hora, menos 0.4
        self.assertIn("n2-1", banco["eventos"])
        self.assertEqual([e["data"] for e in banco["eventos"].values() if e["email"] == "n3"], ["2026-11-05"])

    def test_segunda_conta_tem_prefixo_estado_proprio_e_link_da_conta(self):
        self.cfg["coleta"]["contas"] = [{"nome": "pessoal", "email": "a@gmail.com"},
                                        {"nome": "outra", "email": "b@gmail.com"}]
        coletar(self.cfg, self.gmail, AGORA)
        self.gmail.mensagens["m9"] = mensagem("m9", "Clínica <c@clinica.com>", "Consulta", "Sua consulta é 20/11 às 9h.")
        coletar(self.cfg, self.gmail, AGORA, conta=self.cfg["coleta"]["contas"][1])
        banco = self.banco()
        eventos = banco["eventos"]
        self.assertIn("m1-1", eventos)
        self.assertNotIn("outra.m1-1", eventos)  # o mesmo e-mail nas duas contas: o mesmo compromisso
        self.assertIn("outra.m1-1", banco["repetidos"])
        self.assertIn("outra.m9-1", eventos)
        self.assertEqual(eventos["outra.m9-1"]["conta"], "outra")
        self.assertEqual(eventos["outra.m9-1"]["link"], "https://mail.google.com/mail/u/?authuser=b@gmail.com#all/m9")
        self.assertTrue((self.pasta / "coleta-outra.json").is_file())

    def test_texto_puro_com_tags_html_sai_limpo(self):
        """Caso real: o text/plain da confirmação de inscrição trazia um <a href=...> cru."""
        self.gmail = GmailFalso([mensagem(
            "h1", "Faccat <noreply@faccat.br>", "Confirmação de inscrição",
            "A palestra é dia 12/11 às 19h. <a href='https://calendar.google.com/x?dates=1'>Adicionar</a> &amp; mais.")])
        coletar(self.cfg, self.gmail, AGORA)
        descricao = self.banco()["eventos"]["h1-1"]["descricao"]
        self.assertNotIn("<a", descricao)
        self.assertNotIn("href", descricao)

    def test_mesmo_remetente_dia_e_hora_entra_uma_vez(self):
        """O convite e o ingresso do mesmo evento: dois e-mails, um compromisso, um aviso."""
        self.gmail = GmailFalso([
            mensagem("c1", "Eventos <contato@eventos.com>", "Seu ingresso para o Summit", "O evento será dia 05/11/2026 às 08:30."),
            mensagem("c2", "Eventos <contato@eventos.com>", "Pedido confirmado", "O evento será dia 05/11/2026 às 08:30."),
            mensagem("c3", "Eventos <contato@eventos.com>", "Outro dia", "O evento será dia 06/11/2026 às 08:30."),
            mensagem("c4", "Outra <x@outra.com>", "Mesma hora, outro remetente", "O evento será dia 05/11/2026 às 08:30."),
        ])
        r = coletar(self.cfg, self.gmail, AGORA)
        banco = self.banco()
        self.assertEqual(sorted(banco["eventos"]), ["c1-1", "c3-1", "c4-1"])
        self.assertEqual((r["eventos"], r["repetidos"], banco["repetidos"]), (3, 1, ["c2-1"]))

    def test_eventos_json_antigo_com_repetidos_e_arrumado(self):
        coletar(self.cfg, self.gmail, AGORA)
        banco = self.banco()
        copia = dict(banco["eventos"]["m1-1"], id="velho-1", recebido="2026-11-01T10:00:00-03:00", evento_agenda="ev-9")
        banco["eventos"]["velho-1"] = copia
        banco["revisar"]["duvida-1"] = dict(copia, id="duvida-1", evento_agenda=None)
        (self.pasta / "eventos.json").write_text(json.dumps(banco))
        self.assertEqual(coletar(self.cfg, self.gmail, AGORA)["repetidos"], 2)
        banco = self.banco()
        self.assertIn("velho-1", banco["eventos"])  # fica o que já está no Google
        self.assertNotIn("m1-1", banco["eventos"])
        self.assertNotIn("duvida-1", banco["revisar"])  # a dúvida sobre o que já está na agenda sai
        self.assertEqual(banco.get("apagar_no_google", []), [])  # o m1 não tinha ido para o Google

    def test_compromisso_removido_nao_volta_por_outro_email(self):
        coletar(self.cfg, self.gmail, AGORA)
        banco = self.banco()
        banco["eventos"].pop("m1-1")
        banco["chaves_fora"] = [["secretaria@faculdade.edu.br", "2026-11-12", "19:00"]]
        (self.pasta / "eventos.json").write_text(json.dumps(banco))
        self.gmail.mensagens["m5"] = mensagem("m5", "Secretaria <secretaria@faculdade.edu.br>", "Lembrete",
                                              "Lembrete: prova dia 12/11, às 19h.")
        coletar(self.cfg, self.gmail, AGORA)
        self.assertNotIn("m5-1", self.banco()["eventos"])

    def test_proximos(self):
        coletar(self.cfg, self.gmail, AGORA)
        datas = [e["data"] for e in proximos(self.cfg, 10, AGORA)]
        self.assertEqual(datas, ["2026-11-12"])  # a entrevista (18/11) e a promoção (30/11) passam de 10 dias


class TestBloqueados(unittest.TestCase):
    def test_endereco_dominio_e_subdominio(self):
        b = {"enderecos": ["fulano@x.com"], "dominios": ["loja.com"]}
        self.assertTrue(bloqueado("Fulano@X.com", b))
        self.assertTrue(bloqueado("a@loja.com", b))
        self.assertTrue(bloqueado("a@news.loja.com", b))
        self.assertFalse(bloqueado("a@minhaloja.com", b))

    def test_bloquear_cria_o_arquivo_e_nao_repete(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "bloqueados.json"
            self.assertIn("domínio", bloquear(arquivo, "@Loja.com"))
            self.assertIn("já estava", bloquear(arquivo, "loja.com"))
            self.assertIn("endereço", bloquear(arquivo, "chato@x.com"))
            self.assertEqual(ler_bloqueados(arquivo), {"enderecos": ["chato@x.com"], "dominios": ["loja.com"]})

    def test_consulta(self):
        q = consulta("-category:promotions", {"enderecos": ["a@x.com"], "dominios": ["y.com"]}, AGORA)
        self.assertEqual(q, f"after:{int(AGORA.timestamp())} -category:promotions -from:a@x.com -from:y.com")


class TestLimite(unittest.TestCase):
    def erro(self, status: int, motivo: str = ""):
        from googleapiclient.errors import HttpError
        from httplib2 import Response
        return HttpError(Response({"status": status}), motivo.encode())

    def pedido(self, *resultados):
        fila = list(resultados)

        class Pedido:
            def execute(self):
                r = fila.pop(0)
                if isinstance(r, Exception):
                    raise r
                return r
        return Pedido()

    def test_espera_e_tenta_de_novo_no_limite_por_minuto(self):
        esperas = []
        pedido = self.pedido(self.erro(403, "rateLimitExceeded"), self.erro(429), {"ok": True})
        self.assertEqual(executar(pedido, esperas.append), {"ok": True})
        self.assertEqual(esperas, [2, 5])

    def test_outro_403_nao_espera(self):
        with self.assertRaises(Exception):
            executar(self.pedido(self.erro(403, "insufficientPermissions")), lambda s: self.fail("esperou"))


class TestTitulo(unittest.TestCase):
    def test_tira_re_fwd_e_etiqueta(self):
        self.assertEqual(titulo("RE: Fwd: [Faculdade] Prova remarcada"), "Prova remarcada")
        self.assertEqual(titulo(""), "(sem assunto)")


if __name__ == "__main__":
    unittest.main()
