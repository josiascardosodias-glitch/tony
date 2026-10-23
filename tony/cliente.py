"""Conversa com o modelo de linguagem.

É o único arquivo que sabe que o Ollama existe. Para trocar de provedor, reescreva só este
arquivo mantendo os dois métodos públicos: `conversar` (em pedaços) e `completar` (de uma vez).
"""

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
    def __init__(self, cfg: dict):
        self.modelo = cfg["modelo"]
        self._ollama = Client(host=cfg["ollama"]["host"])
        self._keep_alive = cfg["ollama"]["keep_alive"]
        self._pensar = cfg["geracao"]["pensar"]
        self._opcoes = {
            "temperature": cfg["geracao"]["temperatura"],
            "num_ctx": cfg["contexto"]["num_ctx"],
        }

    def _chat(self, mensagens: list[dict], stream: bool):
        return self._ollama.chat(
            model=self.modelo,
            messages=mensagens,
            stream=stream,
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
