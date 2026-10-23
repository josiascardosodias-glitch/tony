---
criado: 2026-10-23
tags: [tony, projeto, diario]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Diário de bordo

Uma entrada por sessão de trabalho, a mais recente no topo: o que foi feito, o que travou, o que aprendi.

## 2026-10-23 — v0.1.0 publicada

**Feito**
- Corrigida a terceira pessoa: antes, 8 de 8 respostas diziam "o projeto do Josias"; depois de mudar o
  `identidade.md`, 8 de 8 em segunda pessoa ("você me criou", "o seu projeto"). Commit `68c6d83`.
- Licença MIT, `CHANGELOG.md` e link do repositório no README.
- Publicado em [github.com/josiascardosodias-glitch/tony](https://github.com/josiascardosodias-glitch/tony),
  com a tag e a release `v0.1.0`. Conferido antes que config local, logs e resumos ficaram fora do git.
- Documentação no vault: [[Tony - Como usar e evoluir]], mapa com o estado atual e o briefing com o andamento das etapas.
- Roadmap: [[Tony - Próximas atualizações]] no vault (com a v0.2 detalhada para discutir) e `ROADMAP.md` no repositório.

**Pendente**
- Conversar de verdade e marcar `/bom` e `/ruim`.
- v0.2: etapa 4 (revisão pelas marcações) e etapa 5 (falas de teste).

**Aprendi**
- Para corrigir o jeito do modelo: reproduzir o erro várias vezes, mudar o texto e medir de novo do
  mesmo jeito. Uma resposta só não prova nada, porque com temperatura 0,7 cada uma sai diferente.
- O modelo não deduz relações óbvias para a gente: saber "quem me criou" e "com quem estou falando" não
  basta, é preciso dizer que é a mesma pessoa.
- O `gh repo create --push` usa a credencial do `gh`, mas um `git push` depois não. Dá para usar o `gh`
  como credencial num comando só: `git -c credential.helper='!gh auth git-credential' push`.

## 2026-10-23 — Mudança de foco e início da construção

**Feito**
- A v1 deixou de ser "perguntas sobre o vault" e virou **só diálogo**: o Tony não precisa ser útil
  logo, precisa conversar bem e evoluir. Ferramentas e busca foram para a v2 ([[Tony - Briefing v1]]).
- Etapa 1 do briefing pronta em `~/projetos/tony`: personalidade em 3 arquivos, conversa com streaming,
  memória (Inteligência + resumo da última conversa), resumo automático quando o contexto enche,
  log `.jsonl` com `/bom` e `/ruim`, comandos `/nova` e `/prompt`. Testado sem o modelo (com um modelo falso).

- Etapa 2 pronta: Ollama 0.40.10 instalado, login pelo GitHub. Comparei 3 modelos de nuvem com a
  personalidade real; escolhido o `gemma4:31b-cloud` (gratuito, ~1 s, tom mais natural).
  O `deepseek-v4.1-flash` só funciona no plano Pro. Primeiro commit: `8c3b81a`.
- **Primeiro ponto a evoluir:** o Tony disse "sou a primeira versão do projeto do Josias" falando
  com o próprio Josias — não ligou o criador a quem está conversando.

**Pendente**
- Conversar com o Tony (`cd ~/projetos/tony && uv run tony`) e marcar `/bom` e `/ruim`.
- Etapa 3 (memória) já está quase toda no esqueleto; falta testar o resumo entre sessões de verdade.

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
