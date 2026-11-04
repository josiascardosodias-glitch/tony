"""Testes de código do que não depende do modelo: notas, calendário, ferramentas, log, conversa e timer.

    uv run python -m unittest discover testes
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tony import config
from tony.cliente import Chamada, ErroDoModelo
from tony.conversa import Conversa, calendario
from tony.dia import unidades
from tony.ferramentas import ErroDaFerramenta, executar
from tony.memoria import ler_inteligencia, limpar_nota
from tony.registro import Registro
from tony.testes import carregar_falas


class ClienteFalso:
    """Responde o que estiver na fila; um item `Exception` é levantado no lugar da resposta."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)

    def conversar(self, mensagens, ferramentas):
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        yield from resposta

    def completar(self, mensagens):
        return "resumo do começo"


def pasta_temporaria(teste: unittest.TestCase) -> Path:
    pasta = tempfile.TemporaryDirectory()
    teste.addCleanup(pasta.cleanup)
    return Path(pasta.name)


class TestNotas(unittest.TestCase):
    def test_limpar_nota_tira_frontmatter_e_callouts(self):
        nota = "---\ntags: [x]\n---\n\n> [!info] Mapa\n\n# Sobre\n\n- estuda C\n"
        self.assertEqual(limpar_nota(nota), "# Sobre\n\n- estuda C")

    def test_inteligencia_ignora_os_modelos_vazios(self):
        pasta = pasta_temporaria(self)
        (pasta / "Tony - Sobre mim.md").write_text("# Sobre\n\n- real", encoding="utf-8")
        (pasta / "modelos").mkdir()
        (pasta / "modelos" / "Tony - Sobre mim (modelo).md").write_text("- Nome:", encoding="utf-8")
        self.assertEqual(ler_inteligencia(pasta), "# Sobre\n\n- real")

    def test_sem_pasta_nao_quebra(self):
        self.assertEqual(ler_inteligencia(None), "")
        self.assertEqual(ler_inteligencia(Path("/nao/existe")), "")


class TestCalendario(unittest.TestCase):
    def test_dias_com_o_dia_da_semana(self):
        linhas = calendario(datetime(2026, 11, 2), 3).splitlines()  # 02/11/2026 é segunda
        self.assertEqual(linhas, ["segunda-feira, 02/11/2026", "terça-feira, 03/11/2026", "quarta-feira, 04/11/2026"])


class TestFerramentas(unittest.TestCase):
    def setUp(self):
        def somar(a: int, b: int = 0) -> str:
            """Soma."""
            if a < 0:
                raise ErroDaFerramenta("só positivos")
            return str(a + b)
        self.ferramentas = {"somar": somar}

    def test_chamada_certa(self):
        self.assertEqual(executar(self.ferramentas, "somar", {"a": 2, "b": 3}), "5")

    def test_ferramenta_que_nao_existe_volta_como_erro(self):
        self.assertIn("não existe a ferramenta 'sumir'", executar(self.ferramentas, "sumir", {}))

    def test_argumento_faltando_ou_sobrando(self):
        self.assertIn("faltando: ['a']", executar(self.ferramentas, "somar", {"c": 1}))

    def test_erro_da_ferramenta_vai_para_o_modelo(self):
        self.assertEqual(executar(self.ferramentas, "somar", {"a": -1}), "erro: só positivos")


class TestRegistro(unittest.TestCase):
    def test_marcar_so_depois_de_um_turno(self):
        registro = Registro(pasta_temporaria(self), modelo="falso")
        self.assertFalse(registro.marcar("bom"))
        registro.turno_completo("oi", "Oi!", 0.5)
        self.assertTrue(registro.marcar("ruim", "seco demais"))
        eventos = [json.loads(l) for l in registro.arquivo.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["tipo"] for e in eventos], ["inicio", "turno", "marca"])
        self.assertEqual(eventos[-1]["motivo"], "seco demais")


class TestConversa(unittest.TestCase):
    def nova(self, *respostas, limite=8192):
        return Conversa(ClienteFalso(*respostas), limite, "# Quem você é", "- estuda C")

    def test_prompt_tem_personalidade_data_e_inteligencia(self):
        prompt = self.nova().prompt_de_sistema()
        self.assertIn("# Quem você é", prompt)
        self.assertIn("# Agora", prompt)
        self.assertIn("- estuda C", prompt)

    def test_resposta_entra_no_historico(self):
        conversa = self.nova(["Oi", "!"])
        self.assertEqual("".join(conversa.responder("oi")), "Oi!")
        self.assertEqual(conversa.mensagens[-1], {"role": "assistant", "content": "Oi!"})

    def test_erro_no_meio_desfaz_a_fala(self):
        conversa = self.nova(ErroDoModelo("sem rede"))
        with self.assertRaises(ErroDoModelo):
            list(conversa.responder("oi"))
        self.assertEqual(conversa.mensagens, [])

    def test_ferramenta_roda_e_o_resultado_volta_ao_modelo(self):
        conversa = self.nova([Chamada("eco", {"texto": "x"})], ["pronto"])
        conversa.ferramentas = {"eco": lambda texto: f"eco: {texto}"}
        list(conversa.responder("repete x"))
        self.assertIn({"role": "tool", "content": "eco: x", "tool_name": "eco"}, conversa.mensagens)

    def test_contexto_cheio_resume_o_comeco(self):
        conversa = self.nova(["a" * 400], ["b" * 400], ["c" * 400], limite=300)
        for fala in ("um", "dois", "tres"):
            list(conversa.responder(fala))
        self.assertEqual(conversa.resumo, "resumo do começo")
        self.assertEqual(conversa.mensagens[0], {"role": "user", "content": "dois"})


class TestTimer(unittest.TestCase):
    def test_falha_em_todas_as_tentativas_avisa(self):
        arquivos = unidades("08:00", Path("/x/tony-producao"), "/usr/bin/uv")
        servico = arquivos["tony-dia.service"]
        self.assertIn("OnFailure=tony-dia-falhou.service", servico)
        self.assertIn("Restart=on-failure", servico)
        self.assertIn("WorkingDirectory=/x/tony-producao", servico)
        self.assertIn("notify-send", arquivos["tony-dia-falhou.service"])
        self.assertIn("OnCalendar=*-*-* 08:00:00", arquivos["tony-dia.timer"])
        self.assertIn("ExecStart=/usr/bin/uv run tony telegram", arquivos["tony-telegram.service"])
        self.assertIn("Restart=always", arquivos["tony-telegram.service"])


class TestResumoDoDia(unittest.TestCase):
    def test_hoje_proximos_e_revisar_sem_modelo(self):
        from tony.dia import resumo_do_dia
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "eventos.json"
            ev = lambda data, titulo, hora=None: {"data": data, "hora": hora, "titulo": titulo, "descricao": "frase"}
            arquivo.write_text(json.dumps({"eventos": {"a": ev("2026-11-03", "Consulta", "16:00"),
                                                       "b": ev("2026-11-05", "Summit", "08:30"),
                                                       "c": ev("2026-11-20", "Longe")},
                                           "revisar": {"r": ev("2026-11-06", "Talvez")}}))
            cfg = config.carregar()
            cfg["coleta"] = {**cfg["coleta"], "eventos": str(arquivo)}
            texto = resumo_do_dia(cfg, datetime(2026, 11, 3).date())
        self.assertTrue(texto.startswith("Hoje:\n• hoje, 16:00 — Consulta"))
        self.assertIn("Nos próximos 7 dias:\n• qui 05/11, 08:30 — Summit", texto)
        self.assertNotIn("Longe", texto)
        self.assertIn("1 data(s) esperando você decidir", texto)

    def test_nada(self):
        from tony.dia import resumo_do_dia
        cfg = config.carregar()
        cfg["coleta"] = {**cfg["coleta"], "eventos": "/nao/existe.json"}
        self.assertEqual(resumo_do_dia(cfg, datetime(2026, 11, 3).date()),
                         "Nada marcado para hoje nem para os próximos 7 dias.")


class TestFalas(unittest.TestCase):
    def test_toda_fala_tem_id_unico_e_algo_para_conferir(self):
        falas = carregar_falas(config.RAIZ / "testes/falas.yaml", [])
        ids = [f["id"] for f in falas]
        self.assertEqual(len(ids), len(set(ids)))
        for fala in falas:
            self.assertTrue("espera" in fala or "chama" in fala, fala["id"])
            self.assertIn("fala", fala, fala["id"])


if __name__ == "__main__":
    unittest.main()
