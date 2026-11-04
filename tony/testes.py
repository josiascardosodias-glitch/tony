"""Falas de teste: roda falas fixas contra a personalidade atual e um modelo juiz dá o placar.

Cada fala roda várias vezes (a resposta varia a cada vez), sempre numa conversa nova e com a
Inteligência de exemplo — assim o placar só muda quando a personalidade ou o modelo mudam.

`agenda` (lista de {data, hora, titulo,
descricao}, com datas como `{hoje+5}`) é o que está marcado na fala; sem ela, a agenda está vazia. Ferramentas: `chama: [a, b]` exige que
ele chame ao menos uma delas; `chama: []`, que não chame nenhuma, com a confirmação "sim" (ou "não",
com `confirma: false`); `lista: true`, que toda linha comece com "- " — conferidos no código, sem
juiz. Em qualquer texto, `{hoje+3}` vira a data de daqui a 3 dias (dd/mm/aaaa), para os testes não
vencerem.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from . import config, ferramentas
from .cliente import Chamada, Cliente
from .consulta import para_o_modelo
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
    "Você avalia um assistente chamado Tony. Você recebe a situação (a fala da pessoa, às vezes com "
    "a conversa que veio antes), o que o Tony produziu e um critério. Decida se o que ele produziu cumpre o critério — só o critério, não a qualidade "
    "geral. Seja rigoroso: na dúvida, não cumpre. Explique o motivo em uma frase, em português. "
    "Entregue o veredito chamando a função responder."
)


def _com_datas(valor):
    """Troca {hoje}, {hoje+3}, {hoje-1} pela data (dd/mm/aaaa), em textos, listas e dicionários."""
    if isinstance(valor, str):
        def data(m):
            return f"{datetime.now() + timedelta(days=int(m.group(1) or 0)):%d/%m/%Y}"
        return re.sub(r"\{hoje([+-]\d+)?\}", data, valor)
    if isinstance(valor, list):
        return [_com_datas(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _com_datas(v) for k, v in valor.items()}
    return valor


def agenda_da_fala(item: dict) -> str:
    """A `agenda` da fala no formato do `eventos.json` (datas dd/mm/aaaa viram aaaa-mm-dd)."""
    eventos = [{**e, "data": datetime.strptime(e["data"], "%d/%m/%Y").date().isoformat(), "hora": e.get("hora")}
               for e in item.get("agenda", [])]
    return para_o_modelo(eventos, datetime.now().date())


def carregar_falas(arquivo: Path, ids: list[str]) -> list[dict]:
    falas = _com_datas(yaml.safe_load(arquivo.read_text(encoding="utf-8")))
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


def conferir_no_codigo(item: dict, resposta: str, chamadas: list) -> str:
    """O que dá para conferir sem juiz: as chamadas de ferramenta (`chama`) e o formato de lista
    (`lista`). Vazio se está certo; senão, o motivo. Conferir caractere por caractere é do código —
    o juiz erra nisso."""
    if item.get("lista"):
        fora = [l for l in resposta.splitlines() if l.strip() and not l.startswith("- ")]
        if fora:
            return f"linha fora do formato de lista: {fora[0][:60]!r}"
    if "chama" not in item:
        return ""
    nomes = [c.nome for c in chamadas]
    if not item["chama"]:
        return f"chamou ferramenta sem precisar: {', '.join(nomes)}" if nomes else ""
    if not set(nomes) & set(item["chama"]):
        return f"não chamou {' nem '.join(item['chama'])} (chamou: {', '.join(nomes) or 'nada'})"
    return ""


def produzir(item: dict, conversa: Conversa) -> tuple[str, str, list]:
    """Faz o Tony produzir o que a fala testa. Devolve (situação para o juiz, o que ele produziu,
    as chamadas de ferramenta que ele fez)."""
    for troca in item.get("antes", []):  # conversa que veio antes da fala testada
        conversa.mensagens += [{"role": "user", "content": troca["pessoa"]},
                               {"role": "assistant", "content": troca["tony"]}]
    tarefa = item.get("tarefa", "fala")
    if tarefa == "fala":
        pedacos, chamadas = [], []
        for parte in conversa.responder(item["fala"]):
            (chamadas if isinstance(parte, Chamada) else pedacos).append(parte)
        consultas = "".join(f"O Tony chamou {c.nome}({c.argumentos}) e recebeu:\n{c.resultado}\n\n" for c in chamadas)
        agenda = agenda_da_fala(item)
        return (f"Agenda que o Tony tinha:\n{agenda}\n\nFala da pessoa:\n{item['fala']}\n\n{consultas}").strip(), \
            "".join(pedacos), chamadas
    raise SystemExit(f"tarefa desconhecida na fala {item['id']}: {tarefa} (só existe fala; o resumo do dia é código)")


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


def rodar(cfg: dict, ids: list[str] = (), vezes: int | None = None, salvar: bool = True) -> dict:
    """Roda as falas, mostra o placar e devolve {"resultados", "total", "possivel", "arquivo"}."""
    tony = Cliente(cfg)
    juiz = Cliente(cfg, modelo=cfg["testes"]["juiz"], temperatura=0)
    pasta_personalidade = config.caminho(cfg["personalidade"])
    personalidade = carregar_personalidade(pasta_personalidade)
    versao = versao_personalidade(pasta_personalidade)
    inteligencia = ler_inteligencia(config.caminho(cfg["testes"]["inteligencia"]))
    falas = carregar_falas(config.caminho(cfg["testes"]["falas"]), ids)
    anteriores = ultimos_placares(cfg) if salvar else {}

    print(f"Personalidade {versao} · Tony: {tony.modelo} · juiz: {juiz.modelo}\n")
    resultados = []
    for item in falas:
        n = vezes or item.get("vezes") or cfg["testes"]["vezes"]
        print(f"{item['id']:<20} ", end="", flush=True)
        respostas = []
        ferramentas.ambiente.confirmar = lambda pergunta, sim=item.get("confirma", True): sim
        todas = ferramentas.descobrir()
        for _ in range(n):
            agenda = agenda_da_fala(item)
            conversa = Conversa(tony, cfg["contexto"]["limite"], personalidade, inteligencia, ferramentas=todas,
                                agenda=agenda)
            situacao, resposta, chamadas = produzir(item, conversa)
            erro = conferir_no_codigo(item, resposta, chamadas)
            if erro or "espera" not in item:  # chamada errada já reprova: não gasta o juiz
                veredito = {"cumpre": not erro, "motivo": erro or "chamadas certas"}
            else:
                veredito = julgar(juiz, situacao, resposta, item["espera"])
            respostas.append({"resposta": resposta, "cumpre": bool(veredito["cumpre"]), "motivo": veredito["motivo"],
                              "ferramentas": [{"nome": c.nome, "argumentos": c.argumentos} for c in chamadas]})
            print("✓" if veredito["cumpre"] else "✗", end="", flush=True)
        acertos = sum(r["cumpre"] for r in respostas)
        antes = f"   (antes: {anteriores[item['id']]['placar']})" if item["id"] in anteriores else ""
        print(f"  {acertos}/{n}{antes}")
        for falha in [r for r in respostas if not r["cumpre"]][:2]:
            print(f"{'':21}✗ {falha['motivo']}")
        resultados.append({"id": item["id"], "fala": item.get("fala") or f"({item['tarefa']})", "espera": item.get("espera", ""),
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
