"""Uma conversa: monta o prompt de sistema, guarda o histórico e resume o começo quando o contexto enche."""

from datetime import datetime

from .cliente import Cliente, ErroDoModelo

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

PEDIDO_RESUMO_PARCIAL = (
    "Resuma o trecho de conversa abaixo em poucas linhas, em português, para você mesmo continuar "
    "a conversa depois: assuntos, decisões, o que ficou pendente e o tom. Se houver um resumo "
    "anterior no início, incorpore-o."
)
PEDIDO_RESUMO_FINAL = (
    "A conversa vai terminar. Escreva em até 5 linhas, em português, o que você precisa lembrar "
    "na próxima: do que falamos, o que ficou combinado ou pendente e como a pessoa estava."
)

# Estimativa grosseira (≈ 4 caracteres por token). Serve para decidir quando resumir,
# sem depender de contagem do provedor.
CARACTERES_POR_TOKEN = 4
MENSAGENS_MANTIDAS = 4  # ao resumir, as últimas 2 trocas ficam inteiras


class Conversa:
    def __init__(self, cliente: Cliente, limite: int, personalidade: str, inteligencia: str, ultima_conversa: str):
        self.cliente = cliente
        self.limite = limite
        self.mensagens: list[dict] = []  # só usuário e Tony; o prompt de sistema é montado à parte
        self.resumo = ""                 # o começo desta conversa, quando ela fica longa
        self._fixo = self._parte_fixa(personalidade, inteligencia, ultima_conversa)

    @staticmethod
    def _parte_fixa(personalidade: str, inteligencia: str, ultima_conversa: str) -> str:
        agora = datetime.now()
        partes = [personalidade, f"# Agora\n\n{DIAS[agora.weekday()]}, {agora:%d/%m/%Y, %H:%M}."]
        if inteligencia:
            partes.append(f"# O que você sabe sobre quem está conversando com você\n\n{inteligencia}")
        if ultima_conversa:
            partes.append(f"# Como terminou a última conversa\n\n{ultima_conversa}")
        return "\n\n".join(partes)

    def prompt_de_sistema(self) -> str:
        if self.resumo:
            return f"{self._fixo}\n\n# O começo desta conversa (resumido)\n\n{self.resumo}"
        return self._fixo

    def _para_o_modelo(self) -> list[dict]:
        return [{"role": "system", "content": self.prompt_de_sistema()}, *self.mensagens]

    def tokens_estimados(self) -> int:
        texto = self.prompt_de_sistema() + "".join(m["content"] for m in self.mensagens)
        return len(texto) // CARACTERES_POR_TOKEN

    def responder(self, texto: str):
        """Envia a fala e devolve a resposta em pedaços. Se algo falhar no meio, a fala é desfeita."""
        self.mensagens.append({"role": "user", "content": texto})
        pedacos = []
        try:
            for pedaco in self.cliente.conversar(self._para_o_modelo()):
                pedacos.append(pedaco)
                yield pedaco
        except BaseException:  # erro do modelo ou Ctrl+C: a conversa volta a como estava
            self.mensagens.pop()
            raise
        self.mensagens.append({"role": "assistant", "content": "".join(pedacos)})
        if self.tokens_estimados() > 0.8 * self.limite:
            try:
                self._resumir_comeco()
            except ErroDoModelo:
                pass  # a resposta já saiu; tenta resumir de novo no próximo turno

    def _transcricao(self, mensagens: list[dict]) -> str:
        nomes = {"user": "Pessoa", "assistant": "Tony"}
        return "\n".join(f"{nomes[m['role']]}: {m['content']}" for m in mensagens)

    def _resumir_comeco(self) -> None:
        """Troca as mensagens antigas por um resumo, em vez de deixá-las cair em silêncio."""
        antigas = self.mensagens[:-MENSAGENS_MANTIDAS]
        if not antigas:
            return
        trecho = f"Resumo anterior:\n{self.resumo}\n\n" if self.resumo else ""
        self.resumo = self.cliente.completar([
            {"role": "system", "content": PEDIDO_RESUMO_PARCIAL},
            {"role": "user", "content": trecho + self._transcricao(antigas)},
        ])
        self.mensagens = self.mensagens[-MENSAGENS_MANTIDAS:]

    def resumir_para_proxima(self) -> str:
        """Resumo da conversa inteira, para a próxima sessão começar de onde esta parou."""
        if not self.mensagens:
            return ""
        return self.cliente.completar([
            *self._para_o_modelo(),
            {"role": "user", "content": PEDIDO_RESUMO_FINAL},
        ])
