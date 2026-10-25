---
tags: [mapa, tony, projeto, ia]
---

# 🗺️ Tony

O Tony é o meu agente de IA próprio, construído do zero em Python para aprender como agentes funcionam.
Esta pasta (`08-Tony/`) é escrita à mão — o vault-sync não mexe aqui.

> [!success] Estado atual: v1.0.0 (2026-10-24) — a v1 completa
> Só conversa: personalidade versionada, memória (última conversa + conversas antigas consolidadas),
> `/lembrar`, `/bom`/`/ruim`; `tony testar` (placar 76/76) e `tony revisar` (uma mudança por rodada).
> Próxima versão: v2 — ferramentas.
> Modelo: `gemma4:31b-cloud` (Ollama, plano gratuito).
> Código: [github.com/josiascardosodias-glitch/tony](https://github.com/josiascardosodias-glitch/tony) (público, MIT) ·
> local em `~/projetos/tony` · rodar com `uv run tony`.

## Projeto — o que nós planejamos (o Tony não lê)

1. [[Tony - Como usar e evoluir]] — comandos, onde fica cada coisa e o ciclo para melhorar o diálogo
2. [[Tony - Próximas atualizações]] — roadmap vivo: a próxima versão detalhada, dúvidas e ideias soltas
3. [[Tony - Briefing v1]] — o plano da v1: decisões, estrutura e etapas
4. [[Tony - Diário de bordo]] — o que foi feito, travou e aprendi em cada sessão
5. [[Tony - Conceito inicial (GPT)]] — histórico: a primeira ideia, substituída pelo briefing

No repositório: `DECISOES.md` (cada decisão com o porquê), `CHANGELOG.md` (o que mudou em cada versão)
e `ROADMAP.md` (resumo público das próximas versões).

## Inteligência — o que o Tony lê

A única pasta do vault liberada para o Tony (`08-Tony/Inteligência/`). Na v1, todas as notas daqui
entram no prompt no início de cada conversa: é a memória dele sobre mim. Tudo aqui vai para o modelo
na nuvem: só entra o que pode sair da máquina. Uma nota = um assunto, com o prefixo `Tony - `.

1. [[Tony - Sobre o Josias]] — quem eu sou e como prefiro as respostas

A nota `Tony - Lembretes` aparece aqui no primeiro `/lembrar`: é escrita pelo Tony, uma linha por
fato que você confirmou (pode editar ou apagar).

## Conexões com outros mapas

- [[Mapa - Claude Code e IA]] — as ferramentas de IA que já uso e que inspiram o Tony
- [[Mapa - Projetos]] — os outros projetos pessoais

↩ [[Início]]
