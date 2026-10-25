from .. import memoria
from . import ErroDaFerramenta, ambiente


def lembrar(fato: str) -> str:
    """Guarda um fato sobre a pessoa para lembrar nas próximas conversas. A pessoa confirma antes.
    Use quando ela pedir para você guardar, anotar ou lembrar de algo.

    Args:
        fato: o fato em uma frase curta, em terceira pessoa (ex.: "a apresentação do TCC é em 20/11/2026")
    """
    if not ambiente.lembretes:
        raise ErroDaFerramenta("não há onde guardar lembretes (falta configurar a pasta de notas).")
    if not ambiente.confirmar(f"guardar em {ambiente.lembretes.name}:\n  - {fato}"):
        return "a pessoa disse não na confirmação: nada foi guardado. Não pergunte de novo; diga que não guardou."
    memoria.lembrar(ambiente.lembretes, fato)
    return "guardado."
