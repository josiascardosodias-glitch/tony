"""Ferramentas do Tony: uma função por arquivo nesta pasta, descobertas automaticamente.

O modelo só vê o nome, a docstring e os tipos de cada função (a lib `ollama` monta o esquema a partir
deles). O corpo pode fazer qualquer coisa — ler um arquivo, chamar uma API ou um webhook — e ser
trocado sem mexer no laço da conversa.

Para criar uma ferramenta, um arquivo `nome.py` com:
- uma função pública com o mesmo nome do arquivo;
- docstring com o que ela faz e a seção `Args:` (é o que o modelo lê para decidir usar);
- retorno em texto; para avisar um problema ao modelo, levante `ErroDaFerramenta`;
- se ela escreve ou muda algo, pergunte antes com `ambiente.confirmar(...)`.
Arquivos que começam com `_` não são ferramentas.
"""

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class ErroDaFerramenta(Exception):
    """Um problema que o modelo precisa saber para tentar de outro jeito (ex.: nota que não existe)."""


@dataclass
class Ambiente:
    """O que as ferramentas usam além dos argumentos do modelo. A sessão (ou o teste) preenche."""
    inteligencia: Path | None = None              # a única pasta que as ferramentas enxergam
    lembretes: Path | None = None                 # onde `lembrar` escreve
    confirmar: Callable[[str], bool] = lambda pergunta: False  # quem conversa diz sim ou não


ambiente = Ambiente()


def descobrir() -> dict[str, Callable]:
    """{nome: função} de cada arquivo desta pasta."""
    ferramentas = {}
    for modulo in pkgutil.iter_modules(__path__):
        if modulo.name.startswith("_"):
            continue
        funcao = getattr(importlib.import_module(f"{__name__}.{modulo.name}"), modulo.name, None)
        if callable(funcao):
            ferramentas[modulo.name] = funcao
    return ferramentas


def executar(ferramentas: dict[str, Callable], nome: str, argumentos: dict) -> str:
    """Roda uma chamada do modelo e devolve o texto que volta para ele — inclusive o erro, para que
    ele corrija a chamada em vez de a conversa quebrar."""
    funcao = ferramentas.get(nome)
    if not funcao:
        return f"erro: não existe a ferramenta {nome!r}. As que existem: {', '.join(ferramentas)}."
    parametros = inspect.signature(funcao).parameters
    sobrando = sorted(set(argumentos) - set(parametros))
    faltando = [p for p, v in parametros.items() if v.default is inspect.Parameter.empty and p not in argumentos]
    if sobrando or faltando:
        return f"erro: argumentos errados para {nome} (faltando: {faltando or 'nenhum'}; sobrando: {sobrando or 'nenhum'})."
    try:
        return str(funcao(**argumentos))
    except ErroDaFerramenta as e:
        return f"erro: {e}"
