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

> [!note] Mudança de foco (2026-10-23)
> A primeira versão deste briefing fazia o Tony responder perguntas sobre o vault com ferramentas.
> A v1 agora é **só diálogo**: o Tony não precisa ser útil logo de cara, precisa conversar bem e
> melhorar a cada conversa. Ferramentas e busca passaram para a v2.

## 1. O que é o Tony

Um agente de terminal em Python, meu, com código público no GitHub. O modelo de linguagem é um
componente trocável; o que é do Tony é a personalidade, a memória e a forma como ele evolui.

**A v1 faz uma coisa só:** conversar — e ficar melhor nisso com o uso.

## 2. O que "evoluir o diálogo" quer dizer na v1

| Peça | Como funciona |
|---|---|
| **Personalidade em arquivos** | `personalidade/*.md` (identidade, tom, regras) no repositório. Mudar o jeito do Tony é editar texto, e o git guarda a história de cada mudança. |
| **Memória sobre mim** | As notas de `My-Brain/08-Tony/Inteligência/` entram no prompt no início de cada conversa (sem busca: são poucas). |
| **Continuidade** | Ao sair, o Tony resume a conversa; a próxima começa sabendo onde a anterior parou. |
| **Conversa longa** | Quando o contexto enche, as mensagens antigas viram um resumo — nunca são cortadas em silêncio. |
| **Feedback** | `/bom` e `/ruim <motivo>` marcam a última resposta no log. |
| **Revisão** (etapa 4) | O Tony lê os turnos marcados e propõe mudanças na personalidade; eu aceito ou não. |
| **Falas de teste** (etapa 5) | Situações fixas de conversa, rodadas a cada mudança de personalidade ou de modelo, para comparar antes e depois. |

## 3. Decisões fechadas

| Tema | Decisão |
|---|---|
| Nome | **Tony** (pacote, comando e prompt). Sem apelido. |
| Repositório | `~/projetos/tony`, **público** em [github.com/josiascardosodias-glitch/tony](https://github.com/josiascardosodias-glitch/tony), licença MIT |
| Motor | `gemma4:31b-cloud` **na nuvem do Ollama** (plano gratuito), chamado pelo Ollama instalado na máquina. Trocar para local (ex.: `gemma4:e4b`) é mudar uma linha do config. |
| Cliente | Biblioteca nativa `ollama`, isolada em `cliente.py`. Sem Modelfile: tudo sai do config. |
| Ambiente Python | `uv` (o Python do sistema não tem `venv` nem `pip`) |
| Ferramentas, busca, especialistas | **Fora da v1.** Entram na v2. |
| Resposta | Em streaming (o texto aparece enquanto é gerado) |

## 4. Regras por ser público

- Personalidade (`personalidade/`) é pública: é o "jeito" do Tony, não dado meu.
- O que é meu fica fora do git: `config.local.yaml` (caminho do vault), `logs/` e `dados/` (resumos).
- Antes do primeiro push, conferir com `git ls-files` que nada disso escapou.

## 5. Estrutura

```
tony/
├── README.md · DECISOES.md · CHANGELOG.md · LICENSE · pyproject.toml · .gitignore
├── config.exemplo.yaml      # modelo, temperatura, contexto, pasta da Inteligência
├── personalidade/
│   ├── identidade.md        # quem o Tony é
│   ├── tom.md               # como ele fala
│   └── regras.md            # o que ele sempre / nunca faz
├── tony/
│   ├── main.py              # loop do terminal e comandos /
│   ├── config.py            # junta config.exemplo + config.local
│   ├── cliente.py           # único arquivo que conhece o Ollama
│   ├── conversa.py          # histórico, prompt de sistema, resumo quando o contexto enche
│   ├── memoria.py           # lê a Inteligência e o resumo da última conversa
│   └── registro.py          # log .jsonl por sessão + marcações /bom /ruim
├── logs/                    # (gitignored)
└── dados/                   # (gitignored) resumos das conversas
```

Comandos no chat: `/sair`, `/nova`, `/bom`, `/ruim <motivo>`, `/prompt` (mostra o prompt de sistema montado), `/ajuda`.

## 6. Ordem de trabalho

"v1" é o plano deste briefing inteiro. As entregas no GitHub vão subindo em `v0.x` até ele estar
completo, que vira a `v1.0`.

| # | Etapa | Estado |
|---|---|---|
| 1 | **Esqueleto que conversa** — estrutura, config, personalidade inicial, streaming, logs, `/bom` e `/ruim` | ✅ v0.1.0 |
| 2 | **Motor** — Ollama, `ollama signin`, modelo de nuvem | ✅ v0.1.0 (`gemma4:31b-cloud`) |
| 3 | **Memória** — Inteligência no prompt, resumo ao sair, resumo quando o contexto enche | 🟡 código na v0.1.0; falta testar o resumo entre sessões com o modelo real |
| 4 | **Revisão** — comando que lê as marcações e propõe mudanças na personalidade ⏸ | ⬜ próxima (v0.2) |
| 5 | **Falas de teste** — `testes/falas.yaml` e um script que roda e salva as respostas para comparar | ⬜ v0.2 |
| 6 | **Publicar** — conferência do git e repositório público | ✅ v0.1.0 (adiantada) |

## 7. Depois da v1

- **v2** — ferramentas (laço de tool calling, descoberta automática), começando por ler a Inteligência sob demanda.
- **v2.x** — busca no vault (textual, depois embeddings), primeira ferramenta de escrita com confirmação.
- **v3** — fontes externas (e-mail da escola), agendamento.
- **Horizonte** — fine-tuning só se os logs mostrarem que personalidade e memória em texto não bastam.

## 8. Como trabalhar comigo

- Sou desenvolvedor júnior: explique as decisões importantes de forma direta, com o porquê.
- Este projeto existe para eu ganhar conhecimento e experiência: prefira código que eu consiga ler a atalhos mágicos.
- Nada de LangChain ou similares sem me perguntar antes.
- Toda decisão nova vai para o `DECISOES.md`.

## Relacionado

- [[Tony - Conceito inicial (GPT)]] — a primeira ideia, de onde saiu o nome
- [[Tony - Diário de bordo]] — o que já foi feito e o que travou
- [[Tony - Como usar e evoluir]] — o guia de uso e o ciclo de melhoria do diálogo
- [[Tony - Sobre o Josias]] — o que o Tony sabe sobre mim (entra no prompt)
