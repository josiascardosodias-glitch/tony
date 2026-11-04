"""Testes de código do bot do Telegram: Telegram, Gmail, Agenda e modelo falsos, sem rede.

O mais importante: pergunta de agenda não chama o modelo, e mensagem de outro chat é ignorada.

    uv run python -m unittest discover testes
"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import httpx

from tony import config, google
from tony.telegram import Bot, ErroDoTelegram, Telegram

AGORA = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc).astimezone()
MEU_CHAT = 7000


class TelegramFalso:
    chat_id = MEU_CHAT

    def __init__(self):
        self.enviadas: list[dict] = []
        self.chamadas: list[tuple] = []

    def enviar(self, texto, botoes=None):
        self.enviadas.append({"texto": texto, "botoes": botoes})

    def chamar(self, metodo, **dados):
        self.chamadas.append((metodo, dados))
        return []


class ModeloFalso:
    def __init__(self):
        self.chamadas = 0

    def conversar(self, mensagens, ferramentas):
        self.chamadas += 1
        self.prompt = mensagens[0]["content"]
        yield "Resposta do modelo."


def evento(id_: str, data: str, titulo: str, hora: str | None = None) -> dict:
    return {"id": id_, "email": id_[:2], "conta": "pessoal", "remetente": "x@y.com", "nome": "", "titulo": titulo,
            "data": data, "hora": hora, "descricao": f"{titulo}, frase do e-mail.", "origem": "corpo",
            "confianca": 0.9, "link": "", "recebido": "", "criado_em": "", "evento_agenda": None}


def mensagem(texto: str, chat: int = MEU_CHAT, n: int = 1) -> dict:
    return {"update_id": n, "message": {"chat": {"id": chat}, "text": texto}}


class TestBot(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.cfg = config.carregar()
        self.cfg["coleta"] = {**self.cfg["coleta"], "eventos": str(self.pasta / "eventos.json"),
                              "estado": str(self.pasta / "coleta.json"), "contas": [{"nome": "pessoal", "email": ""}]}
        self.cfg["telegram"] = {**self.cfg["telegram"], "estado": str(self.pasta / "telegram.json")}
        self.cfg["logs"] = str(self.pasta / "logs")
        self.cfg["memoria"] = {"inteligencia": ""}
        self.gravar({"m1-1": evento("m1-1", "2026-11-05", "Oktober Summit", "08:30")},
                    {"r1-1": evento("r1-1", "2026-11-10", "Talvez reunião")})
        self.telegram = TelegramFalso()
        self.modelo = ModeloFalso()
        self.bot = Bot(self.cfg, self.telegram, cliente=self.modelo)

    def gravar(self, eventos, revisar):
        (self.pasta / "eventos.json").write_text(json.dumps({"eventos": eventos, "revisar": revisar}))

    def test_pergunta_de_agenda_nao_gasta_token(self):
        self.bot.tratar(mensagem("o que eu tenho quinta?"), AGORA)
        self.assertEqual(self.modelo.chamadas, 0)
        self.assertIn("Oktober Summit", self.telegram.enviadas[0]["texto"])

    def test_conversa_livre_vai_ao_modelo_com_a_agenda(self):
        self.bot.tratar(mensagem("me explica o que é uma closure"), AGORA)
        self.assertEqual(self.modelo.chamadas, 1)
        self.assertIn("Oktober Summit", self.modelo.prompt)
        self.assertNotIn("Talvez reunião", self.modelo.prompt)  # revisar não é agenda
        self.assertEqual(self.telegram.enviadas[0]["texto"], "Resposta do modelo.")

    def test_outro_chat_e_ignorado(self):
        self.bot.tratar(mensagem("o que eu tenho quinta?", chat=666), AGORA)
        self.bot.tratar(mensagem("me conta um segredo", chat=666), AGORA)
        self.assertEqual(self.telegram.enviadas, [])
        self.assertEqual(self.modelo.chamadas, 0)

    def test_revisar_chega_com_botoes_uma_vez(self):
        self.bot.avisar_revisar()
        self.bot.avisar_revisar()
        self.assertEqual(len(self.telegram.enviadas), 1)
        self.assertEqual(self.telegram.enviadas[0]["botoes"][0][0]["callback_data"], "aceitar:r1-1")

    def test_muitas_datas_de_uma_vez_viram_uma_mensagem(self):
        self.gravar({}, {f"r{n}-1": evento(f"r{n}-1", "2026-11-10", f"Promo {n}") for n in range(5)})
        self.bot.avisar_revisar()
        self.assertEqual(len(self.telegram.enviadas), 1)
        self.assertIn("5 datas", self.telegram.enviadas[0]["texto"])
        self.bot.responder("/revisar", AGORA)  # aí sim, uma por uma, com botões
        self.assertEqual(len(self.telegram.enviadas), 6)

    def test_botao_descartar(self):
        clique = {"id": "c1", "data": "descartar:r1-1", "message": {"chat": {"id": MEU_CHAT}, "message_id": 9, "text": "?"}}
        self.bot.tratar({"update_id": 2, "callback_query": clique}, AGORA)
        banco = json.loads((self.pasta / "eventos.json").read_text())
        self.assertEqual((banco["revisar"], banco["descartados"]), ({}, ["r1-1"]))
        self.assertEqual([m for m, _ in self.telegram.chamadas], ["answerCallbackQuery", "editMessageText"])

    def clicar(self, dados: str, n: int = 2):
        clique = {"id": f"c{n}", "data": dados, "message": {"chat": {"id": MEU_CHAT}, "message_id": 9, "text": "?"}}
        self.bot.tratar({"update_id": n, "callback_query": clique}, AGORA)

    def test_remover_pede_confirmacao_e_tira_da_agenda(self):
        self.apagados = []
        self.bot.agenda = lambda: AgendaQueApaga(self.apagados)
        (self.pasta / "agenda.json").write_text(json.dumps({"id": "agenda-1"}))
        self.cfg["agenda"] = {**self.cfg["agenda"], "arquivo": str(self.pasta / "agenda.json")}
        self.gravar({"m1-1": dict(evento("m1-1", "2026-11-05", "Oktober Summit", "08:30"), evento_agenda="ev-1")}, {})
        self.assertEqual(self.bot.responder("/remover", AGORA), "")
        lista = self.telegram.enviadas[-1]
        self.assertEqual(lista["botoes"][0][0]["callback_data"], "remover:m1-1")
        self.assertIn("Oktober Summit", lista["botoes"][0][0]["text"])
        self.clicar("remover:m1-1")
        confirmar = self.telegram.enviadas[-1]
        self.assertIn("Tiro da agenda?", confirmar["texto"])
        self.assertIn("m1-1", json.loads((self.pasta / "eventos.json").read_text())["eventos"])  # ainda não saiu
        self.assertEqual([b["callback_data"] for b in confirmar["botoes"][0]], ["tirar:m1-1", "deixar:m1-1"])
        self.clicar("tirar:m1-1", 3)
        banco = json.loads((self.pasta / "eventos.json").read_text())
        self.assertEqual((banco["eventos"], banco["removidos"], self.apagados), ({}, ["m1-1"], ["ev-1"]))
        self.assertIn("removido", self.telegram.chamadas[-1][1]["text"])

    def test_deixar_nao_remove(self):
        self.clicar("deixar:m1-1")
        self.assertIn("m1-1", json.loads((self.pasta / "eventos.json").read_text())["eventos"])
        self.assertIn("ficou na agenda", self.telegram.chamadas[-1][1]["text"])

    def test_remover_sem_nada_na_agenda(self):
        self.gravar({}, {})
        self.assertIn("nenhum compromisso", self.bot.responder("/remover", AGORA))

    def test_aceitar_deixa_o_botao_de_remover(self):
        self.bot.agenda = lambda: None
        import tony.telegram as modulo
        original = modulo.sincronizar
        modulo.sincronizar = lambda cfg, servico: {}
        self.addCleanup(setattr, modulo, "sincronizar", original)
        self.clicar("aceitar:r1-1")
        editada = self.telegram.chamadas[-1][1]
        self.assertEqual(editada["reply_markup"]["inline_keyboard"][0][0]["callback_data"], "remover:r1-1")

    def test_botao_de_outro_chat_nao_faz_nada(self):
        clique = {"id": "c1", "data": "aceitar:r1-1", "message": {"chat": {"id": 666}, "message_id": 9}}
        self.bot.tratar({"update_id": 2, "callback_query": clique}, AGORA)
        self.assertIn("r1-1", json.loads((self.pasta / "eventos.json").read_text())["revisar"])

    def test_autorizacao_vencida_avisa_uma_vez_por_dia(self):
        def vencida(conta=None):
            raise google.AutorizacaoVencida("a autorização do Google venceu: rode `uv run tony autorizar`")
        self.bot.fonte = vencida
        self.bot.agenda = vencida  # nunca a API de verdade num teste
        self.bot.rodar_coleta(AGORA)
        self.bot.rodar_coleta(AGORA)
        avisos = [m for m in self.telegram.enviadas if "Não consegui olhar" in m["texto"]]
        self.assertEqual(len(avisos), 1)
        self.assertIn("uv run tony autorizar", avisos[0]["texto"])

    def test_comandos(self):
        self.assertIn("/revisar", self.bot.responder("/ajuda", AGORA))
        self.assertIn("/remover", self.bot.responder("/ajuda", AGORA))
        self.assertIn("Oktober Summit", self.bot.responder("/semana", AGORA))
        self.assertEqual(self.bot.responder("/nova", AGORA), "Conversa nova.")
        self.assertIn("Não conheço", self.bot.responder("/xyz", AGORA))
        self.assertEqual(self.modelo.chamadas, 0)

    def test_hora_de_coletar(self):
        self.assertTrue(self.bot.hora_de_coletar(AGORA))
        self.bot.estado["ultima_coleta"] = AGORA.isoformat()
        self.assertFalse(self.bot.hora_de_coletar(AGORA))


class AgendaQueApaga:
    """Só o que o `remover` usa da API da Agenda."""

    def __init__(self, apagados: list):
        self.apagados = apagados

    def events(self):
        return self

    def delete(self, calendarId, eventId):
        self.apagados.append(eventId)
        return type("Pedido", (), {"execute": lambda _: None})()


class TestTelegram(unittest.TestCase):
    def test_erro_de_rede_nao_mostra_o_token(self):
        def falha(request):
            raise httpx.ConnectError(f"falhou {request.url}")
        telegram = Telegram("123:SEGREDO", MEU_CHAT, httpx.Client(transport=httpx.MockTransport(falha)))
        with self.assertRaises(ErroDoTelegram) as erro:
            telegram.enviar("oi")
        self.assertNotIn("SEGREDO", str(erro.exception))

    def test_resposta_de_erro_da_api(self):
        resposta = lambda request: httpx.Response(200, json={"ok": False, "description": "chat not found"})
        telegram = Telegram("123:SEGREDO", MEU_CHAT, httpx.Client(transport=httpx.MockTransport(resposta)))
        with self.assertRaises(ErroDoTelegram) as erro:
            telegram.enviar("oi")
        self.assertIn("chat not found", str(erro.exception))


if __name__ == "__main__":
    unittest.main()
