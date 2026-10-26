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

## ✅ v0.3 — Memória

Memória das conversas antigas (os resumos consolidados), `/lembrar` com confirmação e falas de teste
de memória: lembra, não inventa, não puxa assunto velho do nada, guarda datas certas.

## ✅ v1.0 — A v1 completa

Conversa, memória, testes e revisão prontos, com placar estável (76/76 em duas rodadas). Ajustada
com a primeira conversa real.

## ✅ v2 — Ferramentas

Laço de tool calling, ferramentas descobertas automaticamente (uma por arquivo), leitura e busca nas
notas, `lembrar` com confirmação. Depois, dentro da v2: busca por embeddings e especialistas em `.yaml`.

## ✅ v3 — O mundo de fora

E-mail da faculdade por IMAP, só leitura, e o resumo do dia como notificação, agendado pelo systemd.
Testes de código ao lado das falas. Falta conferir com uma caixa real (v3.0.x).

## Depois

- **Horizonte:** rodar com um modelo local; fine-tuning, se o texto não bastar.
