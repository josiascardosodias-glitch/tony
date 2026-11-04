"""Testes de código da conta Faccat: um App da Web falso no lugar do Apps Script.

    uv run python -m unittest discover testes
"""

import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import httpx

from tony import config
from tony.coleta import coletar
from tony.faccat import ErroDaFaccat, FonteAppsScript, configurar

AGORA = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc).astimezone()
URL = "https://script.google.com/macros/s/ABC/exec"

RESPOSTA = {
    "conta": "aluno@sou.faccat.br",
    "prazos": [{"id": "111", "turma": "Algoritmos", "titulo": "Lista 3", "prazo": "2026-11-10", "hora": "23:59",
                "descricao": "Entregar pelo Classroom.", "link": "https://classroom.google.com/x"},
               {"id": "222", "turma": "Algoritmos", "titulo": "Antiga", "prazo": "2026-10-01", "hora": None}],
    "emails": [{"id": "e1", "de": "Coordenação <coord@faccat.br>", "assunto": "Semana acadêmica",
                "data": int(AGORA.timestamp() * 1000), "texto": "A semana acadêmica começa dia 17/11 às 19h.",
                "em_massa": False, "convites": []}],
}


class TestFaccat(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.conta = {"nome": "faccat", "tipo": "apps-script", "arquivo": str(self.pasta / "faccat.env")}
        self.cfg = config.carregar()
        self.cfg["coleta"] = {**self.cfg["coleta"], "eventos": str(self.pasta / "eventos.json"),
                              "estado": str(self.pasta / "coleta.json"), "bloqueados": str(self.pasta / "b.json"),
                              "contas": [{"nome": "pessoal", "email": ""}, self.conta]}
        self.pedidos: list[httpx.Request] = []

    def fonte(self, resposta=RESPOSTA) -> FonteAppsScript:
        configurar(self.conta, URL)

        def responder(request):
            self.pedidos.append(request)
            return httpx.Response(200, json=resposta)
        return FonteAppsScript(self.conta, httpx.Client(transport=httpx.MockTransport(responder)))

    def test_configurar_cria_chave_guarda_url_e_protege_o_arquivo(self):
        primeira = configurar(self.conta, None)
        self.assertIn("TONY_CHAVE", primeira)
        configurar(self.conta, URL)
        texto = (self.pasta / "faccat.env").read_text()
        self.assertIn(f"TONY_FACCAT_URL={URL}", texto)
        self.assertEqual(stat.S_IMODE((self.pasta / "faccat.env").stat().st_mode), 0o600)
        with self.assertRaises(SystemExit):
            configurar(self.conta, "https://outro.site/exec")

    def test_prazos_viram_eventos_e_emails_passam_pelo_extrator(self):
        r = coletar(self.cfg, self.fonte(), AGORA, self.conta)
        eventos = json.loads((self.pasta / "eventos.json").read_text())["eventos"]
        lista = eventos["faccat.classroom.111"]
        self.assertEqual((lista["titulo"], lista["data"], lista["hora"], lista["confianca"]),
                         ("[Algoritmos] Lista 3", "2026-11-10", "23:59", 1.0))
        self.assertNotIn("faccat.classroom.222", eventos)  # prazo que já passou
        self.assertEqual(eventos["faccat.e1-1"]["data"], "2026-11-17")
        self.assertEqual(r["emails"], 1)

    def test_prazo_removido_nao_volta_na_coleta(self):
        coletar(self.cfg, self.fonte(), AGORA, self.conta)
        arquivo = self.pasta / "eventos.json"
        banco = json.loads(arquivo.read_text())
        banco["eventos"].pop("faccat.classroom.111")
        banco["removidos"] = ["faccat.classroom.111"]
        arquivo.write_text(json.dumps(banco))
        coletar(self.cfg, self.fonte(), AGORA, self.conta)
        self.assertNotIn("faccat.classroom.111", json.loads(arquivo.read_text())["eventos"])

    def test_uma_chamada_por_coleta_com_chave_desde_e_filtro(self):
        coletar(self.cfg, self.fonte(), AGORA, self.conta)
        self.assertEqual(len(self.pedidos), 1)
        params = self.pedidos[0].url.params
        self.assertEqual(params["desde"], str(int(AGORA.timestamp()) - 30 * 86400))
        self.assertIn("-category:promotions", params["filtro"])
        self.assertNotIn("after:", params["filtro"])  # o desde já diz isso
        self.assertTrue(params["chave"])

    def test_chave_recusada(self):
        with self.assertRaises(ErroDaFaccat) as erro:
            coletar(self.cfg, self.fonte({"erro": "chave inválida"}), AGORA, self.conta)
        self.assertIn("chave inválida", str(erro.exception))

    def test_sem_configuracao(self):
        with self.assertRaises(ErroDaFaccat):
            FonteAppsScript(self.conta)

    def test_erro_de_rede_nao_mostra_url_nem_chave(self):
        configurar(self.conta, URL)
        falha = lambda request: (_ for _ in ()).throw(httpx.ConnectError(f"falhou {request.url}"))
        fonte = FonteAppsScript(self.conta, httpx.Client(transport=httpx.MockTransport(falha)))
        with self.assertRaises(ErroDaFaccat) as erro:
            coletar(self.cfg, fonte, AGORA, self.conta)
        self.assertNotIn("script.google.com", str(erro.exception))


if __name__ == "__main__":
    unittest.main()
