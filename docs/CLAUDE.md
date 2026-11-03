# CLAUDE.md do Tony — documentação do agente Tony

Esta pasta guarda a documentação do Tony, o agente de IA próprio do Josias: o planejamento, o diário
de bordo, as regras do projeto e a pasta que o Tony lê (`Inteligência/`). Fica na pasta `docs/` do
repositório **público** do código (`~/projetos/tony`), e o vault My-Brain mostra ela por um link
(`My-Brain/Tony` → `~/projetos/tony/docs`). O ponto de entrada é `Mapa - Tony.md`.

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
| `Inteligência/` | a única pasta que o Tony lê (`memoria.inteligencia` no `config.local.yaml`). Vai para um modelo na nuvem: nada sensível nela. **Fora do git**, menos `modelos/` |
| `Inteligência/modelos/` | modelos vazios das notas pessoais (sobem para o GitHub) |

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
- **Dado pessoal não sobe para o repositório.** Ele vai numa nota da `Inteligência/`, que o
  `.gitignore` deixa de fora; no repositório fica só o modelo vazio em `Inteligência/modelos/`
  (nome com `(modelo)`, para não confundir os links). Nota nova com dado pessoal: crie o modelo
  vazio junto. Nas notas de `Projeto/`, que sobem, escreva sobre o projeto, não sobre a pessoa.

## Git

- O Git é o do repositório do código, e as regras de branch valem aqui também: commit na `develop`,
  com mensagens `docs: <o que mudou>`.
- O histórico das notas anterior a 2026-11-03 veio do Cofre (mensagens `vault: ...` e `tony: ...`).
