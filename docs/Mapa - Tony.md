---
tags: [mapa, tony, projeto, ia]
---

# 🗺️ Tony

O Tony é o meu agente de IA próprio, construído do zero em Python. Esta pasta é a `docs/` do
repositório do código, e aparece no vault como `My-Brain/Tony/`: um mundo próprio, com regras
próprias (o `CLAUDE.md` desta pasta) e nenhum conteúdo cruzando com as outras pastas. Este mapa é o
ponto de entrada.

> [!success] Em produção: v3.0.0 (2026-10-26), na `main`
> Conversa, `tony testar` (placar 131/132), `tony dia` com notificação diária às 08:00.
> Modelo: `gemma4:31b-cloud` (Ollama, plano gratuito).
> Código: [github.com/josiascardosodias-glitch/tony](https://github.com/josiascardosodias-glitch/tony) (público, MIT) ·
> local em `~/projetos/tony` · rodar com `uv run tony`.

> [!important] v4 em construção na branch `develop` (desde 2026-11-03)
> O Tony vira assistente de e-mail: datas dos e-mails → agenda "Tony" no Google → consulta pelo
> Telegram, com o mínimo de IA. Regras de branch e de produção em [[Tony - Regras do projeto]].

## Projeto — o que nós planejamos (o Tony não lê)

0. [[Tony - Regras do projeto]] — branches `main`/`develop`, produção, IA no mínimo; ler antes de qualquer atualização
1. [[Tony - Como usar e evoluir]] — comandos, onde fica cada coisa e o ciclo de testes
2. [[Tony - Próximas atualizações]] — roadmap vivo: o plano da v4, dúvidas e ideias soltas
3. [[Tony - Briefing v1]] — histórico: o plano da v1
4. [[Tony - Diário de bordo]] — o que foi feito, travou e aprendi em cada sessão
5. [[Tony - Conceito inicial (GPT)]] — histórico: a primeira ideia, substituída pelo briefing

No repositório do código: `DECISOES.md` (cada decisão com o porquê), `CHANGELOG.md` (o que mudou em
cada versão) e `ROADMAP.md` (resumo público).

## Inteligência — o que o Tony lê

A única pasta que o Tony lê (`docs/Inteligência/`, apontada no `config.local.yaml`). Tudo aqui vai
para o modelo na nuvem: só entra o que pode sair da máquina. As notas daqui **não sobem para o
GitHub**: o repositório guarda só os modelos vazios em `modelos/`, e cada pessoa preenche os seus. Uma nota = um assunto, com o prefixo
`Tony - `. Na v4, as ferramentas das notas saem e esta pasta deixa de ser lida durante a conversa.

1. [[Tony - Sobre o Josias]] — quem eu sou e como prefiro as respostas
2. [[Tony - Lembretes]] — escrita pelo `/lembrar`, uma linha por fato confirmado
3. Modelos: [[Tony - Sobre mim (modelo)]] e [[Tony - Lembretes (modelo)]]

## Histórico

As notas vieram do Cofre em 2026-11-03 com o histórico do Git (`git log -- docs` mostra desde
2026-10-22). Duas notas antigas que viraram notas do Tony só existem no histórico, em
`docs/historico/`.
