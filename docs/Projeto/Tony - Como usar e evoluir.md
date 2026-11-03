---
criado: 2026-10-23
tags: [tony, projeto, guia]
fonte: própria
---

> [!info] Mapa: [[Mapa - Tony]]

# Tony — Como usar e evoluir

Guia rápido do Tony na v4 (em construção na `develop`): como conversar, onde fica cada coisa e o
ciclo para melhorar. As regras de branch e de produção estão em [[Tony - Regras do projeto]].

## Duas pastas: trabalho e produção

| Pasta | Branch | Para quê |
|---|---|---|
| `~/projetos/tony` | `develop` | onde o trabalho acontece; o Obsidian mostra a `docs/` daqui |
| `~/projetos/tony-producao` | `main` | o que está em uso: o timer do resumo do dia roda daqui |

Depois de um merge na `main`: `cd ~/projetos/tony-producao && git pull` (e `uv sync` se as
dependências mudaram). Se o `config.local.yaml` mudar, copie para as duas pastas.

## Conversar

Num terminal (não dentro do Claude Code):

```bash
cd ~/projetos/tony && uv run tony
```

| Comando | Para quê |
|---|---|
| `/bom` | a última resposta acertou o tom |
| `/ruim <motivo>` | a última resposta errou; o motivo é o que mais ajuda a corrigir |
| `/nova` | começa uma conversa nova |
| `/prompt` | mostra exatamente o que o modelo está recebendo |
| `/sair` ou Ctrl+D | encerra |

Cada conversa começa do zero: o Tony não guarda memória entre conversas. O que ele sabe sobre você
vem das notas da `Inteligência/`. Ainda não há ferramentas: as da agenda entram nas próximas etapas.

## Resumo do dia

Todo dia às 08:00 chega uma notificação com o resumo do dia (`tony dia`), tirado das notas. Para
mudar a hora, rode da pasta de produção: `uv run tony agendar --hora 07:30`; para desligar:
`systemctl --user disable --now tony-dia.timer`. Se o PC estava desligado às 08:00, ele roda ao ligar
e tenta de novo a cada 2 minutos até a rede subir; se as 6 tentativas falharem, chega uma notificação
avisando. Para ver o que aconteceu: `journalctl --user -u tony-dia`.

## Testar

```bash
cd ~/projetos/tony && uv run tony testar          # todas as falas
uv run tony testar tamanho ambiguo                # só algumas
uv run tony testar ambiguo --vezes 8              # repetir mais, quando uma falha pode ser só variação
```

Cada fala de `testes/falas.yaml` roda 4 vezes; o juiz (`gpt-oss:120b-cloud`) confere cada resposta e
o placar sai comparado com a rodada anterior. Para criar um teste novo, acrescente uma fala com um
`espera` que dê para responder com sim ou não, e confira que ele reprova a versão com o problema.

O que não depende do modelo tem testes de código, sem rede, em menos de um segundo:

```bash
cd ~/projetos/tony && uv run python -m unittest discover testes
```

## Onde fica cada coisa

| O quê | Onde | No GitHub? |
|---|---|---|
| Personalidade | `personalidade/` (identidade, tom, regras) | sim |
| Configuração padrão | `config.exemplo.yaml` | sim |
| Seus valores (caminho da Inteligência) | `config.local.yaml`, nas duas pastas | **não** |
| O que ele sabe sobre você | `docs/Inteligência/` (fora do git; no git só `modelos/`) | **não** |
| Contas do Google e do Telegram | `~/.config/tony/` (cliente OAuth, token, `assistente.env`) | **não** |
| Logs com `/bom` e `/ruim` | `logs/*.jsonl` | **não** |
| Falas de teste | `testes/falas.yaml` | sim |
| Placares e respostas dos testes | `dados/testes/` | **não** |
| Documentação (estas notas) | `docs/` | sim |

## O ciclo de evolução

1. **Conversar e marcar** — use `/ruim <motivo>` sem dó; é a matéria-prima.
2. **Virar fala de teste** — o problema entra em `testes/falas.yaml` (com `antes`, se depender da
   conversa), e a fala tem que reprovar a versão atual.
3. **Mudar o texto** em `personalidade/` e rodar `tony testar` completo: a fala do problema tem que
   melhorar e as outras não podem piorar.
4. **Commit na `develop`** — uma mudança por commit, com o antes e o depois na mensagem. O log de cada
   sessão guarda o commit da personalidade em uso, então dá para comparar versões do Tony.
5. **Produção** — quando a `develop` passa nos testes e não conflita, ela vai para a `main`.

Exemplo real (v4, etapa 1): o Tony prometia "eu aviso quando o sistema liberar". A fala `nao-promete`
reprovou a personalidade antiga em 8 de 8; com a regra nova em `regras.md`, 4 de 4.

## Alimentar o que ele sabe

Crie notas em `docs/Inteligência/` (prefixo `Tony - `). Todas entram no prompt no início de cada
conversa. Tudo ali vai para o modelo na nuvem: só o que pode sair da máquina. Essas notas ficam fora
do git; se a nota for de um tipo novo, crie também o modelo vazio em `docs/Inteligência/modelos/`.

## Relacionado

- [[Tony - Regras do projeto]] — branches, produção e o que nunca sobe para o GitHub
- [[Tony - Próximas atualizações]] — as etapas da v4
- [[Tony - Diário de bordo]] — o histórico das sessões de trabalho
- [[Tony - Sobre o Josias]] — a nota principal da Inteligência
