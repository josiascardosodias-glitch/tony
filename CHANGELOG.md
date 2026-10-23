# Changelog

## v0.2.0 — 2026-10-23

Medir e revisar: o ciclo de evolução da personalidade virou comando.

- `tony testar`: falas fixas em `testes/falas.yaml`, cada uma rodada várias vezes numa conversa nova;
  um modelo juiz (`gpt-oss:120b-cloud`) confere cada resposta contra o critério. Placar por fala,
  comparado com o resultado mais recente de cada uma. Falas podem ter `antes` (conversa anterior).
- `tony revisar`: lê as marcações `/ruim`, pede ao revisor **uma** mudança na personalidade, mostra o
  diff e, se aceita, testa antes e depois (inclusive as falas marcadas, no contexto delas).
  Registro do que foi revisado em `dados/revisoes.jsonl`.
- Saída estruturada no cliente (`estruturado`), entregue por chamada de ferramenta.
- Memória de exemplo em `exemplos/inteligencia/`, usada nos testes.
- Placar da versão: 28/28 (7 falas × 4).

## v0.1.0 — 2026-10-23

Primeira versão: o Tony só conversa, e o foco é a evolução do diálogo.

- Personalidade em `personalidade/` (identidade, tom, regras), versionada no git.
- Conversa no terminal com streaming, via Ollama (modelo padrão: `gemma4:31b-cloud`).
- Memória: notas de uma pasta configurável entram no prompt; ao sair, a conversa vira um resumo lido na próxima.
- Conversa longa: o começo é resumido quando o contexto passa de 80% do limite.
- Log `.jsonl` por sessão, com a versão da personalidade em uso e as marcações `/bom` e `/ruim`.
- Comandos: `/bom`, `/ruim`, `/nova`, `/prompt`, `/ajuda`, `/sair`.
- Personalidade: o Tony fala com o criador em segunda pessoa (antes dizia "o projeto do Josias" para o próprio Josias).
