# Changelog

## Em andamento (v0.2)

- `tony testar`: falas fixas em `testes/falas.yaml`, rodadas várias vezes, com placar dado por um modelo
  juiz (`gpt-oss:120b-cloud`) e comparado com a rodada anterior.
- Saída estruturada no cliente (`estruturado`), entregue por chamada de ferramenta.
- Memória de exemplo em `exemplos/inteligencia/` para os testes.

## v0.1.0 — 2026-10-23

Primeira versão: o Tony só conversa, e o foco é a evolução do diálogo.

- Personalidade em `personalidade/` (identidade, tom, regras), versionada no git.
- Conversa no terminal com streaming, via Ollama (modelo padrão: `gemma4:31b-cloud`).
- Memória: notas de uma pasta configurável entram no prompt; ao sair, a conversa vira um resumo lido na próxima.
- Conversa longa: o começo é resumido quando o contexto passa de 80% do limite.
- Log `.jsonl` por sessão, com a versão da personalidade em uso e as marcações `/bom` e `/ruim`.
- Comandos: `/bom`, `/ruim`, `/nova`, `/prompt`, `/ajuda`, `/sair`.
- Personalidade: o Tony fala com o criador em segunda pessoa (antes dizia "o projeto do Josias" para o próprio Josias).
