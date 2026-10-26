# Changelog

## v3.0.0 — 2026-10-26

O mundo de fora: o Tony lê o e-mail da faculdade e fala primeiro, com o resumo do dia.

- `ler_emails`: lê o e-mail por IMAP, só leitura (`EXAMINE` e `BODY.PEEK`: nada é marcado como lido),
  com `email.filtro` decidindo o que vai para o modelo. Aparece só com o e-mail configurado. Espera
  no máximo 30 s pelo servidor; um e-mail com data, charset ou cabeçalho quebrado não derruba a caixa;
  HTML chega sem tags e sem entidades (`&ccedil;` vira "ç"). **Ainda não testado com uma caixa real**
  (falta a senha de app); testado contra um servidor IMAP falso.
- `tony dia`: o Tony fala primeiro, com o resumo do dia; `--notificar` manda como notificação. Sem
  e-mail configurado, ele não diz mais que olhou e-mails.
- `tony agendar [--hora HH:MM]`: timer do systemd do usuário. Se a rede não subiu ainda (ao ligar o
  PC), tenta de novo a cada 2 minutos, até 6 vezes. Quem já agendou: rode `tony agendar` de novo.
- Conversa que acaba sem `/sair` (terminal fechado, rede caída) é resumida pelo log na próxima vez.
- Memória: "sexta que vem" vira a data certa em qualquer dia da semana (o calendário da consolidação
  marca o "que vem" de cada dia; numa segunda, ele errava metade das vezes).
- Testes de código (`uv run python -m unittest discover testes`): 15 testes, do IMAP e da recuperação.
- Falas de teste: caixa de e-mail de exemplo por fala (`emails`), `tarefa: dia` e datas relativas
  (`{hoje+5}`). Seis falas novas, a última `dia-sem-email`.
- Placar: 128/128 (32 falas × 4) antes das mudanças; 131/132 (33 falas × 4) com elas. A falha foi
  do juiz em `dia-sem-email` (reprovou uma resposta que não falava de e-mail); com o critério
  corrigido, 8/8 (e 3/8 com o pedido antigo, então o teste ainda pega o defeito).

## v2.0.0 — 2026-10-24

Ferramentas: o Tony consulta as notas e guarda fatos sozinho, quando a conversa pede.

- Laço de tool calling na conversa (em streaming): o modelo pede, o código roda e devolve, até ele
  responder. No máximo 5 rodadas por resposta; erro de ferramenta volta ao modelo como texto.
- Ferramentas descobertas automaticamente em `tony/ferramentas/` (um arquivo, uma função):
  `listar_notas`, `ler_nota` (aceita nome aproximado), `buscar_notas` e `lembrar` (pede confirmação).
- Só enxergam a pasta da Inteligência. Notas inteiras no prompt até 6000 caracteres; acima, só a lista.
- O terminal mostra cada chamada (`· ler_nota(nome='...')`), e o log guarda chamadas e resultados.
- Testes: `chama` e `lista` conferidos no código, `indice` e `confirma` nas falas, escrita numa pasta
  temporária. Oito falas novas.
- Placar: 107/108 e 108/108 (27 falas × 4).

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
