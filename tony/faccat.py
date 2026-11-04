"""A conta da Faccat pelo App da Web do Apps Script (`TheForge/apps-script/tony.gs`).

A conta da faculdade não passa pelo OAuth do Tony: quem lê o Gmail e o Classroom é um Apps Script
dentro da própria conta Faccat, publicado como App da Web. O Tony chama a URL com uma chave secreta,
o `desde` (a última coleta) e o filtro (categorias e bloqueados, para que e-mail bloqueado nem saia
do Google), e recebe {conta, prazos, emails} em JSON. As datas dos e-mails são achadas aqui, no PC,
pelo mesmo extrator das outras contas; os prazos do Classroom já vêm prontos.

URL e chave ficam no arquivo da conta (padrão `~/.config/tony/faccat.env`, chmod 600):
    TONY_FACCAT_URL=https://script.google.com/macros/s/.../exec
    TONY_FACCAT_CHAVE=<a mesma das propriedades do script>
"""

import os
import secrets
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

import httpx

from . import config
from .coleta import Mensagem


class ErroDaFaccat(Exception):
    pass


def ler_arquivo(arquivo: Path) -> dict:
    valores = {}
    if arquivo.is_file():
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            chave, _, valor = linha.partition("=")
            if chave.strip():
                valores[chave.strip()] = valor.strip().strip("'\"")
    return valores


def _gravar(arquivo: Path, valores: dict) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    descritor = os.open(arquivo, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descritor, "w", encoding="utf-8") as f:
        f.write("".join(f"{k}={v}\n" for k, v in valores.items()))
    os.chmod(arquivo, 0o600)


def configurar(conta: dict, url: str | None) -> str:
    """Cria a chave na primeira vez e guarda a URL. Devolve o que mostrar para você."""
    arquivo = config.caminho(conta["arquivo"])
    valores = ler_arquivo(arquivo)
    nova = "TONY_FACCAT_CHAVE" not in valores
    if nova:
        valores["TONY_FACCAT_CHAVE"] = secrets.token_urlsafe(32)
    if url:
        if not url.startswith("https://script.google.com/") or not url.rstrip("/").endswith("/exec"):
            raise SystemExit("a URL do App da Web começa com https://script.google.com/ e termina em /exec")
        valores["TONY_FACCAT_URL"] = url.rstrip("/")
    _gravar(arquivo, valores)
    linhas = [f"guardado em {arquivo} (chmod 600)."]
    if nova or not url:
        linhas += ["", "No editor do Apps Script da Faccat: Configurações do projeto > Propriedades do script >",
                   "adicionar a propriedade TONY_CHAVE com este valor:", "", f"    {valores['TONY_FACCAT_CHAVE']}"]
    if not valores.get("TONY_FACCAT_URL"):
        linhas += ["", "Depois de implantar o App da Web: uv run tony faccat --url <a URL /exec>"]
    return "\n".join(linhas)


class FonteAppsScript:
    """Uma chamada ao App da Web por coleta: os prazos e os e-mails novos de uma vez."""

    def __init__(self, conta: dict, http: httpx.Client | None = None):
        valores = ler_arquivo(config.caminho(conta["arquivo"]))
        if not valores.get("TONY_FACCAT_URL") or not valores.get("TONY_FACCAT_CHAVE"):
            raise ErroDaFaccat(f"a conta {conta['nome']} ainda não está configurada: rode `uv run tony faccat`")
        self.url, self.chave = valores["TONY_FACCAT_URL"], valores["TONY_FACCAT_CHAVE"]
        self.http = http or httpx.Client(timeout=120, follow_redirects=True)  # o Apps Script redireciona
        self.resposta: dict | None = None

    def _buscar(self, depois_de: datetime, filtro: str) -> dict:
        if self.resposta is None:
            try:
                r = self.http.get(self.url, params={"chave": self.chave, "desde": int(depois_de.timestamp()),
                                                    "filtro": filtro})
                dados = r.json()
            except (httpx.HTTPError, ValueError) as e:
                # a URL e a chave nunca aparecem no erro
                raise ErroDaFaccat(f"o App da Web não respondeu direito ({type(e).__name__})") from None
            if "erro" in dados:
                raise ErroDaFaccat(f"o App da Web recusou: {dados['erro']}")
            self.resposta = dados
        return self.resposta

    def preparar(self, depois_de: datetime, filtro: str) -> None:
        """A coleta pede os prazos antes das mensagens: os dois vêm na mesma chamada."""
        self._buscar(depois_de, filtro)

    def prazos(self) -> list[dict]:
        if self.resposta is None:
            return []
        return [{
            "id": f"classroom.{p['id']}", "email": "", "remetente": "classroom", "nome": p["turma"],
            "titulo": f"[{p['turma']}] {p['titulo']}", "data": p["prazo"], "hora": p.get("hora"),
            "descricao": (p.get("descricao") or p["titulo"]).strip(), "origem": "classroom", "confianca": 1.0,
            "link": p.get("link", ""), "recebido": p.get("atualizado_em", ""),
        } for p in self.resposta.get("prazos", [])]

    def mensagens(self, depois_de: datetime, filtro: str, vistos: set):
        for e in self._buscar(depois_de, filtro).get("emails", []):
            nome, endereco = parseaddr(e.get("de", ""))
            texto = (e.get("texto") or "").strip()
            yield Mensagem(
                id=e["id"], de=endereco.lower(), nome=nome, assunto=(e.get("assunto") or "").strip(),
                recebido=datetime.fromtimestamp(int(e["data"]) / 1000, tz=timezone.utc).astimezone(),
                texto=texto, trecho=" ".join(texto.split())[:160], convites=e.get("convites", []),
                em_massa=bool(e.get("em_massa")),
            )
