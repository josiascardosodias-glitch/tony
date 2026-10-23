# Roadmap

Para onde o Tony vai. O que já saiu está no [CHANGELOG.md](CHANGELOG.md); o porquê de cada escolha,
no [DECISOES.md](DECISOES.md). As versões `v0.x` constroem a v1 (só conversa) até ela ficar completa.

## ✅ v0.1 — Conversa

Personalidade em arquivos, memória, resumo entre sessões, marcações `/bom` e `/ruim`.

## ✅ v0.2 — Medir e revisar

- **`tony testar`** — falas fixas (`testes/falas.yaml`) rodadas várias vezes contra a personalidade
  atual. Um modelo juiz confere cada resposta contra o critério esperado e dá um placar por fala,
  guardado junto com o commit da personalidade.
- **`tony revisar`** — lê as respostas marcadas com `/ruim`, propõe mudanças na personalidade
  (como diff), aplica só as aceitas e roda os testes antes e depois.

## v0.3 — Memória

Testar e ajustar o resumo entre sessões; lembrar além da última conversa.

## v1.0 — A v1 completa

Conversa, memória, testes e revisão prontos, com placar estável.

## Depois

- **v2 — Ferramentas:** laço de tool calling, ferramentas descobertas automaticamente, busca em notas.
- **v3 — O mundo de fora:** e-mail, agendamento.
- **Horizonte:** rodar com um modelo local; fine-tuning, se o texto não bastar.
