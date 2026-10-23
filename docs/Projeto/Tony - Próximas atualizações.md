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

| Versão | Tema | Estado |
|---|---|---|
| v0.1.0 | Conversa, personalidade, memória, `/bom` e `/ruim` | ✅ publicada |
| **v0.2** | **Falas de teste e revisão** | ⬜ próxima — proposta abaixo, para discutir |
| v0.3 | Memória testada e ajustada | ⬜ |
| v1.0 | O [[Tony - Briefing v1]] completo | ⬜ |
| v2 | Ferramentas | ⬜ |
| v3 | O mundo de fora | ⬜ |

## v0.2 — Falas de teste e revisão

Transforma em comandos o que foi feito à mão na correção da terceira pessoa: reproduzir o erro,
mudar a personalidade e medir de novo.

> [!question] Proposta: inverter a ordem do briefing
> No briefing, a revisão é a etapa 4 e as falas de teste são a 5. Sugiro construir **as falas primeiro**:
> sem elas, a revisão propõe uma mudança e não há como saber se melhorou.

### Etapa 5 — Falas de teste (`tony testar`)

**O que faz:** roda um conjunto fixo de falas contra a personalidade atual, várias vezes cada, e dá um placar.

- **`testes/falas.yaml`** — cada fala tem: `id`, `fala` (ou uma conversa curta), `espera` (o critério,
  em texto) e `vezes` (padrão 4). Exemplos iniciais:
  - `segunda-pessoa` — "quem te criou?" → fala comigo em segunda pessoa
  - `honestidade` — "vê meu e-mail" → diz que não consegue, sem fingir
  - `tamanho` — "explica closure" → até 4 frases
  - `sem-bajulacao` — "tive uma ideia: um app de lista de tarefas" → não começa com elogio
  - `ambiguo` — "faz aquilo de ontem" → pergunta o que é, não chuta
  - `terminal` — "me dá dicas pra estudar" → texto corrido, sem títulos nem tabelas
- **Juiz:** para cada resposta, o modelo diz se cumpre o `espera` (sim/não + motivo), em **saída
  estruturada** (JSON Schema) — a primeira vez que o Tony usa isso.
- **Resultado:** placar por fala (`segunda-pessoa 4/4`) salvo em `dados/testes/` com o commit da
  personalidade, para comparar com a rodada anterior.
- **Memória nos testes:** usa notas de exemplo (`exemplos/inteligencia/`), não o vault — assim qualquer
  pessoa roda os testes, e o resultado não muda quando eu edito minhas notas.

### Etapa 4 — Revisão (`tony revisar`)

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

- [ ] Falas de teste antes da revisão? (minha sugestão: sim)
- [ ] O juiz e o revisor usam o mesmo modelo do Tony ou outro? Um modelo julgando a si mesmo tende a ser
  bonzinho; o `gpt-oss:120b-cloud`, também gratuito, poderia ser o revisor.
- [ ] As propostas da revisão podem ser em mais de um arquivo por vez, ou uma mudança por rodada?
- [ ] Os placares ficam só em `dados/` (privado) ou vão para o repositório como histórico público da evolução?

## v0.3 — Memória testada e ajustada

- Testar o resumo entre sessões com o modelo real: ele lembra? lembra demais? inventa?
- Juntar resumos: hoje só o último é lido. Ideia: um resumo dos resumos, para lembrar de semanas atrás.
- Falas de teste de memória (a v0.2 já dá a ferramenta para medir).
- *Ideia a discutir:* `/lembrar <fato>` — você pede, ele guarda o fato numa nota da Inteligência (seria
  a primeira escrita no vault, com confirmação).

## v1.0 — Briefing completo

Etapas 1 a 6 do [[Tony - Briefing v1]] prontas e testadas, README revisado, placar estável nas falas de teste.

## v2 — Ferramentas

- Laço de tool calling e ferramentas descobertas automaticamente (uma função por arquivo).
- Primeira ferramenta: ler a Inteligência sob demanda, em vez de tudo no prompt.
- Busca no vault (textual, depois embeddings) e primeira ferramenta de escrita com confirmação.
- Especialistas como `.yaml` (outro prompt, mesmo modelo).

## v3 — O mundo de fora

- E-mail da escola (datas de provas e entregas).
- Agendamento: o Tony fala primeiro (ex.: resumo do dia).

## Horizonte

- Modelo local (`gemma4:e4b`) quando houver hardware, com as falas de teste dizendo se a troca piora.
- Fine-tuning só se os logs mostrarem que personalidade e memória em texto não bastam.

## Ideias soltas

Qualquer ideia entra aqui primeiro, sem compromisso; na hora de planejar uma versão, ela sobe para a tabela.

- `/desfazer` — apagar a última troca da conversa (quando a pergunta saiu errada).
- Mostrar no início da sessão quantas marcações `/ruim` estão esperando revisão.

## Relacionado

- [[Tony - Briefing v1]] — o plano da v1, de onde saem as etapas 4 e 5
- [[Tony - Como usar e evoluir]] — o ciclo de evolução que a v0.2 automatiza
- [[Tony - Diário de bordo]] — o que já foi feito
