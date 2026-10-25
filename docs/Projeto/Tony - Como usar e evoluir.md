---
criado: 2026-10-23
tags: [tony, projeto, guia]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Como usar e evoluir

Guia rápido do Tony v1.0: como conversar, onde fica cada coisa e o ciclo para melhorar o diálogo.

## Conversar

Num terminal (não dentro do Claude Code):

```bash
cd ~/projetos/tony && uv run tony
```

| Comando | Para quê |
|---|---|
| `/bom` | a última resposta acertou o tom |
| `/ruim <motivo>` | a última resposta errou; o motivo é o que mais ajuda a corrigir |
| `/lembrar <fato>` | guarda o fato em `Tony - Lembretes` na Inteligência (mostra e pede confirmação) |
| `/nova` | fecha a conversa (com resumo) e começa outra |
| `/prompt` | mostra exatamente o que o modelo está recebendo |
| `/sair` ou Ctrl+D | encerra e guarda um resumo para a próxima vez |

## Testar

```bash
cd ~/projetos/tony && uv run tony testar          # todas as falas
uv run tony testar tamanho ambiguo                # só algumas
```

Cada fala de `testes/falas.yaml` roda 4 vezes; o juiz (`gpt-oss:120b-cloud`) confere cada resposta e
o placar sai comparado com a rodada anterior. Para criar um teste novo, acrescente uma fala com um
`espera` que dê para responder com sim ou não.

## Revisar

```bash
cd ~/projetos/tony && uv run tony revisar
```

Junta as respostas marcadas com `/ruim` e o revisor (`gpt-oss:120b-cloud`) propõe **uma** mudança na
personalidade, mostrada como diff. Opções: **aceitar** (aplica e testa: placar antes e depois, mais as
falas marcadas no contexto delas — no fim você decide se fica), **outra proposta**, **descartar** as
marcações (não eram problema) ou **sair**. Mudança mantida → o comando mostra o `git commit` sugerido.

## Onde fica cada coisa

| O quê | Onde | No GitHub? |
|---|---|---|
| Personalidade | `~/projetos/tony/personalidade/` (identidade, tom, regras) | sim |
| Configuração padrão | `config.exemplo.yaml` | sim |
| Seus valores (caminho do vault) | `config.local.yaml` | **não** |
| O que ele sabe sobre você | `My-Brain/08-Tony/Inteligência/` (este vault) | **não** |
| Resumos das conversas | `~/projetos/tony/dados/resumos/` | **não** |
| Memória das conversas antigas | `~/projetos/tony/dados/memoria.md` (até 40 fatos, pode editar) | **não** |
| Lembretes do `/lembrar` | `My-Brain/08-Tony/Inteligência/Tony - Lembretes.md` | **não** |
| Logs com `/bom` e `/ruim` | `~/projetos/tony/logs/*.jsonl` | **não** |
| Falas de teste | `~/projetos/tony/testes/falas.yaml` | sim |
| Placares e respostas dos testes | `~/projetos/tony/dados/testes/` | **não** |
| O que já foi revisado | `~/projetos/tony/dados/revisoes.jsonl` | **não** |

## O ciclo de evolução

1. **Conversar e marcar** — use `/ruim <motivo>` sem dó; é a matéria-prima.
2. **Revisar** — `tony revisar` lê as marcações, propõe uma mudança e mede antes e depois.
3. **Se o problema vai voltar a ser testado** — vire-o uma fala em `testes/falas.yaml` (com `antes`, se
   depender da conversa), para que nenhuma mudança futura o traga de volta.
4. **À mão, quando preferir** — mudar o texto em `personalidade/` e rodar `tony testar` completo:
   a fala do problema tem que melhorar e as outras não podem piorar.
5. **Decidir** — só fica a mudança que melhora sem piorar o resto.
6. **Commit** — uma mudança por commit, com o antes e o depois na mensagem. O log de cada sessão
   guarda o commit da personalidade em uso, então dá para comparar versões do Tony.

Exemplo real (v0.1): o Tony dizia "o projeto do Josias" falando com o próprio Josias. Reproduzido em
8 de 8 respostas; corrigido no `identidade.md` dizendo que quem conversa é o criador; depois, 8 de 8
em segunda pessoa (commit `68c6d83`).

## Alimentar a memória

Crie notas em `08-Tony/Inteligência/` (prefixo `Tony - `). Todas entram no prompt no início de cada
conversa. Tudo ali vai para o modelo na nuvem: só o que pode sair da máquina.

O resto ele faz sozinho: ao sair, a conversa vira um resumo (lido inteiro na próxima), e o resumo
anterior é consolidado em `dados/memoria.md`, uma lista de fatos com data. Para algo que ele não pode
esquecer, use `/lembrar`. Se a memória guardar algo errado, edite o arquivo; a primeira linha
(`<!-- até: ... -->`) precisa ficar.

## Relacionado

- [[Tony - Briefing v1]] — o plano da v1 e o que vem depois
- [[Tony - Diário de bordo]] — o histórico das sessões de trabalho
- [[Tony - Sobre o Josias]] — a primeira nota da memória
