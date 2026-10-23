"""Conversa com o modelo de linguagem.

É o único arquivo que sabe que o Ollama existe. Para trocar de provedor, reescreva só este
arquivo mantendo os métodos públicos: `conversar` (em pedaços), `completar` (de uma vez) e
`estruturado` (um dicionário que segue um JSON Schema).
"""

import json
from contextlib import contextmanager

import httpx
from ollama import Client, ResponseError


class ErroDoModelo(Exception):
    """Qualquer falha ao falar com o modelo, já explicada em português."""


@contextmanager
def _traduzir_erros():
    try:
        yield
    except ResponseError as e:
        raise ErroDoModelo(f"o Ollama recusou o pedido: {e.error}") from e
    # Sem streaming a lib converte a falha de rede em ConnectionError; com streaming, o erro do
    # httpx (a biblioteca HTTP por baixo dela) escapa direto. Os dois casos dão a mesma mensagem.
    except (ConnectionError, httpx.TransportError) as e:
        raise ErroDoModelo("não consegui falar com o Ollama. Ele está rodando? (ollama serve)") from e


class Cliente:
    def __init__(self, cfg: dict, modelo: str | None = None, temperatura: float | None = None):
        """`modelo` e `temperatura` trocam os do config (ex.: o juiz dos testes usa outro modelo, com 0)."""
        self.modelo = modelo or cfg["modelo"]
        self._ollama = Client(host=cfg["ollama"]["host"])
        self._keep_alive = cfg["ollama"]["keep_alive"]
        self._pensar = cfg["geracao"]["pensar"]
        self._opcoes = {
            "temperature": cfg["geracao"]["temperatura"] if temperatura is None else temperatura,
            "num_ctx": cfg["contexto"]["num_ctx"],
        }

    def _chat(self, mensagens: list[dict], stream: bool, ferramentas: list[dict] | None = None):
        return self._ollama.chat(
            model=self.modelo,
            messages=mensagens,
            stream=stream,
            tools=ferramentas,
            think=self._pensar,
            options=self._opcoes,
            keep_alive=self._keep_alive,
        )

    def conversar(self, mensagens: list[dict]):
        """Devolve a resposta em pedaços, para o texto aparecer enquanto é escrito."""
        with _traduzir_erros():
            for pedaco in self._chat(mensagens, stream=True):
                if pedaco.message.content:
                    yield pedaco.message.content

    def completar(self, mensagens: list[dict]) -> str:
        """Devolve a resposta inteira de uma vez (usado nos resumos)."""
        with _traduzir_erros():
            return self._chat(mensagens, stream=False).message.content or ""

    def estruturado(self, mensagens: list[dict], esquema: dict) -> dict:
        """Devolve um dicionário com os campos do `esquema` (JSON Schema).

        Os modelos de nuvem do Ollama ignoram o parâmetro `format` (testado em 2026-10-23), então o
        modelo entrega o resultado chamando uma ferramenta `responder` cujos parâmetros são o esquema.
        Se ele responder em texto, ainda tenta ler o texto como JSON.
        """
        ferramenta = {
            "type": "function",
            "function": {
                "name": "responder",
                "description": "Entrega o resultado final. Sempre chame esta função.",
                "parameters": esquema,
            },
        }
        with _traduzir_erros():
            mensagem = self._chat(mensagens, stream=False, ferramentas=[ferramenta]).message
        if mensagem.tool_calls:
            resultado = dict(mensagem.tool_calls[0].function.arguments)
        else:
            try:
                resultado = json.loads(mensagem.content or "")
            except json.JSONDecodeError as e:
                raise ErroDoModelo(f"o modelo não devolveu o resultado no formato pedido: {mensagem.content!r:.200}") from e
        faltando = [c for c in esquema.get("required", []) if c not in resultado]
        if faltando:
            raise ErroDoModelo(f"faltaram campos no resultado do modelo: {', '.join(faltando)}")
        return resultado
