---
tags: [mapa, tony, projeto, ia]
---

# 🗺️ Tony

O Tony é o meu agente de IA próprio, construído do zero em Python para aprender como agentes funcionam.
Esta pasta (`08-Tony/`) é escrita à mão — o vault-sync não mexe aqui.

> [!success] Estado atual: v3.0.0 publicada (2026-10-26)
> Conversa, memória, `/lembrar`, `/bom`/`/ruim`, `tony testar` (placar 131/132) e `tony revisar`.
> v2: ferramentas sobre a Inteligência (listar, ler, buscar, lembrar). v3: `ler_emails` (falta a senha
> de app para testar com a caixa real), `tony dia` e notificação diária às 08:00. Testes de código com
> `uv run python -m unittest discover testes`.
> Modelo: `gemma4:31b-cloud` (Ollama, plano gratuito).
> Código: [github.com/josiascardosodias-glitch/tony](https://github.com/josiascardosodias-glitch/tony) (público, MIT) ·
> local em `~/projetos/tony` · rodar com `uv run tony`.

> [!important] v4 em construção na branch `develop` (desde 2026-11-03)
> O Tony vira assistente de e-mail: datas dos e-mails → agenda "Tony" no Google → consulta pelo
> Telegram, com o mínimo de IA. Regras de branch e de produção em [[Tony - Regras do projeto]].

## Projeto — o que nós planejamos (o Tony não lê)

0. [[Tony - Regras do projeto]] — branches `main`/`develop`, produção, IA no mínimo; ler antes de qualquer atualização
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
