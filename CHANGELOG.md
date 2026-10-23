# Changelog

## v0.1.0 — 2026-10-23

Primeira versão: o Tony só conversa, e o foco é a evolução do diálogo.

- Personalidade em `personalidade/` (identidade, tom, regras), versionada no git.
- Conversa no terminal com streaming, via Ollama (modelo padrão: `gemma4:31b-cloud`).
- Memória: notas de uma pasta configurável entram no prompt; ao sair, a conversa vira um resumo lido na próxima.
- Conversa longa: o começo é resumido quando o contexto passa de 80% do limite.
- Log `.jsonl` por sessão, com a versão da personalidade em uso e as marcações `/bom` e `/ruim`.
- Comandos: `/bom`, `/ruim`, `/nova`, `/prompt`, `/ajuda`, `/sair`.
- Personalidade: o Tony fala com o criador em segunda pessoa (antes dizia "o projeto do Josias" para o próprio Josias).
