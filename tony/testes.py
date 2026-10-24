"""Falas de teste: roda falas fixas contra a personalidade atual e um modelo juiz dá o placar.

Cada fala roda várias vezes (a resposta varia a cada vez), sempre numa conversa nova e com a
Inteligência de exemplo; resumo da última conversa e memória antiga só entram quando a fala traz os
seus (`ultima_conversa`, `memoria`) — assim o placar só muda quando a personalidade ou o modelo mudam.

Além de respostas, dá para testar a memória: `tarefa: resumo` julga o resumo que o Tony faz da
conversa `antes`, e `tarefa: memoria` julga a memória depois de esse resumo entrar nela.
"""

import json
from datetime import datetime
from pathlib import Path

import yaml

from . import config
from .cliente import Cliente
from .conversa import DIAS, TEMPERATURA_MEMORIA, Conversa, consolidar_memoria
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
    "Você avalia um assistente chamado Tony. Você recebe a situação (a fala da pessoa, às vezes com "
    "o que o Tony lembrava de antes, ou uma conversa que ele resumiu), o que o Tony produziu e um "
    "critério. Decida se o que ele produziu cumpre o critério — só o critério, não a qualidade "
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


def julgar(juiz: Cliente, situacao: str, resposta: str, espera: str) -> dict:
    return juiz.estruturado(
        [
            {"role": "system", "content": PEDIDO_JUIZ},
            {"role": "user", "content": f"{situacao}\n\nO que o Tony produziu:\n{resposta}\n\nCritério:\n{espera}"},
        ],
        ESQUEMA_VEREDITO,
    )


def produzir(item: dict, conversa: Conversa, organizador: Cliente) -> tuple[str, str]:
    """Faz o Tony produzir o que a fala testa. Devolve (situação para o juiz, o que ele produziu)."""
    for troca in item.get("antes", []):  # conversa que veio antes da fala testada
        conversa.mensagens += [{"role": "user", "content": troca["pessoa"]},
                               {"role": "assistant", "content": troca["tony"]}]
    contexto = ""
    if item.get("memoria"):
        contexto += f"Memória antiga do Tony:\n{item['memoria']}\n\n"
    if item.get("ultima_conversa"):
        contexto += f"Resumo da última conversa, que o Tony tinha:\n{item['ultima_conversa']}\n\n"
    tarefa = item.get("tarefa", "fala")
    if tarefa == "fala":
        return f"{contexto}Fala da pessoa:\n{item['fala']}", "".join(conversa.responder(item["fala"]))
    situacao = f"{contexto}Conversa:\n{conversa.transcricao(conversa.mensagens)}"
    resumo = conversa.resumir_para_proxima()
    if tarefa == "resumo":
        return situacao, resumo
    if tarefa == "memoria":
        hoje = datetime.now()
        return (f"{situacao}\n\nA conversa foi em {DIAS[hoje.weekday()]}, {hoje:%d/%m/%Y}. Resumo que o Tony fez dela:\n{resumo}",
                consolidar_memoria(organizador, item.get("memoria", ""), resumo, hoje))
    raise SystemExit(f"tarefa desconhecida na fala {item['id']}: {tarefa} (use fala, resumo ou memoria)")


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
    organizador = Cliente(cfg, temperatura=TEMPERATURA_MEMORIA)
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
        print(f"{item['id']:<20} ", end="", flush=True)
        respostas = []
        for _ in range(n):
            conversa = Conversa(tony, cfg["contexto"]["limite"], personalidade, inteligencia,
                                ultima_conversa=item.get("ultima_conversa", ""), memoria=item.get("memoria", ""))
            situacao, resposta = produzir(item, conversa, organizador)
            veredito = julgar(juiz, situacao, resposta, item["espera"])
            respostas.append({"resposta": resposta, "cumpre": bool(veredito["cumpre"]), "motivo": veredito["motivo"]})
            print("✓" if veredito["cumpre"] else "✗", end="", flush=True)
        acertos = sum(r["cumpre"] for r in respostas)
        antes = f"   (antes: {anteriores[item['id']]['placar']})" if item["id"] in anteriores else ""
        print(f"  {acertos}/{n}{antes}")
        for falha in [r for r in respostas if not r["cumpre"]][:2]:
            print(f"{'':21}✗ {falha['motivo']}")
        resultados.append({"id": item["id"], "fala": item.get("fala") or f"({item['tarefa']})", "espera": item["espera"],
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
