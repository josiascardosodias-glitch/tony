---
criado: 2026-11-03
tags: [tony, projeto, regras]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Regras do projeto

As regras de negócio do Tony, que valem para qualquer atualização a partir da v4. **Toda vez que o
estado e a estrutura do Tony forem levantados antes de uma atualização, esta nota entra junto.**

## 1. A v4 é produção

A partir da v4.0.0, a `main` é a versão em uso de verdade. Uma versão só vira produção quando passa
nos testes (ver a regra 2).

## 2. Duas branches: `main` e `develop`

- **`main`**: a principal, só produção. Ninguém trabalha direto nela. As releases e tags (`v4.0.0`,
  `v4.1.0`…) saem só daqui.
- **`develop`**: a secundária. Toda feature, correção ou mudança de documentação é feita e
  commitada aqui.
- **Para levar `develop` à `main`**, as três condições precisam valer:
  1. `uv run python -m unittest discover testes` passa inteiro;
  2. `uv run tony testar` não piora o placar em relação à `main`;
  3. não há conflito com a `main`: `git merge-tree --write-tree main develop` termina sem conflito
     (ou um `git merge main` dentro da `develop` sai limpo).
- Só então: `git switch main && git merge --no-ff develop`, tag e release. Depois, a `develop` volta a
  acompanhar a `main` (`git switch develop && git merge main`).
- **A produção roda de uma pasta presa à `main`:** `~/projetos/tony-producao` (`git worktree`). O
  timer do resumo do dia roda de lá. Depois de um merge, `git pull` nessa pasta. Nunca agende o timer
  da pasta de trabalho, que está na `develop`.
- Push só com pedido. Por HTTPS:
  `git -c credential.helper= -c credential.helper="!gh auth git-credential" push origin develop`.

## 3. IA no mínimo

O Tony vai rodar várias vezes por dia, o mês inteiro. O que um script, uma API ou uma ferramenta
consegue fazer não passa pela IA: buscar e-mails, filtrar, achar datas, gravar na agenda e montar
respostas de agenda são código. O modelo fica como **gerenciador**, para o que o código não resolve
(uma pergunta livre no Telegram, um caso ambíguo).

- Antes de pôr a IA em qualquer passo, pesquise se um script ou uma API resolve e anote o resultado
  no `DECISOES.md`.
- A IA nunca lê o e-mail inteiro. Quando precisa, recebe só título, data e a frase da data.
- O contraexemplo é um fluxo em que a IA faz o que um script faria: cada rodada gasta muito, e o
  Tony roda dezenas de vezes por dia.

## 4. Dados e segredos ficam no PC

- O repositório é **público**: e-mails, eventos, logs e configuração pessoal ficam em `dados/`,
  `logs/` e `config.local.yaml`, fora do git.
- Senhas e tokens (OAuth do Google, bot do Telegram) ficam em `~/.config/tony/` com `chmod 600`.
- A lista de bloqueados (`bloqueados.json`) é local: e-mail de remetente bloqueado não é baixado nem
  lido.
- **Informação pessoal não sobe.** A documentação (`docs/`) é pública junto com o código; o que é
  pessoal fica nas notas de `docs/Inteligência/`, fora do git pelo `.gitignore`, e o repositório guarda
  só os modelos vazios (`docs/Inteligência/modelos/`). Antes de cada commit, confira com
  `git status` que nenhuma nota pessoal entrou.

## Como levantar o estado antes de uma atualização

1. Esta nota.
2. [[Tony - Próximas atualizações]]: o que está planejado e o que ficou pendente.
3. [[Tony - Diário de bordo]]: a última entrada.
4. No repositório: `git branch -a`, `git worktree list`, `git log --oneline main..develop` (o que está
   na `develop` e ainda não foi para produção), `git status` e o `ROADMAP.md`.
5. O timer: `grep WorkingDirectory ~/.config/systemd/user/tony-dia.service` tem que apontar para a
   pasta de produção.

## Relacionado

- [[Tony - Próximas atualizações]] — o plano da v4, que segue estas regras
- [[Tony - Como usar e evoluir]] — comandos e o ciclo de testes que a regra 2 usa
- [[Tony - Diário de bordo]] — onde cada sessão registra o que fez
