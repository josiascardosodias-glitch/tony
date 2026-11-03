# CLAUDE.md do Tony — documentação do agente Tony

Esta pasta guarda a documentação do Tony, o agente de IA próprio do Josias: o planejamento, o diário
de bordo, as regras do projeto e a pasta que o Tony lê (`Inteligência/`). O código fica em outro
lugar, no repositório público `~/projetos/tony`.

É uma pasta dentro do vault My-Brain, isolada no conteúdo, com Git próprio (repositório local; sem
remoto até o usuário pedir). O ponto de entrada é `Mapa - Tony.md`.

## Isolamento

- **Use só o conteúdo desta pasta e o repositório do código** (`~/projetos/tony`).
- **Nunca leia, busque, linke, copie ou cite o Cofre nem o TheForge**, mesmo quando o assunto é
  igual. O `.claude/settings.json` bloqueia o acesso. As skills globais do segundo cérebro
  (`capturar`, `bom-dia`, `consultar-cerebro`, `fecha-o-dia`…) são do Cofre e não se aplicam aqui.
- Os wikilinks daqui só apontam para notas desta pasta.

## Regras do projeto

Antes de qualquer atualização do Tony, leia `Projeto/Tony - Regras do projeto.md`: branches `main`
(produção) e `develop` (trabalho), as condições para o merge, IA no mínimo e dados no PC. Para
levantar o estado, siga a lista "Como levantar o estado" dessa nota.

## Estrutura

| Caminho | O que é |
|---|---|
| `Mapa - Tony.md` | entrada: estado atual e a lista das notas |
| `Projeto/` | o que planejamos (o Tony não lê): regras, roadmap, diário, briefing, guia de uso |
| `Inteligência/` | a única pasta que o Tony lê (`memoria.inteligencia` no `config.local.yaml`). Vai para um modelo na nuvem: nada sensível nela |

## Convenções das notas

- Português, Markdown compatível com Obsidian.
- Nota nova começa com frontmatter e, logo abaixo, o callout do mapa:
  ```yaml
  ---
  criado: AAAA-MM-DD
  tags: [tony, ...]
  fonte: <url ou "própria">
  ---
  ```
  `> [!info] Mapa: [[Mapa - Tony]]`
- Nomes com o prefixo `Tony - `. Uma nota = um assunto. Nota nova entra no `Mapa - Tony`.
- O diário de bordo recebe uma entrada por sessão de trabalho, a mais recente no topo.
- Nenhum segredo nas notas (senha, token, chave): eles ficam em `~/.config/tony/`.

## Git

- Commit ao fim de cada sessão de trabalho, com mensagens `tony: <o que mudou>`. Antes de reescrever
  várias notas, faça um checkpoint: `git commit --allow-empty -qm "tony: antes de <tarefa>"`.
- O histórico anterior a 2026-11-03 veio do Cofre (mensagens `vault: ...`), extraído só com as notas
  do Tony.
