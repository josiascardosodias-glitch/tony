"""Uma conversa: monta o prompt de sistema, guarda o histórico e resume o começo quando o contexto enche.

Desde a v4 não há memória entre conversas: cada uma começa só com a personalidade e a Inteligência.
"""

from datetime import datetime, timedelta

from .cliente import Chamada, Cliente, ErroDoModelo
from .ferramentas import executar

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

PEDIDO_RESUMO_PARCIAL = (
    "Resuma o trecho de conversa abaixo em poucas linhas, em português, para você mesmo continuar "
    "a conversa depois: assuntos, decisões, o que ficou pendente e o tom. Se houver um resumo "
    "anterior no início, incorpore-o."
)

# Estimativa grosseira (≈ 4 caracteres por token). Serve para decidir quando resumir,
# sem depender de contagem do provedor.
CARACTERES_POR_TOKEN = 4
TROCAS_MANTIDAS = 2  # ao resumir, as últimas 2 trocas ficam inteiras
RODADAS_DE_FERRAMENTA = 5  # numa resposta, no máximo 5 idas e voltas com ferramentas


class Conversa:
    def __init__(self, cliente: Cliente, limite: int, personalidade: str, inteligencia: str,
                 ferramentas: dict | None = None, agenda: str = ""):
        self.cliente = cliente
        self.ferramentas = ferramentas or {}  # {nome: função}; vazio = só conversa
        self.limite = limite
        self.mensagens: list[dict] = []  # só usuário e Tony; o prompt de sistema é montado à parte
        self.resumo = ""                 # o começo desta conversa, quando ela fica longa
        self._fixo = self._parte_fixa(personalidade, inteligencia, agenda)

    @staticmethod
    def _parte_fixa(personalidade: str, inteligencia: str, agenda: str = "") -> str:
        agora = datetime.now()
        partes = [personalidade, f"# Agora\n\n{DIAS[agora.weekday()]}, {agora:%d/%m/%Y, %H:%M}."]
        if inteligencia:
            partes.append(f"# O que você sabe sobre quem está conversando com você\n\n{inteligencia}")
        if agenda:
            partes.append(f"# A agenda dela nos próximos 30 dias\n\n{agenda}\n\n(É o que o código achou nos "
                          "e-mails dela. Você não lê os e-mails: o que não está aqui, você não sabe.)")
        return "\n\n".join(partes)

    def prompt_de_sistema(self) -> str:
        prompt = self._fixo
        if self.resumo:
            prompt += f"\n\n# O começo desta conversa (resumido)\n\n{self.resumo}"
        return prompt

    def _para_o_modelo(self) -> list[dict]:
        return [{"role": "system", "content": self.prompt_de_sistema()}, *self.mensagens]

    def tokens_estimados(self) -> int:
        texto = self.prompt_de_sistema() + "".join(m["content"] for m in self.mensagens)
        return len(texto) // CARACTERES_POR_TOKEN

    def responder(self, texto: str):
        """Envia a fala e devolve a resposta: pedaços de texto e, antes de rodar cada ferramenta que o
        modelo pedir, a `Chamada` (com o `resultado` preenchido depois). Se algo falhar no meio, a fala
        e as chamadas dela são desfeitas."""
        inicio = len(self.mensagens)
        self.mensagens.append({"role": "user", "content": texto})
        try:
            for _ in range(RODADAS_DE_FERRAMENTA):
                pedacos, chamadas = [], []
                for item in self.cliente.conversar(self._para_o_modelo(), list(self.ferramentas.values())):
                    if isinstance(item, Chamada):
                        chamadas.append(item)
                    else:
                        pedacos.append(item)
                        yield item
                if not chamadas:
                    break
                # O modelo pediu ferramentas: o pedido e cada resultado entram no histórico, e ele
                # responde de novo, agora sabendo o resultado.
                self.mensagens.append({"role": "assistant", "content": "".join(pedacos), "tool_calls": [
                    {"function": {"name": c.nome, "arguments": c.argumentos}} for c in chamadas]})
                for chamada in chamadas:
                    yield chamada
                    chamada.resultado = executar(self.ferramentas, chamada.nome, chamada.argumentos)
                    self.mensagens.append({"role": "tool", "content": chamada.resultado, "tool_name": chamada.nome})
            else:
                pedacos = ["(parei: foram ferramentas demais para uma resposta só.)"]
                yield pedacos[0]
        except BaseException:  # erro do modelo ou Ctrl+C: a conversa volta a como estava
            del self.mensagens[inicio:]
            raise
        self.mensagens.append({"role": "assistant", "content": "".join(pedacos)})
        if self.tokens_estimados() > 0.8 * self.limite:
            try:
                self._resumir_comeco()
            except ErroDoModelo:
                pass  # a resposta já saiu; tenta resumir de novo no próximo turno

    def transcricao(self, mensagens: list[dict]) -> str:
        nomes = {"user": "Pessoa", "assistant": "Tony", "tool": "Ferramenta"}
        return "\n".join(f"{nomes[m['role']]}: {m['content']}" for m in mensagens if m["content"])

    def _resumir_comeco(self) -> None:
        """Troca as mensagens antigas por um resumo, em vez de deixá-las cair em silêncio."""
        # O corte é sempre numa fala da pessoa: um resultado de ferramenta sem o pedido dele confunde o modelo.
        falas = [i for i, m in enumerate(self.mensagens) if m["role"] == "user"]
        if len(falas) <= TROCAS_MANTIDAS:
            return
        corte = falas[-TROCAS_MANTIDAS]
        antigas = self.mensagens[:corte]
        trecho = f"Resumo anterior:\n{self.resumo}\n\n" if self.resumo else ""
        self.resumo = self.cliente.completar([
            {"role": "system", "content": PEDIDO_RESUMO_PARCIAL},
            {"role": "user", "content": trecho + self.transcricao(antigas)},
        ])
        self.mensagens = self.mensagens[corte:]


def calendario(inicio: datetime, dias: int = 14) -> str:
    """Os próximos dias com o dia da semana. Modelo erra conta de calendário; consultar uma lista, não."""
    return "\n".join(f"{DIAS[d.weekday()]}, {d:%d/%m/%Y}" for d in (inicio + timedelta(n) for n in range(dias)))
