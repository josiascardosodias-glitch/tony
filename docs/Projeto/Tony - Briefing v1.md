---
criado: 2026-10-23
tags: [tony, projeto, briefing, agente, ia]
fonte: própria (conversas com GPT, Claude web e Claude Code)
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Briefing v1 (versão oficial)

> [!abstract] Como usar
> Este é o briefing que vai para o Claude Code dentro de `~/projetos/tony`. Ele substitui o
> [[Tony - Conceito inicial (GPT)]] e o rascunho feito no Claude web. As decisões técnicas, com o
> motivo de cada uma, ficam no `DECISOES.md` do repositório. O andamento fica no [[Tony - Diário de bordo]].

Você vai me ajudar a construir a v1 do Tony, meu agente de IA próprio. Leia tudo antes de agir e
pare para me mostrar o resultado nos pontos marcados com ⏸.

## 1. O que é o Tony

Um agente de terminal em Python que entende linguagem natural e usa ferramentas para responder.
O código é meu, público no GitHub; o modelo de linguagem é um componente trocável.

**A v1 faz uma coisa só, e bem:** responder perguntas sobre a pasta de inteligência do Tony no meu
vault do Obsidian (`My-Brain/08-Tony/Inteligência/`), citando a nota de onde tirou a resposta.

## 2. Decisões fechadas

| Tema | Decisão |
|---|---|
| Nome | **Tony** (pacote, comando e prompt). Sem apelido. |
| Repositório | `~/projetos/tony`, **público** no GitHub |
| Motor | Modelo **na nuvem do Ollama**, chamado pelo Ollama instalado na máquina (mesma API do modelo local). Trocar para um modelo local é mudar uma linha do config. |
| Cliente | Biblioteca nativa `ollama` (não o endpoint `/v1`), isolada em `cliente.py` — o único arquivo que sabe que o Ollama existe. |
| Modelfile | **Não usar.** Prompt, `num_ctx` e temperatura saem do config e vão em cada requisição: uma fonte de verdade só. |
| O que o Tony lê | **Só** `My-Brain/08-Tony/Inteligência/`. Nada mais do vault. Só leitura na v1. |
| Ferramentas | Funções Python com docstring e tipos, uma por arquivo em `tony/ferramentas/`, descobertas sozinhas. A lib `ollama` gera o esquema a partir da função. |
| Saída estruturada | Não na v1. Tool calling para agir; JSON Schema só quando houver extração de dados (v2). |
| Especialistas | Fora da v1. |
| Busca | Textual (palavras-chave) na v1. Embeddings na v1.1. |
| Thinking | Desligado por padrão (configurável). |

## 3. Regras por ser público

O vault é privado e o código é público. Nada que identifique o vault vai para o git:

- `config.exemplo.yaml` vai para o git; `config.local.yaml` (caminho real do vault) fica no `.gitignore`.
- `logs/` e `dados/` ficam no `.gitignore`: contêm trechos das notas.
- Os testes rodam contra notas **falsas** em `exemplos/inteligencia/`, nunca contra o vault real.
- Antes do primeiro push, conferir com `git status` e `git ls-files` que nada disso escapou.

## 4. Estrutura

```
tony/
├── README.md               # instalar, configurar, adicionar ferramenta
├── DECISOES.md             # decisão, motivo, alternativa descartada
├── pyproject.toml          # pip install -e . → comando `tony`
├── config.exemplo.yaml     # modelo, num_ctx, temperatura, keep_alive, pasta liberada
├── prompts/
│   └── sistema.md          # quem é o Tony (editável sem mexer em código)
├── tony/
│   ├── main.py             # loop do terminal (/sair, /ruim)
│   ├── config.py           # junta config.exemplo + config.local
│   ├── cliente.py          # conversa com o Ollama; checa se o modelo suporta tools ao iniciar
│   ├── orquestrador.py     # laço de tool calling, com limite de voltas
│   ├── registro.py         # importa tony/ferramentas/*.py e entrega as funções
│   ├── acesso.py           # trava de caminhos: nada fora da pasta liberada (nem com ../)
│   └── ferramentas/
│       ├── buscar_no_cerebro.py   # busca por palavras, devolve notas + trechos
│       └── ler_nota.py            # lê uma nota inteira da pasta liberada
├── exemplos/inteligencia/  # 3–5 notas falsas para teste
├── testes/
│   ├── perguntas.yaml      # pergunta + o que a resposta precisa conter
│   └── rodar.py            # roda as perguntas e mostra acertos
├── logs/                   # (gitignored) um .jsonl por sessão
└── dados/                  # (gitignored) índice da v1.1
```

## 5. Comportamento esperado

- A data de hoje entra no prompt de sistema ao iniciar a sessão (não precisa de ferramenta).
- Resposta sempre cita a nota usada. Sem nota que responda, o Tony diz que não encontrou — não inventa.
- O laço de ferramentas tem limite (ex.: 5 voltas) e trata erro de ferramenta devolvendo a mensagem ao modelo.
- Ferramenta retorna texto curto: trechos, não notas gigantes. Corte com aviso, nunca em silêncio.
- Cada turno vai para `logs/<data-hora>.jsonl`: pergunta, chamadas de ferramenta, resposta, modelo, tempo.
- `/ruim` marca o último turno como erro no log (material para melhorar o prompt).

## 6. Ordem de trabalho

1. **Ambiente:** versão do Python, instalar o Ollama, `ollama signin`, listar os modelos de nuvem
   disponíveis no plano gratuito e propor 2 ou 3 com suporte a tools (prós, contras, limites). ⏸
2. **Esqueleto:** estrutura, `pyproject.toml`, configs, `sistema.md`, `cliente.py`, `registro.py`,
   `orquestrador.py`, `main.py` e uma ferramenta de teste trivial. Testar que conversa e chama a ferramenta. ⏸
3. **Ferramentas reais:** `acesso.py`, `buscar_no_cerebro`, `ler_nota`, notas de exemplo.
4. **Testes:** `perguntas.yaml` com ~10 perguntas sobre as notas de exemplo e o `rodar.py`.
5. **Documentar:** README curto e `DECISOES.md` atualizado.
6. **Publicar:** `git init`, conferência do que vai para o git e criação do repositório público. ⏸

## 7. Depois da v1

- **v1.1** — embeddings (`nomic-embed-text` local, índice em `numpy` + `.npz`), notas divididas por título antes de indexar; comparar com a busca textual usando os mesmos testes.
- **v2** — primeira ferramenta de escrita (`anotar_na_inteligencia`), com confirmação no terminal; especialistas como `.yaml` (outro prompt, mesmo modelo); saída estruturada para extração.
- **v3** — fontes externas (e-mail da escola), agendamento diário.
- **Horizonte** — o que o Tony consulta sempre sobe para o prompt; fine-tuning só se os logs mostrarem que prompt e busca não bastam (e em GPU na nuvem).

## 8. Como trabalhar comigo

- Sou desenvolvedor júnior: explique as decisões importantes de forma direta, com o porquê.
- Soluções simples; nada de LangChain ou similares sem me perguntar antes.
- Se algo aqui não fizer sentido no meu ambiente, diga e proponha alternativa.
- Toda decisão nova vai para o `DECISOES.md`.

## Relacionado

- [[Tony - Conceito inicial (GPT)]] — a primeira ideia, de onde saíram o nome e o caso do e-mail
- [[Tony - Diário de bordo]] — o que já foi feito e o que travou
- [[Tony - Sobre o Josias]] — exemplo do que vai na pasta que o Tony lê
