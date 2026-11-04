"""Testes de código da agenda: uma API do Google Agenda falsa, em memória.

    uv run python -m unittest discover testes
"""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tony import config
from tony.agenda import corpo, decidir, id_da_agenda, remover, sincronizar

HOJE = date(2026, 11, 3)


class Executar:
    def __init__(self, resposta):
        self.resposta = resposta

    def execute(self):
        return self.resposta


class AgendaFalsa:
    """Imita calendars().insert e events().list/insert com listas em memória."""

    def __init__(self):
        self.agendas: list[dict] = []
        self.eventos: list[dict] = []

    def calendars(self):
        return self

    def events(self):
        return self

    def insert(self, body, calendarId=None):
        if calendarId is None:  # calendars().insert
            nova = {"id": f"agenda-{len(self.agendas) + 1}", **body}
            self.agendas.append(nova)
            return Executar(nova)
        novo = {"id": f"ev-{len(self.eventos) + 1}", "calendarId": calendarId, **body}
        self.eventos.append(novo)
        return Executar(novo)

    def delete(self, calendarId, eventId):
        antes = len(self.eventos)
        self.eventos = [e for e in self.eventos if e["id"] != eventId]
        if len(self.eventos) == antes:  # como a API: evento que não existe é 404
            from googleapiclient.errors import HttpError
            from httplib2 import Response
            return Executar404(HttpError(Response({"status": 404}), b"not found"))
        return Executar({})

    def list(self, calendarId, privateExtendedProperty, maxResults=1, showDeleted=False):
        tony_id = privateExtendedProperty.split("=", 1)[1]
        achados = [e for e in self.eventos if e["calendarId"] == calendarId
                   and e["extendedProperties"]["private"]["tony_id"] == tony_id]
        return Executar({"items": achados[:maxResults]})


class Executar404:
    def __init__(self, erro):
        self.erro = erro

    def execute(self):
        raise self.erro


def evento(id_: str, data: str, hora: str | None = "19:00", remetente: str = "secretaria@faculdade.edu.br") -> dict:
    return {"id": id_, "email": id_.split("-")[0], "conta": "pessoal", "remetente": remetente, "nome": "Secretaria",
            "titulo": "Prova remarcada", "data": data, "hora": hora, "descricao": "A prova foi remarcada.",
            "origem": "corpo", "confianca": 0.9, "link": f"https://mail.google.com/mail/u/0/#all/{id_}",
            "recebido": "2026-11-03T10:00:00-03:00", "criado_em": "2026-11-03T10:00:00", "evento_agenda": None}


class TestAgenda(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.cfg = config.carregar()
        self.cfg["coleta"] = {**self.cfg["coleta"], "eventos": str(self.pasta / "eventos.json")}
        self.cfg["agenda"] = {"arquivo": str(self.pasta / "agenda.json")}
        self.google = AgendaFalsa()

    def gravar(self, eventos: dict, revisar: dict | None = None):
        (self.pasta / "eventos.json").write_text(json.dumps({"eventos": eventos, "revisar": revisar or {}}))

    def banco(self) -> dict:
        return json.loads((self.pasta / "eventos.json").read_text())

    def test_cria_a_agenda_uma_vez_e_guarda_o_id(self):
        self.assertEqual(id_da_agenda(self.cfg, self.google), "agenda-1")
        self.assertEqual(id_da_agenda(self.cfg, self.google), "agenda-1")
        self.assertEqual(len(self.google.agendas), 1)
        self.assertEqual(self.google.agendas[0]["summary"], "Tony")

    def test_cria_os_eventos_e_nao_duplica_na_segunda_vez(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12"), "m2-1": evento("m2-1", "2026-11-20", None)})
        self.assertEqual(sincronizar(self.cfg, self.google, HOJE), {"criados": 2, "repetidos": 0, "ja_estavam": 0})
        self.assertEqual(sincronizar(self.cfg, self.google, HOJE), {"criados": 0, "repetidos": 0, "ja_estavam": 0})
        self.assertEqual(len(self.google.eventos), 2)
        self.assertEqual(self.banco()["eventos"]["m1-1"]["evento_agenda"], "ev-1")

    def test_eventos_json_perdido_acha_o_que_ja_estava_no_google(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12")})
        sincronizar(self.cfg, self.google, HOJE)
        self.gravar({"m1-1": evento("m1-1", "2026-11-12")})  # como se o evento_agenda tivesse sumido
        self.assertEqual(sincronizar(self.cfg, self.google, HOJE)["ja_estavam"], 1)
        self.assertEqual(len(self.google.eventos), 1)

    def test_dois_emails_do_mesmo_compromisso_viram_um_evento(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12"), "m2-1": evento("m2-1", "2026-11-12")})
        self.assertEqual(sincronizar(self.cfg, self.google, HOJE), {"criados": 1, "repetidos": 1, "ja_estavam": 0})
        self.assertEqual((list(self.banco()["eventos"]), self.banco()["repetidos"]), (["m1-1"], ["m2-1"]))

    def test_repetido_que_ja_estava_no_google_sozinho_e_apagado_la(self):
        self.gravar({"m1-1": dict(evento("m1-1", "2026-11-12"), evento_agenda="ev-a"),
                     "m2-1": dict(evento("m2-1", "2026-11-12"), evento_agenda="ev-b")})
        self.google.eventos += [{"id": "ev-a"}, {"id": "ev-b"}]
        sincronizar(self.cfg, self.google, HOJE)
        self.assertEqual([e["id"] for e in self.google.eventos], ["ev-a"])
        self.assertEqual(self.banco()["apagar_no_google"], [])

    def test_aceitar_o_que_ja_esta_na_agenda_por_outro_email(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12")}, {"r1-1": evento("r1-1", "2026-11-12")})
        self.assertIn("já estava na agenda", decidir(self.cfg, "r1-1", True))
        self.assertEqual(list(self.banco()["eventos"]), ["m1-1"])

    def test_passado_nao_vai(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-01")})
        self.assertEqual(sincronizar(self.cfg, self.google, HOJE)["criados"], 0)

    def test_com_hora_e_dia_inteiro(self):
        com_hora = corpo(evento("m1-1", "2026-11-12", "19:00"))
        self.assertEqual(com_hora["start"], {"dateTime": "2026-11-12T19:00:00", "timeZone": "America/Sao_Paulo"})
        self.assertEqual(com_hora["end"]["dateTime"], "2026-11-12T20:00:00")
        self.assertIn("https://mail.google.com/mail/u/0/#all/m1-1", com_hora["description"])
        dia = corpo(evento("m1-1", "2026-11-12", None))
        self.assertEqual((dia["start"], dia["end"]), ({"date": "2026-11-12"}, {"date": "2026-11-13"}))

    def test_remover_apaga_no_google_e_leva_o_repetido_junto(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12"), "m2-1": evento("m2-1", "2026-11-12"),
                     "m3-1": evento("m3-1", "2026-11-20")})
        self.assertIn("e mais 1 e-mail(s)", remover(self.cfg, self.google, "m2-1"))  # antes de sincronizar
        sincronizar(self.cfg, self.google, HOJE)
        banco = self.banco()
        self.assertEqual((list(banco["eventos"]), sorted(banco["removidos"])), (["m3-1"], ["m1-1", "m2-1"]))
        self.assertEqual(banco["chaves_fora"], [["secretaria@faculdade.edu.br", "2026-11-12", "19:00"]])
        self.assertEqual(len(self.google.eventos), 1)

    def test_remover_depois_de_sincronizar_apaga_no_google(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12"), "m3-1": evento("m3-1", "2026-11-20")})
        sincronizar(self.cfg, self.google, HOJE)
        self.assertIn("removido", remover(self.cfg, self.google, "m1-1"))
        self.assertEqual([e["id"] for e in self.google.eventos], ["ev-2"])

    def test_remover_o_que_ja_foi_apagado_a_mao_nao_quebra(self):
        self.gravar({"m1-1": evento("m1-1", "2026-11-12")})
        sincronizar(self.cfg, self.google, HOJE)
        self.google.eventos.clear()
        self.assertIn("removido", remover(self.cfg, self.google, "m1-1"))

    def test_remover_o_que_nao_existe(self):
        self.gravar({})
        self.assertIn("não há", remover(self.cfg, self.google, "x-1"))

    def test_aceitar_e_descartar(self):
        self.gravar({}, {"r1-1": evento("r1-1", "2026-11-05"), "r2-1": evento("r2-1", "2026-11-06")})
        self.assertIn("aceito", decidir(self.cfg, "r1-1", True))
        self.assertIn("descartado", decidir(self.cfg, "r2-1", False))
        self.assertIn("não há", decidir(self.cfg, "r9-9", True))
        banco = self.banco()
        self.assertEqual((list(banco["eventos"]), banco["revisar"], banco["descartados"]), (["r1-1"], {}, ["r2-1"]))


if __name__ == "__main__":
    unittest.main()
