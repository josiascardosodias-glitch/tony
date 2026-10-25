from . import _notas

MAX_NOTAS = 5
MAX_LINHAS = 4


def buscar_notas(termos: str) -> str:
    """Procura palavras nas suas notas sobre a pessoa e devolve as linhas onde elas aparecem.

    Args:
        termos: uma ou mais palavras (ex.: "horário estudo"); acha linhas com qualquer uma delas
    """
    palavras = [p for p in termos.casefold().split() if len(p) > 2] or [termos.casefold()]
    achados = []
    for nome, caminho in _notas.todas().items():
        linhas = [l.strip() for l in _notas.texto(caminho).splitlines()
                  if l.strip() and any(p in l.casefold() for p in palavras)]
        if linhas:
            achados.append((len(linhas), nome, linhas[:MAX_LINHAS]))
    if not achados:
        return f"nada encontrado para {termos!r}."
    achados.sort(reverse=True)  # as notas com mais linhas encontradas primeiro
    return "\n\n".join(f"## {nome}\n" + "\n".join(linhas) for _, nome, linhas in achados[:MAX_NOTAS])
