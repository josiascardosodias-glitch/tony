"""O que as ferramentas de notas têm em comum: achar uma nota pelo nome, mesmo aproximado."""

from pathlib import Path

from ..memoria import limpar_nota
from . import ErroDaFerramenta, ambiente


def todas() -> dict[str, Path]:
    """{nome sem .md: caminho} das notas da Inteligência."""
    pasta = ambiente.inteligencia
    if not pasta or not pasta.is_dir():
        raise ErroDaFerramenta("não há pasta de notas configurada.")
    return {n.stem: n for n in sorted(pasta.glob("*.md"))}


def achar(nome: str) -> tuple[str, Path]:
    """A nota com esse nome. Aceita sem o prefixo "Tony - ", sem .md, maiúsculas trocadas ou só um
    pedaço do nome, desde que só uma nota combine (o modelo nem sempre acerta o nome exato)."""
    notas = todas()
    procurado = nome.removesuffix(".md").strip().casefold()
    exatas = [n for n in notas if n.casefold() in (procurado, f"tony - {procurado}")]
    parecidas = exatas or [n for n in notas if procurado in n.casefold()]
    if len(parecidas) == 1:
        return parecidas[0], notas[parecidas[0]]
    opcoes = ", ".join(parecidas or notas) or "nenhuma"
    raise ErroDaFerramenta(f"não achei uma nota só chamada {nome!r}. Notas {'parecidas' if parecidas else 'que existem'}: {opcoes}.")


def texto(caminho: Path) -> str:
    return limpar_nota(caminho.read_text(encoding="utf-8"))
