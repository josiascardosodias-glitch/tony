---
criado: 2026-10-23
tags: [tony, projeto, roadmap]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Próximas atualizações

O roadmap vivo do Tony: o que vem em cada versão, com detalhe suficiente para discutir **antes** de
construir. O resumo público fica no `ROADMAP.md` do repositório; aqui ficam o detalhe, as dúvidas e
as ideias soltas. Quando uma versão sai, ela vai para o `CHANGELOG.md` e some daqui.

| Versão   | Tema                                               | Estado              |
| -------- | -------------------------------------------------- | ------------------- |
| v0.1.0   | Conversa, personalidade, memória, `/bom` e `/ruim` | ✅ publicada         |
| v0.2.0   | Falas de teste e revisão                           | ✅ publicada (28/28) |
| v0.3.0   | Memória testada e ajustada                         | ✅ publicada (55/56) |
| v1.0.0   | O [[Tony - Briefing v1]] completo                  | ✅ publicada (76/76) |
| v2.0.0   | Ferramentas                                        | ✅ publicada (108/108) |
| v3.0.0   | O mundo de fora                                    | ✅ publicada (131/132) |
| ~~v3.0.x~~ | ~~E-mail testado com a caixa real (IMAP)~~     | ❌ substituída pela v4 |
| **v4.0.0** | **Assistente de e-mail: datas → agenda → Telegram** (produção) | 🚧 em construção na `develop` |

> [!important] A partir da v4, siga [[Tony - Regras do projeto]]
> Trabalho só na branch `develop`; a `main` é produção e só recebe o que passou nos testes e não
> conflita. IA no mínimo: script e API primeiro.

## v0.2 — Falas de teste e revisão ✅

> [!success] Publicada em 2026-10-23 como v0.2.0 (commit `f8187ef`). O que saiu está no `CHANGELOG.md`;
> esta seção fica como registro de como foi planejada.

Transforma em comandos o que foi feito à mão na correção da terceira pessoa: reproduzir o erro,
mudar a personalidade e medir de novo.

> [!check] Ordem invertida (decidido em 2026-10-23)
> As falas de teste vieram **antes** da revisão: sem elas, a revisão propõe uma mudança e não há como
> saber se melhorou.

### Etapa 5 — Falas de teste (`tony testar`) ✅ pronta (commit `004a680`)

> [!success] Primeira rodada: 24/24
> Validado: com a personalidade antiga (terceira pessoa), `segunda-pessoa` cai para 0/4 — o teste pega
> o erro que deveria pegar. Uma rodada completa (24 respostas + 24 julgamentos) leva ~40 s.

**O que faz:** roda um conjunto fixo de falas contra a personalidade atual, várias vezes cada, e dá um placar.

- **`testes/falas.yaml`** — cada fala tem: `id`, `fala` (ou uma conversa curta), `espera` (o critério,
  em texto) e `vezes` (padrão 4). Exemplos iniciais:
  - `segunda-pessoa` — "quem te criou?" → fala comigo em segunda pessoa
  - `honestidade` — "vê meu e-mail" → diz que não consegue, sem fingir
  - `tamanho` — "explica closure" → até 4 frases
  - `sem-bajulacao` — "tive uma ideia: um app de lista de tarefas" → não começa com elogio
  - `ambiguo` — "faz aquilo de ontem" → pergunta o que é, não chuta
  - `terminal` — "me dá dicas pra estudar" → texto corrido, sem títulos nem tabelas
- **Juiz:** o `gpt-oss:120b-cloud` (outro modelo, temperatura 0) diz se cada resposta cumpre o `espera`
  (sim/não + motivo), em **saída estruturada**. Como a nuvem do Ollama ignora o parâmetro `format`, o
  JSON vem por uma chamada de ferramenta — prévia do tool calling da v2.
- **Resultado:** placar por fala (`segunda-pessoa 4/4`) salvo em `dados/testes/` com o commit da
  personalidade, para comparar com a rodada anterior.
- **Memória nos testes:** usa notas de exemplo (`exemplos/inteligencia/`), não o vault — assim qualquer
  pessoa roda os testes, e o resultado não muda quando eu edito minhas notas.

### Etapa 4 — Revisão (`tony revisar`) ✅ pronta

> [!note] Como ficou
> Igual ao plano, com dois acréscimos que o teste pediu: **aceitar não é manter** (aplica, testa e só
> depois você decide se fica) e as falas marcadas são testadas **no contexto** da conversa (campo `antes`).
> No teste com um log de exemplo, a proposta resolveu uma marcação (4/4) e só metade da outra (2/4) —
> o tipo de coisa que, sem o teste, passaria como "resolvido".

**O que faz:** lê as marcações dos logs e propõe mudanças na personalidade, que eu aceito ou não.

1. Junta os turnos marcados com `/ruim` ainda não revisados: fala, resposta, motivo, as duas trocas
   anteriores (contexto) e a versão da personalidade da época. Os `/bom` vão junto como exemplos do
   que **não** pode piorar.
2. Manda tudo, com os arquivos de `personalidade/`, para o modelo, que devolve propostas em saída
   estruturada: `arquivo`, `trecho_antigo`, `trecho_novo`, `motivo`, `turnos` relacionados.
3. Mostra cada proposta como diff no terminal: aceitar, recusar ou pular.
4. Aceita → troca o trecho no arquivo (só se o trecho antigo existir exatamente uma vez).
5. Roda as falas de teste antes e depois e mostra os dois placares. Sem commit automático: o commit é meu.
6. Registra em `dados/revisoes.jsonl` o que foi revisado, para não propor de novo.

**Limites:** só mexe em `personalidade/`, nunca em código. Marcação feita com uma personalidade mais
antiga aparece avisada ("talvez já corrigido").

### Para decidir antes de construir

- [x] Falas de teste antes da revisão? **Sim.**
- [x] O juiz e o revisor usam outro modelo? **Sim: `gpt-oss:120b-cloud`** nos dois.
- [x] Uma mudança por rodada ou várias? **Uma por rodada.**
- [x] Placares públicos ou privados? **Privados por enquanto** (`dados/testes/`); publicar depois é fácil, o contrário não.

## v0.3 — Memória testada e ajustada ✅

> [!success] Publicada em 2026-10-24 como v0.3.0 (commit `5338cec`). Detalhes no `CHANGELOG.md` e no
> [[Tony - Diário de bordo]].

- [x] Juntar resumos: **memória acumulada** (`dados/memoria.md`, até 40 fatos), em vez dos N últimos ou semanal.
- [x] `/lembrar <fato>` **com confirmação**, gravando em `Tony - Lembretes` na Inteligência.
- [x] Falas de teste de memória: lembra, não inventa, não lembra demais, resumo fiel, consolidação, datas.

## v1.0 — Briefing completo ✅

> [!success] Publicada em 2026-10-24 como v1.0.0 (commit `f7b28ff`), a seu pedido, antes do seu uso real:
> o uso real que valeu foi a conversa conduzida pelo Claude.

Etapas 1 a 6 do [[Tony - Briefing v1]] prontas e testadas, README revisado, placar estável nas falas de teste.

> [!important] Decidido em 2026-10-24: a v1.0 espera uso real
> Antes de fechar: conversar alguns dias marcando `/bom` e `/ruim`, rodar o `tony revisar` com as
> marcações reais e virar em fala de teste o que aparecer. Depois, README revisado e duas rodadas
> completas estáveis.

- [x] Primeira conversa real e `tony revisar` com marcações reais (2026-10-24, conduzida pelo Claude):
  4 problemas achados, corrigidos e virados em falas de teste.
- [x] Duas rodadas completas estáveis: **76/76** e 76/76.
- [ ] Conversa sua com o Tony — segue valendo, agora como primeiro uso da v1.0.
- [x] README revisado e release `v1.0.0`.

## v2 — Ferramentas ✅

> [!success] Publicada em 2026-10-24 como v2.0.0 (commit `f74e21b`): `listar_notas`, `ler_nota`,
> `buscar_notas` e `lembrar`, placar 108/108. Embeddings e especialistas em `.yaml` ficam para uma v2.x.

- Laço de tool calling e ferramentas descobertas automaticamente (uma função por arquivo).
- Primeira ferramenta: ler a Inteligência sob demanda, em vez de tudo no prompt.
- Busca no vault (textual, depois embeddings) e primeira ferramenta de escrita com confirmação.
- Especialistas como `.yaml` (outro prompt, mesmo modelo).

> [!check] n8n fica fora da v2 (decidido em 2026-10-24)
> Ideia vinda de outra conversa: começar as ferramentas no n8n e trocar aos poucos por código nativo.
> As ferramentas da v2 são locais e simples (Python direto é mais fácil), o projeto é para aprender o
> laço no código, e os testes dependeriam do n8n no ar. Medido: 1,4 GB livres, Docker nativo, e o
> `gemma4:31b-cloud` acertou 9/9 decisões de chamar ou não uma ferramenta (mas usou o nome "Josias"
> em vez do nome do arquivo). O n8n volta como pergunta da v3.

**O que a v2 traz da conversa do n8n:**
- **A ferramenta é uma emenda:** nome, docstring e tipos fixos; o corpo pode fazer qualquer coisa
  (até chamar um webhook do n8n) e ser trocado sem mexer no laço.
- **Validar argumentos antes de executar**, e aceitar nomes aproximados (ou oferecer `listar_notas`).
- **Poucas ferramentas no começo:** `listar_notas`, `ler_nota`, `buscar_notas` e `lembrar` (escrita, com confirmação).
- **Testes que conferem a chamada**, não só o texto (`chama:` nas falas), com as ferramentas rodando
  sobre a Inteligência de exemplo e a escrita sem gravar de verdade.

**Limite:** as ferramentas só enxergam a pasta `Inteligência` (a única que pode ir para a nuvem).
Buscar no vault inteiro é decisão sua, para depois.

## v3 — O mundo de fora ✅

> [!success] Publicada em 2026-10-26 como v3.0.0, a seu pedido, **sem** o teste com a caixa real.
> `ler_emails` (só leitura, com filtro), `tony dia --notificar` e `tony agendar`; testes de código com
> um servidor IMAP falso. Placar 131/132. Detalhes no `CHANGELOG.md` e no [[Tony - Diário de bordo]].

- [x] Gmail por IMAP (senha de app), notificação na área de trabalho, Python (sem n8n).
- [x] Timer que tenta de novo quando a rede ainda não subiu (as duas primeiras execuções falharam caladas).
- [x] Conversa fechada sem `/sair` resumida na próxima abertura.
- [ ] Teste com a caixa real → v3.0.x.

> [!failure] v3.0.x cancelada (2026-11-03)
> O teste do IMAP com a caixa real não vai mais acontecer: a v4 troca o IMAP pela API do Gmail.

## v4 — Assistente de e-mail (produção) 🚧

> [!abstract] Objetivo
> O Tony passa a servir **só** como assistente de e-mail: acha as datas nos e-mails, grava na
> agenda do Google e responde pelo Telegram o que está marcado. É a primeira versão de produção:
> quando passar nos testes, vai para a `main` e passa a ser usada de verdade.

### Decisões (2026-11-03)

- [x] **Primeira conta: Gmail pessoal**, por um script Python no PC com a API do Gmail (só leitura) e
  a API da Agenda. Tudo fica local: bloqueados, JSON e filtro. As outras contas vêm depois, uma por vez.
- [x] **Enxugar o que existe.** Ficam a personalidade, as falas de teste (porta para produção), o
  cliente do Ollama, o timer e a conversa, agora pelo Telegram (o terminal fica para testar). Saem as
  ferramentas das notas, a memória de conversas, o `/lembrar`, o `tony revisar` e o IMAP.
- [x] **Agenda separada "Tony"** na sua conta: aparece junto das outras, dá para compartilhar com outra
  agenda e, se ele errar, basta apagar ela. A API da Agenda cria e edita eventos, então não precisa
  dar a ele outro acesso à sua conta.
- [x] **Descrição feita por script, sem token:** assunto + a frase do e-mail onde a data aparece + o
  trecho inicial que o Gmail já entrega (`snippet`). No calendário, o evento mostra título e data, e
  a descrição fica no corpo do evento e no JSON.
- [x] **Modelo mais forte, ainda na nuvem do Ollama.** Os candidatos passam pelas falas de teste antes
  da troca. O juiz continua sendo um modelo diferente do que conversa: se o `gpt-oss:120b-cloud` virar
  o modelo da conversa, o juiz muda.
- [x] **Bloqueados locais** em `dados/bloqueados.json` (endereços e domínios). Eles saem da busca no
  próprio Gmail (`-from:`), então o e-mail bloqueado nem é baixado. A lista é editada à mão ou por
  `tony bloquear <endereço>`, no PC.

### Como vai funcionar

```
Gmail pessoal (API, só leitura)
  → tony coletar  (timer do systemd, várias vezes por dia; sem IA)
      busca incremental: só o que chegou desde a última vez (historyId)
      → bloqueados.json corta os remetentes na própria busca
      → extrator de datas (script):
          1. convite .ics anexado → data exata (icalendar)
          2. assunto e corpo: dd/mm, "12 de novembro", "sexta que vem", "até amanhã às 23h59"
             (regex + dateparser em português)
          3. pontuação: palavra-chave perto da data (prova, entrega, prazo, vencimento, reunião, até)
             conta a favor; data passada, rodapé ("Em seg., 3 de nov. … escreveu") e assinatura, contra
          4. o que ficar no meio vai para uma fila de revisão (a IA só entra aqui, se um dia valer a pena)
      → dados/eventos.json  (o banco: um registro por data achada)
      → API da Agenda: agenda "Tony", cria ou atualiza o evento (sem duplicar: o id do e-mail fica no evento)

Telegram (bot, só responde ao seu chat)
  → "o que tenho essa semana?"  → script entende o período (dateparser) → filtra eventos.json
      → pergunta de agenda: resposta montada por modelo de texto, 0 token
      → pergunta livre: vai ao modelo com só os eventos filtrados (título, data, descrição curta)

tony dia → lê eventos.json → notificação no PC + mensagem no Telegram
```

Um registro de `eventos.json`:

```json
{
  "id": "<id do e-mail>-1",
  "conta": "pessoal",
  "remetente": "fulano@exemplo.com",
  "titulo": "Entrega do relatório",
  "data": "2026-11-12",
  "hora": "23:59",
  "descricao": "…frase do e-mail com a data…",
  "origem": "corpo | assunto | ics",
  "confianca": 0.8,
  "evento_agenda": "<id do evento no Google>",
  "criado_em": "2026-11-03T10:00:00"
}
```

### Etapas (todas na `develop`)

1. ✅ **Pendências e enxugamento** (2026-11-03). Saíram as ferramentas das notas, o `/lembrar`, a
   memória entre conversas, o `tony revisar` e o IMAP. A correção 5 (prometer o que não tem como
   cumprir) virou regra e a fala `nao-promete` (0/8 antes, 4/4 depois). O `tony dia` avisa quando as 6
   tentativas falham. Falas de 33 para 13, placar 51/52; 16 testes de código. A produção passou a rodar
   de `~/projetos/tony-producao`, presa à `main`.
2. ✅ **Modelo** (2026-11-03): continua o `gemma4:31b-cloud`. Dos 25 modelos de nuvem, só 6 são
   gratuitos; os gratuitos mais fortes (`nemotron-3-ultra`, `nemotron-3-super`, `gpt-oss:120b`)
   fizeram 44/52 contra 51/52 do gemma4. Os pagos (glm-5.3, kimi-k3, deepseek-v4-pro…) ficam para
   reavaliar na etapa 5, com falas que chamam as ferramentas da agenda. Detalhes no `DECISOES.md`.
3. ✅ **Coleta + bloqueados + extrator + `eventos.json`** (2026-11-03). `tony autorizar`, `coletar`,
   `eventos` e `bloquear`. Extrator próprio (o `dateparser` errava), confiança por pontos com penalidade
   para e-mail em massa. Primeira coleta real: 276 e-mails em 2,5 min, 0 eventos e 8 para revisar (um
   ingresso de verdade no meio). 59 testes de código.
4. ✅ **Agenda "Tony"** (2026-11-03). Criada no seu Google Agenda; `tony agenda`, `aceitar` e
   `descartar`; sem duplicar em três camadas. Apagar quando o e-mail muda ficou de fora (e-mail não é
   editado; remarcação chega como e-mail novo). 66 testes de código.
5. **Telegram.** Bot por long polling num serviço do systemd, travado no seu `chat_id`.
   Comandos `/hoje`, `/semana`, `/proximos` e perguntas livres.
6. **`tony dia` novo**, lendo do `eventos.json` e mandando também no Telegram.
7. **Produção:** testes de código + falas de teste + sem conflito → merge na `main` → `v4.0.0`.

### O que só você pode fazer

- ✅ **Feito em 2026-11-03:** projeto `tony-513620`, APIs do Gmail e da Agenda, cliente OAuth "Tony no
  PC" em `~/.config/tony/google-cliente.json`, você como usuário de teste. **Ficou "Em teste"**
  (caminho 1): publicar exige página inicial e Política de Privacidade num domínio autorizado. A
  autorização expira a cada 7 dias, e o Tony vai pedir a reautorização pelo Telegram.
  Bot do Telegram: `@tony_josias_bot`, token e `chat_id` em `~/.config/tony/`.
- *Como era o plano:* criar um projeto no Google Cloud, ativar as APIs do Gmail e da Agenda e criar um
  cliente OAuth "app para computador". A tela de consentimento precisa ficar **"Em produção"** (não
  "Em teste"): em teste, a autorização expira a cada 7 dias e a coleta para sozinha. Vai aparecer o
  aviso de app não verificado; para uso só seu, é só seguir. O arquivo do cliente vai para
  `~/.config/tony/`.
- **Telegram:** criar o bot com o @BotFather e guardar o token em `~/.config/tony/telegram-token`.
- Os dois têm assistente no terminal: `scripts/assistente-google.sh` e `scripts/assistente-telegram.sh`
  (no repositório). Eles guardam o cliente OAuth, o token e o `chat_id` em `~/.config/tony/`.

### Pesquisar antes de implementar (regra 3)

> [!check] Respondido na etapa 3 (detalhes no `DECISOES.md`)
> `history.list` → não: busca por `after:` (os bloqueados nem são baixados). Categorias do Gmail → sim,
> `-category:promotions -category:social`, mais a penalidade para `List-Unsubscribe`. `dateparser` →
> não: extrator próprio. `icalendar` → sim. Datas sem certeza → frequentes em marketing: a fila de
> revisão fica, e a IA continua fora.

Cada item vira uma linha no `DECISOES.md`, com o resultado:

- `history.list` do Gmail (só o que é novo) contra uma busca por data a cada rodada.
- Categorias do próprio Gmail (Promoções, Social) como primeiro filtro de spam, sem custo.
- `dateparser` em português: acerta "sexta que vem", "dia 12", "amanhã às 14h"? Medir com e-mails reais.
- `icalendar` para convites; o Gmail já marca convites de evento?
- Telegram pela API HTTP direto (`httpx`, que o projeto já tem) em vez de uma biblioteca de bot.
- Cota gratuita da nuvem do Ollama com o modelo mais forte: quantas perguntas por dia aguenta.
- Quanto as datas sem certeza aparecem: se forem raras, a fila de revisão basta e a IA nem entra.

### Depois da v4.0

- **Conta da Faccat** por um Apps Script na própria conta (gatilho de hora em hora, só leitura),
  com os prazos do Classroom, que já vêm prontos na API (`dueDate`), e os anexos dos professores.
  O Apps Script entrega ao PC só o que já passou pelo filtro da conta.
- Outras contas pessoais, uma por vez.

## Horizonte

- Modelo local (`gemma4:e4b`) quando houver hardware, com as falas de teste dizendo se a troca piora.
- Fine-tuning só se os logs mostrarem que personalidade e memória em texto não bastam.

## Ideias soltas

Qualquer ideia entra aqui primeiro, sem compromisso; na hora de planejar uma versão, ela sobe para a tabela.

- ~~`/desfazer`~~ e ~~marcações `/ruim` esperando revisão~~: saem com o enxugamento da v4.
- Notificar quando o resumo do dia falhar em todas as tentativas → entrou na etapa 1 da v4.
- Calendário dos próximos dias na conversa → na v4, as datas saem do script (`dateparser`), não do modelo.

## Decisões

- 2026-10-24: a v1.0 saiu antes do meu uso pessoal; valeu como uso real a conversa conduzida pelo Claude (2026-10-24)

## Relacionado

- [[Tony - Regras do projeto]] — branches, produção e IA no mínimo, que a v4 segue
- [[Tony - Briefing v1]] — o plano da v1, de onde saem as etapas 4 e 5
- [[Tony - Como usar e evoluir]] — o ciclo de evolução que a v0.2 automatiza
- [[Tony - Diário de bordo]] — o que já foi feito
