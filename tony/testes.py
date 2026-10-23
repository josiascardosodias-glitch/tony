"""Falas de teste: roda falas fixas contra a personalidade atual e um modelo juiz dá o placar.

Cada fala roda várias vezes (a resposta varia a cada vez), sempre numa conversa nova, sem o resumo
da última conversa e com a memória de exemplo — assim o placar só muda quando a personalidade ou o
modelo mudam.
"""

import json
from datetime import datetime
from pathlib import Path

import yaml

from . import config
from .cliente import Cliente
from .conversa import Conversa
from .memoria import carregar_personalidade, ler_inteligencia, versao_personalidade

ESQUEMA_VEREDITO = {
    "type": "object",
    "properties": {
        "cumpre": {"type": "boolean", "description": "true se a resposta cumpre o critério"},
        "motivo": {"type": "string", "description": "uma frase explicando a decisão"},
    },
    "required": ["cumpre", "motivo"],
}

PEDIDO_JUIZ = (
    "Você avalia respostas de um assistente chamado Tony. Você recebe a fala da pessoa, a resposta "
    "do Tony e um critério. Decida se a resposta cumpre o critério — só o critério, não a qualidade "
    "geral. Seja rigoroso: na dúvida, não cumpre. Explique o motivo em uma frase, em português. "
    "Entregue o veredito chamando a função responder."
)


def carregar_falas(arquivo: Path, ids: list[str]) -> list[dict]:
    falas = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    if not ids:
        return falas
    desconhecidas = set(ids) - {f["id"] for f in falas}
    if desconhecidas:
        raise SystemExit(f"falas que não existem em {arquivo.name}: {', '.join(sorted(desconhecidas))}")
    return [f for f in falas if f["id"] in ids]


def julgar(juiz: Cliente, fala: str, resposta: str, espera: str) -> dict:
    return juiz.estruturado(
        [
            {"role": "system", "content": PEDIDO_JUIZ},
            {"role": "user", "content": f"Fala da pessoa:\n{fala}\n\nResposta do Tony:\n{resposta}\n\nCritério:\n{espera}"},
        ],
        ESQUEMA_VEREDITO,
    )


def ultimos_placares(cfg: dict) -> dict:
    """O placar mais recente de cada fala, juntando todas as rodadas salvas.

    Devolve {id: {"placar": "3/4", "personalidade": "68c6d83"}}. Fala por fala, para que uma rodada
    parcial (`tony testar ambiguo`) não apague a comparação das outras.
    """
    pasta = config.caminho(cfg["testes"]["resultados"])
    placares = {}
    for rodada in sorted(pasta.glob("*.json")) if pasta.is_dir() else []:
        dados = json.loads(rodada.read_text(encoding="utf-8"))
        for r in dados["resultados"]:
            placares[r["id"]] = {"placar": f"{r['acertos']}/{r['vezes']}", "personalidade": dados["personalidade"]}
    return placares


def rodar(cfg: dict, ids: list[str] = (), vezes: int | None = None,
          falas: list[dict] | None = None, salvar: bool = True) -> dict:
    """Roda as falas, mostra o placar e devolve {"resultados", "total", "possivel", "arquivo"}.

    `falas` troca as do falas.yaml (a revisão usa isso para testar as falas marcadas com /ruim).
    """
    tony = Cliente(cfg)
    juiz = Cliente(cfg, modelo=cfg["testes"]["juiz"], temperatura=0)
    pasta_personalidade = config.caminho(cfg["personalidade"])
    personalidade = carregar_personalidade(pasta_personalidade)
    versao = versao_personalidade(pasta_personalidade)
    inteligencia = ler_inteligencia(config.caminho(cfg["testes"]["inteligencia"]))
    if falas is None:
        falas = carregar_falas(config.caminho(cfg["testes"]["falas"]), ids)
    anteriores = ultimos_placares(cfg) if salvar else {}

    print(f"Personalidade {versao} · Tony: {tony.modelo} · juiz: {juiz.modelo}\n")
    resultados = []
    for item in falas:
        n = vezes or item.get("vezes") or cfg["testes"]["vezes"]
        print(f"{item['id']:<16} ", end="", flush=True)
        respostas = []
        for _ in range(n):
            conversa = Conversa(tony, cfg["contexto"]["limite"], personalidade, inteligencia, ultima_conversa="")
            for troca in item.get("antes", []):  # conversa que veio antes da fala testada
                conversa.mensagens += [{"role": "user", "content": troca["pessoa"]},
                                       {"role": "assistant", "content": troca["tony"]}]
            resposta = "".join(conversa.responder(item["fala"]))
            veredito = julgar(juiz, item["fala"], resposta, item["espera"])
            respostas.append({"resposta": resposta, "cumpre": bool(veredito["cumpre"]), "motivo": veredito["motivo"]})
            print("✓" if veredito["cumpre"] else "✗", end="", flush=True)
        acertos = sum(r["cumpre"] for r in respostas)
        antes = f"   (antes: {anteriores[item['id']]['placar']})" if item["id"] in anteriores else ""
        print(f"  {acertos}/{n}{antes}")
        for falha in [r for r in respostas if not r["cumpre"]][:2]:
            print(f"{'':17}✗ {falha['motivo']}")
        resultados.append({"id": item["id"], "fala": item["fala"], "espera": item["espera"],
                           "acertos": acertos, "vezes": n, "respostas": respostas})

    total, possivel = sum(r["acertos"] for r in resultados), sum(r["vezes"] for r in resultados)
    print(f"\nTotal: {total}/{possivel}")
    arquivo = None
    if salvar:
        pasta_resultados = config.caminho(cfg["testes"]["resultados"])
        pasta_resultados.mkdir(parents=True, exist_ok=True)
        arquivo = pasta_resultados / f"{datetime.now():%Y-%m-%d_%H%M%S}_{versao.replace('*', '-editada')}.json"
        arquivo.write_text(json.dumps(
            {"personalidade": versao, "modelo": tony.modelo, "juiz": juiz.modelo, "resultados": resultados},
            ensure_ascii=False, indent=2,
        ), encoding="utf-8")
        print(f"Respostas e motivos completos em {arquivo.relative_to(config.RAIZ)}")
    return {"resultados": resultados, "total": total, "possivel": possivel, "arquivo": arquivo}
