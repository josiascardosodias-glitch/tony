---
criado: 2026-10-23
tags: [tony, projeto, diario]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Diário de bordo

Uma entrada por sessão de trabalho, a mais recente no topo: o que foi feito, o que travou, o que aprendi.

## 2026-11-03 — Rumo da v4: assistente de e-mail em produção

**Feito**
- Mapa do estado atual (fluxogramas da conversa, do `tony dia` e do ciclo de evolução) publicado como página.
- Novo objetivo: o Tony vira **só** assistente de e-mail (datas dos e-mails → agenda "Tony" no Google →
  consulta pelo Telegram), e a v4 é a primeira versão de produção.
- Regras novas em [[Tony - Regras do projeto]]: `main` é produção, todo trabalho vai na `develop`, merge
  só com testes passando e sem conflito; IA no mínimo; dados e segredos no PC.
- Branch `develop` criada no repositório (local, sem push).
- Decisões: começar pelo Gmail pessoal (API, Python local), enxugar o que existe, agenda separada
  "Tony", descrição feita por script (0 token). Plano detalhado em [[Tony - Próximas atualizações]].
- v3.0.x (IMAP com a caixa real) cancelada: a v4 usa a API do Gmail.
- **O Tony saiu do Cofre:** a documentação virou a pasta `My-Brain/Tony/`, com Git próprio e o
  histórico das notas (30 commits, extraídos com `git-filter-repo`) e regras de isolamento como as
  das outras pastas. O `config.local.yaml` do código já aponta para `Tony/Inteligência/`.

**Pendente**
- Etapa 1 da v4: enxugamento e a correção que continua valendo (prometer o que não pode cumprir).
- Seu: projeto no Google Cloud com o cliente OAuth "Em produção" e o bot no @BotFather.

**Aprendi**
- `git filter-repo --path ... --path-rename ...` tira uma pasta de um repositório com todo o histórico,
  mesmo quando ela mudou de caminho no meio (aqui, `My-Brain/08-Tony/` e depois `08-Tony/`).
- Tela de consentimento do Google "Em teste" faz a autorização expirar em 7 dias: para um robô que
  roda sozinho, ela precisa ficar "Em produção".

## 2026-10-26 — Conversa de teste do Claude (sandbox)

**Feito**
- Conversa de ~20 trocas, com o Claude se apresentando como Claude, numa **cópia isolada** do repositório
  e da Inteligência: nada entrou na memória, nos resumos, nos logs nem nos Lembretes reais.
- Saídas conferidas e funcionando: `/bom` e `/ruim` antes da primeira resposta, `/ajuda`, comando
  desconhecido, `/lembrar` sem fato, `/lembrar` aceito e recusado, `/prompt`, `/nova` (lembrou da conversa
  anterior), `/sair`, Ctrl+D, terminal morto no meio (resumiu pelo log ao abrir de novo), `tony dia` sem
  nada e com um lembrete datado (acertou "quinta, 29/10").
- Respostas boas: recusou ler e-mail sem a ferramenta, opinião direta ("não acho boa ideia" para o 1B),
  "sexta que vem" = 06/11 numa segunda, perguntou de volta num pedido ambíguo, terceira pessoa com o Claude.

**Problemas achados**
1. **Recusa vira "erro do sistema":** com `n` na confirmação do `lembrar`, ele disse "houve um erro no
   sistema". A mentira foi para o resumo e para a memória ("tentou salvar... mas houve um erro").
   A fala `lembrar-recusado` não pega isso: o critério não proíbe culpar um erro.
2. **Confirmação dupla:** pedido para guardar, ele perguntou "quer que eu anote?" antes de chamar a
   ferramenta, que pergunta de novo.
3. **Ferramentas à toa:** "o que você tem anotado sobre o Josias?" → `listar_notas` + 2× `ler_nota`, com as
   notas já inteiras no prompt (a fala `nao-rele-o-que-ja-sabe` cobre outra pergunta).
4. **Memória velha:** "O Tony não tem acesso a arquivos ou internet" continua na memória desde a v1 e
   contradiz as ferramentas. A memória também diz "a pessoa" sem dizer se era você ou o Claude.
5. **E-mail:** sem a ferramenta, disse "se o sistema me liberar, consigo ler e-mails" e "se a ferramenta
   estiver disponível, eu aviso" — promessa que ele não tem como cumprir.
6. **Escorregões na terceira pessoa** falando com o Claude: "as regras de personalidade que você me deu",
   "o seu projeto".
7. Sugeriu 7–8B para rodar local sem saber da máquina (7,5 GB, sem GPU): faltava esse fato na Inteligência.

**Pendente**
- Corrigir 1 (texto da recusa + critério da fala) e 4 (fato velho na memória); avaliar 2, 3 e 5.
- Continua: senha de app para a v3.0.x.

**Aprendi**
- Testar escrita numa cópia isolada (`rsync` do repo + `config.local.yaml` apontando para a cópia da
  Inteligência) deixa conversar à vontade sem sujar a memória real.
- Uma resposta errada do modelo não fica na conversa: o resumo e a consolidação transformam ela em "fato".

## 2026-10-26 — v3.0.0 publicada e a sua primeira conversa

**Feito**
- A seu pedido, a v3 fechou **sem** o teste com a caixa real (falta a senha de app). Release
  `v3.0.0` (commit `9f47201`). Placar **131/132** (33 falas × 4); a falha foi do juiz.
- **Testes de código** novos (`uv run python -m unittest discover testes`, 15 testes): o `caixa_imap`
  de verdade conversando com um servidor IMAP falso. Contra o código antigo, dois falharam — uma data
  quebrada derrubava a caixa inteira e o HTML chegava com `&ccedil;`. Corrigidos.
- **O timer nunca tinha funcionado de verdade:** as duas execuções ao ligar o PC (25 e 26/10) falharam
  porque a rede ainda não estava no ar, e ninguém ficou sabendo. Agora o systemd tenta de novo a cada
  2 minutos (conferido com uma unidade de teste: falhou duas vezes, passou na terceira).
- **Sua primeira conversa com o Tony** (26/10, 09:29, duas trocas) acabou sem resumo: o terminal fechou
  sem `/sair`. Agora ele resume a conversa perdida pelo log ao abrir — e foi assim que a sua entrou na memória.
- O resumo do dia dizia "não achei nada nas notas e e-mails" sem ter e-mail: `dia-sem-email` 5/8 → 8/8.
- Numa segunda-feira, "sexta que vem" virava ora 30/10, ora 06/11 (`memoria-datas` 4/8; já falhava no
  código antigo). O calendário da consolidação agora marca o "que vem" de cada dia: 8/8.

**Pendente**
- v3.0.x: a senha de app e o teste com a caixa real (passo a passo em [[Tony - Próximas atualizações]]).
- Conversar mais com o Tony, marcando `/bom` e `/ruim`, e sair com `/sair`.

**Aprendi**
- Agendar não é funcionar: o timer estava "instalado e testado", mas só o `journalctl` mostrou que as
  execuções reais falhavam. Olhar o que aconteceu de verdade, não só se o comando roda.
- O que não depende do modelo merece teste de código: é exato e roda em segundos. As falas ficam para
  o que só o juiz decide.
- Um teste que dependia do dia da semana passou por semanas e falhou numa segunda. Data relativa testa
  o caso de hoje, não todos.
- Uma regra em texto pode não mudar nada (4/8 → 4/8); a mesma informação calculada pelo código resolveu.
- Critério vago ("nem dá a entender") faz o juiz reprovar resposta certa. Critério bom diz o que cumpre.

## 2026-10-24 — v2 (ferramentas) e começo da v3

**Feito**
- Analisada a ideia do n8n (vinda de outra conversa): fica fora da v2; na v3 você escolheu Python.
- **v2.0.0** publicada (tag e release, commit `f74e21b`): laço de ferramentas em streaming, `tony/ferramentas/` com
  `listar_notas`, `ler_nota` (nome aproximado), `buscar_notas`, `lembrar`. Placar 108/108.
- **v3** (commit `712f7bc`, só local): `ler_emails` (IMAP, só leitura, filtro), `tony dia`, `tony agendar` —
  timer instalado para 08:00 e testado pelo systemd (a notificação chegou). Placar 128/128.

**Pendente**
- Criar a senha de app do Gmail e configurar o e-mail (passo a passo no README); depois testamos com
  a caixa real e fechamos a v3.
- Publicar a v3 depois do teste com a caixa real.

**Aprendi**
- O `gemma4:31b-cloud` decide bem quando chamar uma ferramenta, mas erra o nome exato do argumento:
  a ferramenta tem que aceitar o aproximado e devolver o erro como texto, para ele se corrigir.
- "Não confirmou" ele leu como "ainda não confirmou" e pediu de novo (0/6); "disse não, não pergunte
  de novo" resolveu (6/6). O texto que a ferramenta devolve também é prompt.
- O juiz não vê o prompt do Tony: o fato de que ele precisa para julgar vai no critério.
- Fato de teste numa sessão real vaza: recusado na confirmação, ainda entrou no resumo e apareceu no
  resumo do dia. Testes de escrita, só com dados de exemplo.

## 2026-10-24 — v1.0.0 publicada

**Feito**
- A seu pedido, a v1.0 fechou sem esperar o seu uso: valeu como uso real a conversa conduzida pelo Claude.
- README revisado (versão, placar, ponteiro para a v2), `CHANGELOG.md` com a v1.0.0, roadmap com a v2 como próxima.
- Push dos commits da conversa real, tag e release `v1.0.0` (commit `f7b28ff`). Conferido que nenhum dado pessoal foi para o git.

**Pendente**
- Você conversar com o Tony e marcar `/bom` e `/ruim`: o que aparecer vira fala de teste na v1.0.x ou na v2.
- Planejar a v2 (ferramentas) em [[Tony - Próximas atualizações]].

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
- Commits `a710386`, `68f0230`, `9ef433d`, `444261d` — publicados na v1.0.0.

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
