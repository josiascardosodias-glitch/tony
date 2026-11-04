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
Testes de código ao lado das falas. A conferência com a caixa real (v3.0.x) foi cancelada: a v4
troca o IMAP pela API do Gmail.

## ✅ v4.0 — Assistente de e-mail (primeira versão de produção)

O Tony passa a servir só como assistente de e-mail:

- **Coleta sem IA:** o Gmail pessoal pela API (só leitura), só o que é novo, com uma lista local de
  remetentes bloqueados que nem chegam a ser baixados.
- **Datas por script:** convites `.ics`, datas no assunto e no corpo (`dateparser` em português) e uma
  pontuação por palavras-chave. O resultado fica num `eventos.json` local.
- **Agenda:** cada data vira um evento numa agenda "Tony" no Google Agenda, sem duplicar.
- **Telegram:** pergunte o que tem na semana; respostas de agenda são montadas pelo código, e o
  modelo (mais forte, ainda na nuvem do Ollama) só entra nas perguntas livres.
- **Enxugado:** saem as ferramentas das notas, a memória de conversas, o `/lembrar`, o
  `tony revisar` e o IMAP. Ficam a personalidade, as falas de teste e o resumo do dia.

Publicada em 2026-11-03, com três contas: dois Gmails pela API e a Faccat pelo Apps Script (só os
prazos do Classroom). A `main` passa a ser só produção; o trabalho segue na `develop`.

## Depois da v4.0

- Os e-mails da Faccat por um caminho com login (sem URL pública).
- Publicar o app do Google (hoje "Em teste": a autorização vence a cada 7 dias).
- ✅ v4.1.0: `tony remover <id>` e `/remover` no Telegram (tirar um compromisso já aceito); o mesmo
  compromisso (remetente, dia e hora) entra uma vez só.
- Rodar 24 horas: hoje o Tony para quando o notebook suspende (tampa fechada).

## 📝 v5 — Tony no Google Apps Script

Rodar 24 horas sem o notebook e sem cartão: coleta, agenda, repetidos e Telegram (webhook) em
JavaScript no Apps Script, com Gmail e Agenda acessados pela própria conta (sem token que vence). As
falas de teste continuam em Python no PC.

## Depois

- **Mais contas:** a da faculdade (Apps Script na própria conta, com os prazos do Classroom) e outras
  pessoais, uma por vez.
- **Horizonte:** rodar com um modelo local; fine-tuning, se o texto não bastar.
