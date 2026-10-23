---
criado: 2026-10-23
tags: [tony, projeto, guia]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Como usar e evoluir

Guia rápido do Tony v0.1: como conversar, onde fica cada coisa e o ciclo para melhorar o diálogo.

## Conversar

Num terminal (não dentro do Claude Code):

```bash
cd ~/projetos/tony && uv run tony
```

| Comando | Para quê |
|---|---|
| `/bom` | a última resposta acertou o tom |
| `/ruim <motivo>` | a última resposta errou; o motivo é o que mais ajuda a corrigir |
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

## Onde fica cada coisa

| O quê | Onde | No GitHub? |
|---|---|---|
| Personalidade | `~/projetos/tony/personalidade/` (identidade, tom, regras) | sim |
| Configuração padrão | `config.exemplo.yaml` | sim |
| Seus valores (caminho do vault) | `config.local.yaml` | **não** |
| O que ele sabe sobre você | `My-Brain/08-Tony/Inteligência/` (este vault) | **não** |
| Resumos das conversas | `~/projetos/tony/dados/resumos/` | **não** |
| Logs com `/bom` e `/ruim` | `~/projetos/tony/logs/*.jsonl` | **não** |
| Falas de teste | `~/projetos/tony/testes/falas.yaml` | sim |
| Placares e respostas dos testes | `~/projetos/tony/dados/testes/` | **não** |

## O ciclo de evolução

1. **Conversar e marcar** — use `/ruim <motivo>` sem dó; é a matéria-prima.
2. **Ler as marcações** — nos logs, cada linha `"tipo": "marca"` aponta o turno com problema.
3. **Reproduzir** — virar o problema uma fala em `testes/falas.yaml` e rodar `tony testar <id>`.
4. **Ajustar a personalidade** — mudar o texto em `personalidade/`.
5. **Medir de novo** — `tony testar` completo: a fala nova tem que melhorar e as outras não podem piorar.
6. **Commit** — uma mudança por commit, com o antes e o depois na mensagem. O log de cada sessão
   guarda o commit da personalidade em uso, então dá para comparar versões do Tony.

Exemplo real (v0.1): o Tony dizia "o projeto do Josias" falando com o próprio Josias. Reproduzido em
8 de 8 respostas; corrigido no `identidade.md` dizendo que quem conversa é o criador; depois, 8 de 8
em segunda pessoa (commit `68c6d83`).

## Alimentar a memória

Crie notas em `08-Tony/Inteligência/` (prefixo `Tony - `). Todas entram no prompt no início de cada
conversa. Tudo ali vai para o modelo na nuvem: só o que pode sair da máquina.

## Relacionado

- [[Tony - Briefing v1]] — o plano da v1 e o que vem depois
- [[Tony - Diário de bordo]] — o histórico das sessões de trabalho
- [[Tony - Sobre o Josias]] — a primeira nota da memória
