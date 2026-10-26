"""Falas de teste: roda falas fixas contra a personalidade atual e um modelo juiz dá o placar.

Cada fala roda várias vezes (a resposta varia a cada vez), sempre numa conversa nova e com a
Inteligência de exemplo; resumo da última conversa e memória antiga só entram quando a fala traz os
seus (`ultima_conversa`, `memoria`) — assim o placar só muda quando a personalidade ou o modelo mudam.

Além de respostas, dá para testar a memória: `tarefa: resumo` julga o resumo que o Tony faz da
conversa `antes`, e `tarefa: memoria` julga a memória depois de esse resumo entrar nela.

Ferramentas: rodam sobre a Inteligência de exemplo, e a escrita (`lembrar`) vai para uma pasta
temporária, com a confirmação "sim" (ou "não", com `confirma: false`). `chama: [a, b]` exige que ele chame ao menos uma delas;
`chama: []`, que não chame nenhuma; `lista: true`, que toda linha comece com "- " — conferidos no
código, sem juiz. `indice: true` põe no prompt só a
lista das notas (como quando elas não cabem), para testar a leitura sob demanda.

E-mail: `emails` (lista de {de, assunto, data, texto}) é a caixa de exemplo da fala; sem ela, o
e-mail fica desligado. `tarefa: dia` julga o resumo do dia. Em qualquer texto, `{hoje+3}` vira a data
de daqui a 3 dias (dd/mm/aaaa), para os testes não vencerem.
"""

import json
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from . import config, ferramentas
from .cliente import Chamada, Cliente
from .conversa import DIAS, TEMPERATURA_MEMORIA, Conversa, consolidar_memoria
from .dia import pedido_do_dia
from .memoria import carregar_personalidade, inteligencia_para_prompt, versao_personalidade

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


def produzir(item: dict, conversa: Conversa, organizador: Cliente) -> tuple[str, str, list]:
    """Faz o Tony produzir o que a fala testa. Devolve (situação para o juiz, o que ele produziu,
    as chamadas de ferramenta que ele fez)."""
    for troca in item.get("antes", []):  # conversa que veio antes da fala testada
        conversa.mensagens += [{"role": "user", "content": troca["pessoa"]},
                               {"role": "assistant", "content": troca["tony"]}]
    contexto = ""
    if item.get("memoria"):
        contexto += f"Memória antiga do Tony:\n{item['memoria']}\n\n"
    if item.get("ultima_conversa"):
        contexto += f"Resumo da última conversa, que o Tony tinha:\n{item['ultima_conversa']}\n\n"
    tarefa = item.get("tarefa", "fala")
    if tarefa == "dia":
        hoje = datetime.now()
        emails = item.get("emails")
        resumo = "".join(p for p in conversa.responder(pedido_do_dia(emails, hoje)) if isinstance(p, str))
        caixa = ("(e-mail não configurado)" if emails is None else
                 "\n".join(f"- [{m['data']}] {m['assunto']}: {m['texto']}" for m in emails) or "(nenhum)")
        return (f"{contexto}Hoje é {DIAS[hoje.weekday()]}, {hoje:%d/%m/%Y}. O Tony escreveu sozinho a notificação "
                f"que abre o dia da pessoa. E-mails que ele tinha:\n{caixa}").strip(), resumo.strip(), []
    if tarefa == "fala":
        pedacos, chamadas = [], []
        for parte in conversa.responder(item["fala"]):
            (chamadas if isinstance(parte, Chamada) else pedacos).append(parte)
        consultas = "".join(f"O Tony chamou {c.nome}({c.argumentos}) e recebeu:\n{c.resultado}\n\n" for c in chamadas)
        return f"{contexto}Fala da pessoa:\n{item['fala']}\n\n{consultas}".strip(), "".join(pedacos), chamadas
    if item.get("resumo"):  # resumo fixo: testa só a consolidação, sem a variação do resumo
        situacao, resumo = contexto.strip(), item["resumo"]
    else:
        situacao = f"{contexto}Conversa:\n{conversa.transcricao(conversa.mensagens)}"
        resumo = conversa.resumir_para_proxima()
    if tarefa == "resumo":
        return situacao, resumo, []
    if tarefa == "memoria":
        hoje = datetime.now()
        return (f"{situacao}\n\nA conversa foi em {DIAS[hoje.weekday()]}, {hoje:%d/%m/%Y}. Resumo que o Tony fez dela:\n{resumo}",
                consolidar_memoria(organizador, item.get("memoria", ""), resumo, hoje), [])
    raise SystemExit(f"tarefa desconhecida na fala {item['id']}: {tarefa} (use fala, resumo, memoria ou dia)")


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
    pasta_inteligencia = config.caminho(cfg["testes"]["inteligencia"])
    inteiras = inteligencia_para_prompt(pasta_inteligencia, cfg["memoria"]["inteligencia_inteira_ate"])
    so_lista = inteligencia_para_prompt(pasta_inteligencia, 0)
    caixa = tempfile.TemporaryDirectory()  # onde o `lembrar` dos testes escreve; some no fim
    ferramentas.ambiente.inteligencia = pasta_inteligencia
    ferramentas.ambiente.lembretes = Path(caixa.name) / "Tony - Lembretes.md"
    if falas is None:
        falas = carregar_falas(config.caminho(cfg["testes"]["falas"]), ids)
    anteriores = ultimos_placares(cfg) if salvar else {}

    print(f"Personalidade {versao} · Tony: {tony.modelo} · juiz: {juiz.modelo}\n")
    resultados = []
    for item in falas:
        n = vezes or item.get("vezes") or cfg["testes"]["vezes"]
        print(f"{item['id']:<20} ", end="", flush=True)
        respostas = []
        ferramentas.ambiente.confirmar = lambda pergunta, sim=item.get("confirma", True): sim
        ferramentas.ambiente.caixa_de_email = (lambda dias, caixa=item["emails"]: caixa) if "emails" in item else None
        todas = ferramentas.descobrir()
        for _ in range(n):
            conversa = Conversa(tony, cfg["contexto"]["limite"], personalidade,
                                so_lista if item.get("indice") else inteiras,
                                ultima_conversa=item.get("ultima_conversa", ""), memoria=item.get("memoria", ""),
                                ferramentas=todas)
            situacao, resposta, chamadas = produzir(item, conversa, organizador)
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
    caixa.cleanup()
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
