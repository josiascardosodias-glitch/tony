# Changelog

## v1.0.0 — 2026-10-24

A v1 completa: o Tony conversa, lembra, é medido e revisado. Esta versão fecha com a primeira
conversa real (com o Claude) e o primeiro `tony revisar` com marcações reais.

- Memória: a consolidação diz de quem é cada fato (o "eu" do resumo é o Tony). Testes de memória
  aceitam um `resumo` fixo.
- Personalidade: fala do Josias na terceira pessoa com quem não é ele; tem opinião diante de uma
  ideia ruim; não fecha a resposta com pergunta de praxe.
- Cinco falas novas: `memoria-quem`, `outra-pessoa`, `discorda`, `concorda-quando-faz-sentido`,
  `sem-pergunta-de-praxe`.
- Placar: 76/76 (19 falas × 4), em duas rodadas seguidas.
- Etapas 1 a 6 do briefing da v1 prontas: conversa, motor, memória, revisão, falas de teste e publicação.

## v0.3.0 — 2026-10-24

Memória: lembrar além da última conversa, sem inventar e sem puxar assunto velho do nada.

- Memória das conversas antigas em `dados/memoria.md`: quando um resumo deixa de ser o último, o
  modelo o consolida numa lista de até 40 fatos, com a data do calendário de cada decisão e
  pendência. Entra no prompt junto com o resumo inteiro da última conversa. Se a consolidação falhar,
  o resumo fica pendente e entra na próxima vez.
- `/lembrar <fato>`: grava o fato na nota `Tony - Lembretes.md` da pasta da Inteligência, só depois
  da confirmação. Vale já na conversa atual.
- Os resumos agora pedem só o que foi dito, e as seções de memória do prompt dizem quando usá-las.
- Falas de teste de memória: `ultima_conversa` e `memoria` nas falas; `tarefa: resumo` e
  `tarefa: memoria` julgam o resumo e a consolidação. Sete falas novas.
- Placar da versão: 55/56 (14 falas × 4). A falha foi em `sem-bajulacao`: um "É um clássico para
  quem está aprendendo" abrindo a resposta.

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
