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
| **v3**   | **O mundo de fora**                                | 🟡 em andamento      |

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

## v3 — O mundo de fora 🟡 em andamento

> [!check] Decidido em 2026-10-24: Gmail por IMAP (senha de app), notificação na área de trabalho, Python (sem n8n).
> Feito (commit `712f7bc`): `ler_emails` só leitura com filtro, `tony dia --notificar`, `tony agendar`
> (timer instalado, 08:00). **Falta:** a senha de app e o teste com a caixa real.

- E-mail da escola (datas de provas e entregas).
- Agendamento: o Tony fala primeiro (ex.: resumo do dia).
- *Pergunta:* n8n ou Python? O n8n poupa o OAuth do Google e os gatilhos de horário; IMAP e um
  `systemd timer` resolvem em Python sem serviço extra. Medir a RAM com o n8n antes; credenciais
  nunca no repositório; autenticar o webhook.

## Horizonte

- Modelo local (`gemma4:e4b`) quando houver hardware, com as falas de teste dizendo se a troca piora.
- Fine-tuning só se os logs mostrarem que personalidade e memória em texto não bastam.

## Ideias soltas

Qualquer ideia entra aqui primeiro, sem compromisso; na hora de planejar uma versão, ela sobe para a tabela.

- `/desfazer` — apagar a última troca da conversa (quando a pergunta saiu errada).
- Mostrar no início da sessão quantas marcações `/ruim` estão esperando revisão.
- Calendário dos próximos dias também no `# Agora` da conversa (hoje só a consolidação recebe), para
  ele não errar "que dia cai a sexta que vem" conversando.

## Relacionado

- [[Tony - Briefing v1]] — o plano da v1, de onde saem as etapas 4 e 5
- [[Tony - Como usar e evoluir]] — o ciclo de evolução que a v0.2 automatiza
- [[Tony - Diário de bordo]] — o que já foi feito
