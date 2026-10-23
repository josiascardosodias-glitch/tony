"""O que o Tony carrega antes de conversar: a personalidade, o que ele sabe sobre você e o fim da última conversa."""

import re
import subprocess
from datetime import datetime
from pathlib import Path


def carregar_personalidade(pasta: Path) -> str:
    """Junta os .md da personalidade em ordem alfabética."""
    return "\n\n".join(p.read_text(encoding="utf-8").strip() for p in sorted(pasta.glob("*.md")))


def versao_personalidade(pasta: Path) -> str:
    """Commit da última mudança na personalidade (+ '*' se há edição não commitada).

    Vai para o log: assim dá para saber qual versão do Tony deu cada resposta.
    """
    def git(*args):
        return subprocess.run(["git", *args], cwd=pasta, capture_output=True, text=True).stdout.strip()

    versao = git("log", "-1", "--format=%h", "--", ".") or "sem-commit"
    return versao + ("*" if git("status", "--porcelain", "--", ".") else "")


def ler_inteligencia(pasta: Path | None) -> str:
    """Notas .md de uma pasta (no caso, a Inteligência do vault), sem o que é só do Obsidian."""
    if not pasta or not pasta.is_dir():
        return ""
    return "\n\n".join(_limpar_nota(n.read_text(encoding="utf-8")) for n in sorted(pasta.glob("*.md")))


def _limpar_nota(texto: str) -> str:
    """Tira o frontmatter (--- ... ---) e os callouts (linhas com >), que não interessam ao modelo."""
    texto = re.sub(r"\A---\n.*?\n---\n", "", texto, flags=re.S)
    return "\n".join(l for l in texto.splitlines() if not l.startswith(">")).strip()


def ultimo_resumo(pasta: Path) -> str:
    resumos = sorted(pasta.glob("*.md")) if pasta.is_dir() else []
    return resumos[-1].read_text(encoding="utf-8") if resumos else ""


def salvar_resumo(pasta: Path, texto: str) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{datetime.now():%Y-%m-%d_%H%M%S}.md").write_text(texto, encoding="utf-8")
