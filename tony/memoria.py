"""O que o Tony carrega antes de conversar: a personalidade, o que ele sabe sobre você, a memória
das conversas antigas e o fim da última conversa. E o que ele grava: resumos, memória e lembretes."""

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


def data_do_resumo(arquivo: Path) -> datetime:
    """Quando a conversa aconteceu, pelo nome do arquivo do resumo (AAAA-MM-DD_HHMMSS.md)."""
    return datetime.strptime(arquivo.stem, "%Y-%m-%d_%H%M%S")


def salvar_resumo(pasta: Path, texto: str) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{datetime.now():%Y-%m-%d_%H%M%S}.md").write_text(texto, encoding="utf-8")


# A memória guarda na primeira linha até qual resumo já foi consolidada. Se a consolidação falhar
# (sem rede, por exemplo), os resumos seguintes continuam pendentes e entram na próxima vez.
MARCA_MEMORIA = re.compile(r"\A<!-- até: (\S+) -->\n")


def ler_memoria(arquivo: Path) -> tuple[str, str]:
    """Devolve (memória, nome do último resumo consolidado). Vazios se ainda não há memória."""
    texto = arquivo.read_text(encoding="utf-8") if arquivo.is_file() else ""
    marca = MARCA_MEMORIA.match(texto)
    return texto[marca.end():].strip() if marca else texto.strip(), marca.group(1) if marca else ""


def salvar_memoria(arquivo: Path, texto: str, ate: str) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(f"<!-- até: {ate} -->\n{texto.strip()}\n", encoding="utf-8")


def resumos_pendentes(pasta: Path, ate: str) -> list[Path]:
    """Resumos que ainda não entraram na memória, menos o último (que já vai inteiro no prompt)."""
    resumos = sorted(pasta.glob("*.md"))[:-1] if pasta.is_dir() else []
    return [r for r in resumos if r.stem > ate]


CABECALHO_LEMBRETES = """---
criado: {hoje}
tags: [tony, inteligencia, lembretes]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

> [!note] Escrita pelo Tony
> Cada linha entrou com `/lembrar` e a sua confirmação. Pode editar ou apagar à vontade.

# Lembretes do Tony

"""


def lembrar(arquivo: Path, fato: str) -> None:
    """Acrescenta um fato no fim da nota de lembretes (criada na primeira vez)."""
    if not arquivo.exists():
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(CABECALHO_LEMBRETES.format(hoje=f"{datetime.now():%Y-%m-%d}"), encoding="utf-8")
    with arquivo.open("a+", encoding="utf-8") as f:
        f.seek(0)
        quebra = "" if f.read().endswith("\n") else "\n"  # você pode ter editado a nota sem a última quebra
        f.write(f"{quebra}- {fato} (anotado em {datetime.now():%d/%m/%Y})\n")
