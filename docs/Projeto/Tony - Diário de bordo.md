---
criado: 2026-10-23
tags: [tony, projeto, diario]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Diário de bordo

Uma entrada por sessão de trabalho, a mais recente no topo: o que foi feito, o que travou, o que aprendi.

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
