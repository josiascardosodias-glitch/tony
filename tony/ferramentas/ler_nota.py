from . import _notas


def ler_nota(nome: str) -> str:
    """Lê uma das suas notas sobre a pessoa, inteira.

    Args:
        nome: o nome da nota, como aparece em listar_notas (ex.: "Tony - Sobre o Josias")
    """
    nome_certo, caminho = _notas.achar(nome)
    return f"# Nota: {nome_certo}\n\n{_notas.texto(caminho)}"
