"""Revisão: lê as respostas marcadas com /ruim e propõe UMA mudança na personalidade por rodada.

O fluxo: juntar as marcações pendentes → o revisor (outro modelo) propõe uma troca de trecho num
arquivo de `personalidade/` → você vê o diff → se aceitar, a mudança é aplicada e testada (placar
antes e depois, mais as próprias falas marcadas) → você decide se ela fica. Nada de commit
automático, e nada fora de `personalidade/` é tocado.
"""

import difflib
import json
import sys
from datetime import datetime
from pathlib import Path

from . import config, testes
from .cliente import Cliente, ErroDoModelo
from .memoria import versao_personalidade

PEDIDO_REVISOR = """Você revisa a personalidade de um assistente de IA chamado Tony. A personalidade é \
um conjunto de arquivos em Markdown que vira o prompt de sistema dele. Você recebe esses arquivos, \
respostas do Tony que o criador marcou como ruins (com o motivo) e algumas marcadas como boas.

Proponha UMA mudança, a menor possível, que corrija o problema mais importante das respostas ruins \
sem estragar o que as boas fazem bem. Regras:
- `trecho_antigo` é copiado EXATAMENTE do arquivo (mesmos espaços e pontuação) e aparece nele uma vez só.
- `trecho_novo` substitui o trecho antigo. Para acrescentar uma regra, use uma linha existente como \
trecho antigo e repita essa linha no trecho novo, seguida da regra nova.
- Escreva no mesmo estilo e idioma dos arquivos (português do Brasil, frases curtas e diretas).
- Diga ao Tony o que fazer de forma concreta; evite proibições vagas.
Entregue a proposta chamando a função responder."""


def esquema_proposta(arquivos: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "diagnostico": {"type": "string", "description": "o que as respostas ruins têm em comum e por que a personalidade atual permite isso"},
            "arquivo": {"type": "string", "enum": arquivos, "description": "arquivo da personalidade a mudar"},
            "trecho_antigo": {"type": "string", "description": "trecho copiado exatamente do arquivo"},
            "trecho_novo": {"type": "string", "description": "texto que substitui o trecho antigo"},
            "motivo": {"type": "string", "description": "uma frase: por que essa mudança resolve"},
            "marcas": {"type": "array", "items": {"type": "integer"}, "description": "números das respostas ruins que a mudança resolve"},
        },
        "required": ["diagnostico", "arquivo", "trecho_antigo", "trecho_novo", "motivo", "marcas"],
    }


# ---------- marcações ----------

def ler_marcas(pasta_logs: Path) -> list[dict]:
    """Todas as marcações /bom e /ruim dos logs, com o turno marcado e as duas trocas anteriores."""
    marcas = {}
    for arquivo in sorted(pasta_logs.glob("*.jsonl")) if pasta_logs.is_dir() else []:
        versao, turnos, conversa = "?", {}, []
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            evento = json.loads(linha)
            tipo = evento["tipo"]
            if tipo == "inicio":
                versao = evento.get("personalidade", "?")
            elif tipo == "nova_conversa":
                conversa = []
            elif tipo == "turno":
                turnos[evento["turno"]] = evento
                conversa.append(evento["turno"])
            elif tipo == "marca" and evento["turno"] in turnos:
                n = evento["turno"]
                anteriores = conversa[:conversa.index(n)][-2:] if n in conversa else []
                chave = f"{arquivo.name}#{n}"  # a marcação mais recente do mesmo turno vale
                marcas[chave] = {
                    "chave": chave, "valor": evento["valor"], "motivo": evento.get("motivo", ""),
                    "versao": versao, "turno": turnos[n], "contexto": [turnos[i] for i in anteriores],
                }
    return list(marcas.values())


def chaves_revisadas(arquivo: Path) -> set[str]:
    if not arquivo.exists():
        return set()
    feitas = set()
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        evento = json.loads(linha)
        if evento["decisao"] in ("aceita", "descartada"):
            feitas.update(evento["marcas"])
    return feitas


def registrar(arquivo: Path, decisao: str, marcas: list[dict], **dados) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    evento = {"hora": datetime.now().isoformat(timespec="seconds"), "decisao": decisao,
              "marcas": [m["chave"] for m in marcas], **dados}
    with arquivo.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


# ---------- proposta ----------

def _descrever(marca: dict) -> str:
    linhas = [f"Pessoa: {t['usuario']}\nTony: {t['tony']}" for t in marca["contexto"]]
    contexto = ("Antes, na mesma conversa:\n" + "\n".join(linhas) + "\n") if linhas else ""
    return (f"{contexto}Fala: {marca['turno']['usuario']}\nResposta do Tony: {marca['turno']['tony']}\n"
            f"Personalidade em uso: {marca['versao']}")


def _pedido(arquivos: dict[str, str], ruins: list[dict], boas: list[dict]) -> str:
    partes = ["# Arquivos da personalidade"]
    partes += [f"## {nome}\n```\n{texto}\n```" for nome, texto in arquivos.items()]
    partes.append("# Respostas marcadas como ruins")
    for i, m in enumerate(ruins, 1):
        partes.append(f"[{i}]\n{_descrever(m)}\nProblema apontado: {m['motivo'] or '(sem motivo)'}")
    if boas:
        partes.append("# Respostas marcadas como boas (não podem piorar)")
        partes += [_descrever(m) for m in boas]
    return "\n\n".join(partes)


def _problema(proposta: dict, arquivos: dict[str, str]) -> str:
    """Por que a proposta não pode ser aplicada ('' se pode)."""
    texto = arquivos.get(proposta["arquivo"])
    if texto is None:
        return f"o arquivo {proposta['arquivo']} não existe."
    ocorrencias = texto.count(proposta["trecho_antigo"]) if proposta["trecho_antigo"] else 0
    if ocorrencias != 1:
        return (f"o trecho_antigo aparece {ocorrencias} vezes em {proposta['arquivo']}; precisa aparecer "
                "exatamente uma vez. Copie-o do arquivo letra por letra.")
    if proposta["trecho_novo"].strip() == proposta["trecho_antigo"].strip():
        return "o trecho_novo é igual ao trecho_antigo."
    return ""


def propor(revisor: Cliente, arquivos: dict[str, str], ruins: list[dict], boas: list[dict],
           recusadas: list[dict]) -> dict:
    """Pede uma proposta ao revisor, devolvendo o erro a ele quando ela não dá para aplicar."""
    pedido = _pedido(arquivos, ruins, boas)
    if recusadas:
        pedido += "\n\n# Propostas já recusadas (proponha algo diferente)\n" + "\n".join(
            f"- {p['arquivo']}: {p['trecho_novo']!r}" for p in recusadas)
    mensagens = [{"role": "system", "content": PEDIDO_REVISOR}, {"role": "user", "content": pedido}]
    esquema = esquema_proposta(list(arquivos))
    for _ in range(3):
        proposta = revisor.estruturado(mensagens, esquema)
        problema = _problema(proposta, arquivos)
        if not problema:
            return proposta
        mensagens += [
            {"role": "assistant", "content": json.dumps(proposta, ensure_ascii=False)},
            {"role": "user", "content": f"Essa proposta não pode ser aplicada: {problema} Corrija e chame responder de novo."},
        ]
    raise ErroDoModelo(f"o revisor não chegou a uma proposta aplicável em 3 tentativas ({problema})")


# ---------- terminal ----------

def _diff(nome: str, antes: str, depois: str) -> str:
    cores = sys.stdout.isatty()
    linhas = []
    for linha in difflib.unified_diff(antes.splitlines(), depois.splitlines(),
                                      f"personalidade/{nome}", f"personalidade/{nome}", lineterm=""):
        if cores and linha.startswith("+") and not linha.startswith("+++"):
            linha = f"\033[32m{linha}\033[0m"
        elif cores and linha.startswith("-") and not linha.startswith("---"):
            linha = f"\033[31m{linha}\033[0m"
        linhas.append(linha)
    return "\n".join(linhas)


def _perguntar(texto: str, opcoes: str) -> str:
    while True:
        try:
            resposta = input(f"{texto} ").strip().lower()[:1]
        except EOFError:
            return opcoes[-1]  # sem entrada: a opção mais segura, que é sempre a última
        if resposta in opcoes:
            return resposta


# ---------- fluxo ----------

def revisar(cfg: dict, pasta_logs: Path | None = None) -> None:
    pasta_logs = pasta_logs or config.caminho(cfg["logs"])
    arquivo_registro = config.caminho(cfg["revisao"]["registro"])
    pasta_personalidade = config.caminho(cfg["personalidade"])
    versao_atual = versao_personalidade(pasta_personalidade).rstrip("*")

    marcas = ler_marcas(pasta_logs)
    feitas = chaves_revisadas(arquivo_registro)
    ruins = [m for m in marcas if m["valor"] == "ruim" and m["chave"] not in feitas]
    boas = [m for m in marcas if m["valor"] == "bom"][-5:]
    if not ruins:
        print("Nenhuma resposta marcada com /ruim esperando revisão.")
        return

    print(f"{len(ruins)} resposta(s) marcada(s) com /ruim esperando revisão:\n")
    for i, m in enumerate(ruins, 1):
        aviso = "" if m["versao"].rstrip("*") == versao_atual else f"   ⚠ personalidade antiga ({m['versao']}): talvez já corrigido"
        print(f"  [{i}] \"{m['turno']['usuario'][:60]}\" → {m['motivo'] or '(sem motivo)'}{aviso}")

    revisor = Cliente(cfg, modelo=cfg["revisao"]["revisor"], temperatura=0.3)
    recusadas = []
    while True:
        arquivos = {p.name: p.read_text(encoding="utf-8") for p in sorted(pasta_personalidade.glob("*.md"))}
        print(f"\nPedindo uma proposta ao revisor ({revisor.modelo})...\n")
        proposta = propor(revisor, arquivos, ruins, boas, recusadas)
        nome, antes = proposta["arquivo"], arquivos[proposta["arquivo"]]
        depois = antes.replace(proposta["trecho_antigo"], proposta["trecho_novo"], 1)
        resolve = [ruins[i - 1] for i in proposta["marcas"] if 1 <= i <= len(ruins)] or ruins

        print(f"Diagnóstico: {proposta['diagnostico']}")
        print(f"Mudança: {proposta['motivo']}")
        print(f"Resolve: {', '.join(f'[{ruins.index(m) + 1}]' for m in resolve)}\n")
        print(_diff(nome, antes, depois) + "\n")
        escolha = _perguntar("[a]ceitar e testar · [o]utra proposta · [d]escartar as marcações · [s]air", "aods")
        if escolha == "s":
            return
        if escolha == "d":
            registrar(arquivo_registro, "descartada", ruins)
            print("Marcações descartadas: não serão propostas de novo.")
            return
        if escolha == "o":
            registrar(arquivo_registro, "recusada", resolve, proposta=proposta)
            recusadas.append(proposta)
            continue
        break

    # Aceitou: placar antes (se a versão atual ainda não tem), aplica, placar depois, falas marcadas.
    if any(p["personalidade"] != versao_personalidade(pasta_personalidade)
           for p in testes.ultimos_placares(cfg).values()) or not testes.ultimos_placares(cfg):
        print("\n— Placar antes da mudança —")
        testes.rodar(cfg)
    caminho = pasta_personalidade / nome
    caminho.write_text(depois, encoding="utf-8")
    print("\n— Placar depois da mudança —")
    rodada = testes.rodar(cfg)
    com_motivo = [m for m in resolve if m["motivo"]]
    if com_motivo:
        print("\n— As falas marcadas, depois da mudança —")
        testes.rodar(cfg, salvar=False, falas=[
            {"id": f"marcada-{ruins.index(m) + 1}", "fala": m["turno"]["usuario"],
             "espera": f"A resposta não tem este problema: {m['motivo']}",
             "antes": [{"pessoa": c["usuario"], "tony": c["tony"]} for c in m["contexto"]]}
            for m in com_motivo])

    if _perguntar("\nManter a mudança? [s/n]", "sn") == "n":
        caminho.write_text(antes, encoding="utf-8")
        rodada["arquivo"].unlink()  # o placar da versão desfeita não serve de comparação
        registrar(arquivo_registro, "desfeita", resolve, proposta=proposta)
        print("Mudança desfeita. As marcações continuam pendentes.")
        return
    registrar(arquivo_registro, "aceita", resolve, proposta=proposta,
              placar=f"{rodada['total']}/{rodada['possivel']}")
    print(f"\nMudança mantida em personalidade/{nome}. Para guardar no histórico:\n"
          f"  git add personalidade && git commit -m \"Personalidade: {proposta['motivo']}\"")
