---
criado: 2026-10-23
tags: [tony, projeto, diario]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Diário de bordo

Uma entrada por sessão de trabalho, a mais recente no topo: o que foi feito, o que travou, o que aprendi.

## 2026-10-23 — Mudança de foco e início da construção

**Feito**
- A v1 deixou de ser "perguntas sobre o vault" e virou **só diálogo**: o Tony não precisa ser útil
  logo, precisa conversar bem e evoluir. Ferramentas e busca foram para a v2 ([[Tony - Briefing v1]]).
- Etapa 1 do briefing pronta em `~/projetos/tony`: personalidade em 3 arquivos, conversa com streaming,
  memória (Inteligência + resumo da última conversa), resumo automático quando o contexto enche,
  log `.jsonl` com `/bom` e `/ruim`, comandos `/nova` e `/prompt`. Testado sem o modelo (com um modelo falso).

**Pendente**
- Etapa 2: instalar o Ollama (`curl -fsSL https://ollama.com/install.sh | sh`), `ollama signin` e escolher o modelo de nuvem.
- Primeiro commit do repositório.

**Aprendi**
- O Python do sistema (Ubuntu) vem sem `venv` e `pip`; o `uv` cria o ambiente sem precisar de `sudo`.
- Com `stream=True`, a lib `ollama` não converte falha de rede em `ConnectionError`: o erro do `httpx`
  escapa direto. Só apareceu porque testei com o Ollama desligado — testar o caminho de erro vale a pena.
- Um gerador (função com `yield`) pode desfazer o próprio estado num `except`: se a resposta falha no
  meio, a fala do usuário sai do histórico e a conversa não fica com pergunta sem resposta.

## 2026-10-23 — Definição da v1

**Feito**
- Análise do [[Tony - Conceito inicial (GPT)]] e do rascunho feito no Claude web.
- Hardware conferido: 7,5 GB de RAM, GPU Intel integrada, sem Ollama. Modelo local fica limitado a 3–4B na CPU.
- Decisões fechadas e escritas no [[Tony - Briefing v1]]: nome Tony, modelo na nuvem do Ollama,
  repositório público em `~/projetos/tony`, v1 = perguntas sobre a pasta `08-Tony/Inteligência/`.
- Criada a pasta `08-Tony/` no vault, separada de `07-Projetos/` (que é do vault-sync).

**Pendente**
- Ler a política de privacidade do Ollama sobre os modelos de nuvem (não confirmei retenção de dados).
- Escolher a licença do repositório (sugestão: MIT).
- Revisar e completar [[Tony - Sobre o Josias]].

**Aprendi**
- Um agente é um laço: o modelo pede uma ferramenta, o código executa e devolve, até o modelo responder sem pedir nada.
- O endpoint `/v1` (compatível com OpenAI) do Ollama não cobre `num_ctx` e `keep_alive`; a lib nativa cobre.
