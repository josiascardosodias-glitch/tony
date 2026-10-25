---
criado: 2026-10-23
tags: [tony, projeto, diario]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Diário de bordo

Uma entrada por sessão de trabalho, a mais recente no topo: o que foi feito, o que travou, o que aprendi.

## 2026-10-24 — Primeira conversa real: o Claude treinou o Tony

**Feito**
- O Claude conversou com o Tony de verdade (`uv run tony`, dados reais), apresentando-se como Claude,
  e marcou 10 respostas: 6 `/bom`, 4 `/ruim`. Usou `/lembrar` com um fato do seu Planejamento de
  Estudos (NotebookLM + exercícios gerados por LLM) e testou continuidade com `/nova`.
- Achados e correções, cada um virando fala de teste conferida antes (falha) e depois (passa):
  - **Memória trocava quem disse o quê**: "eu não tenho acesso a arquivos" (o Tony) virou "o usuário
    não possui acesso". Consolidação corrigida; `memoria-quem` 2/6 → 6/6. Memória real refeita.
  - **"Você me criou" para quem disse que não é o Josias.** Primeira proposta real do `tony revisar`,
    aceita: `outra-pessoa` 0/6 → 6/6.
  - **Em cima do muro** diante de ideia ruim: `discorda` 0/8 → 8/8 com a regra "tenha opinião". A
    proposta do revisor para isso foi testada e **desfeita** (0/4 na fala marcada).
  - **Pergunta de praxe no fim** ("ficou claro?"): era a raiz de três falhas, inclusive puxar o projeto
    antigo. Regra no `tom.md`: 8/8 nas cinco falas ligadas.
- Placar: **76/76** (19 falas × 4), duas rodadas seguidas. Conversa de verificação no fim: lembrou as
  duas conversas, discordou de cara de "pular os testes", explicou callback sem pergunta no fim.
- Commits `a710386`, `68f0230`, `9ef433d`, `444261d` — **locais, ainda sem push** (no `CHANGELOG.md`
  como "Não publicado").

**Pendente**
- **Você** conversar com ele — até agora só o Claude conversou. A memória atual registra que "o Tony
  está sendo ajudado pelo Claude"; edite `dados/memoria.md` se não quiser isso lá.
- Decidir se fecha a v1.0 agora ou depois do seu uso.

**Aprendi**
- O revisor acerta o diagnóstico mais do que a mudança: das três propostas, uma ficou, uma repetia uma
  regra existente e uma não resolveu. "Aceitar não é manter" pagou a conta.
- O motivo do `/ruim` vira o critério do teste: "depois pergunte se quiser" fez o juiz exigir uma
  pergunta. Escreva o motivo como o defeito, não como a receita.
- Uma regra nova pode piorar outra fala por um caminho indireto (a opinião trouxe uma pergunta que
  puxava assunto velho). Rodar a bateria inteira, não só a fala da mudança.

## 2026-10-24 — v0.3.0 publicada: memória

**Feito**
- Decidido: **memória acumulada** (`dados/memoria.md`, até 40 fatos com data) em vez dos N últimos
  resumos ou de um resumo por semana; e **`/lembrar` com confirmação**, gravando em
  `Tony - Lembretes.md` na Inteligência (a primeira escrita do Tony no vault).
- Quando um resumo deixa de ser o último, ele é consolidado na memória. A memória marca até qual
  resumo já entrou: se a consolidação falhar, nada se perde.
- Sete falas de teste de memória: lembra a pendência, não inventa, não puxa assunto velho, lembra a
  memória antiga, resumo fiel, consolidação e datas. Placar: **55/56** (14 falas × 4).
- Simulei três conversas seguidas numa pasta temporária: a terceira lembrou o que foi decidido na
  primeira, com a data certa da prova.
- Publicado: tag e release `v0.3.0` (commit `5338cec`).

**Pendente**
- **Conversar de verdade** por alguns dias, marcando `/bom` e `/ruim`, e rodar o `tony revisar`
  com marcações reais. Só depois disso sai a v1.0 (decidido hoje: não lançar "completa" sem uso real).
- A falha que sobrou: `sem-bajulacao` abriu uma vez com "É um clássico para quem está aprendendo".

**Aprendi**
- **O modelo erra conta de calendário.** Sem a data da conversa, ele inventava datas (2/4). Com a data,
  "sexta que vem" caía no sábado (2/6). Com o código entregando uma lista dos próximos 14 dias, 6/6.
  Conta é trabalho do código; o modelo só consulta.
- **A posição no prompt pesa.** A regra "não puxe assunto antigo" na personalidade oscilava entre 1/4
  e 7/8. A mesma instrução colada no resumo da última conversa (a última coisa do prompt) deu 12/12.
- **Ler a resposta antes de culpar o Tony.** Duas falhas eram do juiz: ele contou como "inventado" o
  que o próprio Tony tinha dito e não aceitou "SQL" como resposta a "o que eu decidi estudar antes de Node?".
- Placar com 4 repetições oscila: um 3/4 isolado pode ser ruído. Antes de mudar algo, `--vezes 8` ou 12.

## 2026-10-23 — v0.2.0 publicada: revisão

**Feito**
- `tony revisar`: lê os `/ruim`, o revisor (`gpt-oss:120b-cloud`) propõe **uma** mudança, diff no
  terminal, aceitar → testa antes e depois → você decide se fica. Commit manual.
- Testado com um log de exemplo (marcações inventadas por mim, mudança desfeita no fim): o revisor achou o
  padrão certo ("toda resposta termina com pergunta"), placar geral seguiu 24/24, e as falas marcadas
  deram 4/4 e 2/4 — correção só parcial, que o teste deixou visível.
- Falas de teste com conversa anterior (`antes`) e fala nova `encerramento`. Placar: **28/28**.
- Publicado: tag e release `v0.2.0` (commit `f8187ef`).

**Aprendi**
- Contexto muda o resultado: "valeu, era isso" sozinho não é a mesma fala que no fim de uma conversa.
- Uma rodada parcial de testes não pode virar "a rodada anterior" de tudo: comparar fala por fala.
- No bash, `H='-c x=!gh auth ...'` e depois `git $H` quebra o argumento nos espaços: argumento com espaço
  vai escrito por extenso (ou num array).

## 2026-10-23 — v0.2: falas de teste

**Feito**
- Decidido: testes antes da revisão; juiz em outro modelo (`gpt-oss:120b-cloud`); placares privados.
- `tony testar` com 6 falas (segunda pessoa, honestidade, tamanho, sem bajulação, pedido ambíguo,
  formato de terminal). Primeira rodada: **24/24**. Commit `004a680` (local).
- Validação do teste: voltando a personalidade antiga, `segunda-pessoa` deu 0/4.

**Travou**
- A saída estruturada (parâmetro `format`) não funciona nos modelos de nuvem: testei 5 modelos e todos
  responderam em texto solto. Saída: o juiz entrega o veredito chamando uma ferramenta cujos parâmetros
  são o esquema — funcionou de primeira.

**Pendente**
- Etapa 4: `tony revisar` (decidir: uma mudança por rodada ou várias).
- Conversar com o Tony e marcar `/ruim`, que é a entrada da revisão.

**Aprendi**
- Um teste que sempre passa não prova nada: é preciso ver ele **falhar** quando deveria (rodar contra a
  versão com o defeito) antes de confiar no 24/24.
- Uma API pode aceitar um parâmetro e ignorá-lo em silêncio. Testar o recurso isolado antes de construir
  em cima dele economizou a etapa inteira.
- Tool calling serve para mais do que "fazer coisas": é também um jeito de obrigar o modelo a responder
  num formato.

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
