from . import _notas


def listar_notas() -> str:
    """Lista as notas que você tem sobre a pessoa (nome e tamanho de cada uma)."""
    notas = _notas.todas()
    if not notas:
        return "não há nenhuma nota."
    return "\n".join(f"- {nome} ({len(_notas.texto(caminho).splitlines())} linhas)" for nome, caminho in notas.items())
