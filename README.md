# Tony

Um agente de IA pessoal construído do zero em Python, para aprender como agentes funcionam por dentro.

**v4 (em construção na branch `develop`): assistente de e-mail.** O Tony vai achar as datas nos seus
e-mails, gravar numa agenda "Tony" do Google Agenda e responder pelo Telegram o que está marcado, com
o mínimo de IA: buscar, filtrar e achar datas é código; o modelo só entra no que o código não resolve.
A primeira etapa enxugou o que veio das versões anteriores: ficaram a personalidade em arquivos de
texto versionados, a conversa no terminal, as marcações `/bom` e `/ruim`, o resumo do dia e as falas
de teste (placar da etapa 1: 51/52). O plano está no [ROADMAP.md](ROADMAP.md).

## Instalar

Requisitos: [uv](https://docs.astral.sh/uv/) e [Ollama](https://ollama.com).

```bash
git clone https://github.com/josiascardosodias-glitch/tony.git && cd tony
uv sync
ollama signin            # só para modelos de nuvem (sufixo -cloud)
```

## Configurar

Os padrões estão em `config.exemplo.yaml`. Para mudar algo, crie um `config.local.yaml` só com o que
quer trocar (ele fica fora do git):

```yaml
modelo: "qwen3:4b"                      # outro modelo, local ou de nuvem
memoria:
  inteligencia: "~/notas/sobre-mim"     # pasta de .md que o Tony lê no início de cada conversa
```

Para usar a pasta do próprio repositório, aponte para `docs/Inteligência` e copie para lá os modelos
de `docs/Inteligência/modelos/`, preenchidos com os seus dados. As notas preenchidas ficam fora do git.

## Contas do Google e do Telegram (v4)

Dois assistentes no terminal fazem a parte manual, passo a passo, e guardam tudo em `~/.config/tony/`
(fora do repositório):

```bash
scripts/assistente-google.sh     # projeto no Google Cloud, APIs do Gmail e da Agenda, cliente OAuth
scripts/assistente-telegram.sh   # bot no @BotFather, token e o seu chat_id
```

## Coletar as datas dos e-mails (v4)

Tudo aqui é código, sem IA, e os e-mails não saem do seu PC.

```bash
uv run tony autorizar            # uma vez (e a cada 7 dias, enquanto o app do Google estiver "Em teste")
uv run tony coletar              # e-mails novos → datas → dados/eventos.json
uv run tony eventos              # as datas dos próximos 30 dias
uv run tony eventos --revisar    # as de confiança média, para você decidir
uv run tony bloquear @loja.com   # nunca mais lê e-mails desse domínio (ou de um endereço)
uv run tony aceitar <id>         # uma data de revisar vira evento (os ids estão no --revisar)
uv run tony descartar <id>       # uma data de revisar é jogada fora
uv run tony agenda               # leva os eventos para a agenda "Tony" (o coletar já faz isso)
```

Os eventos vão para uma agenda "Tony" que ele cria no seu Google Agenda. Ele só tem acesso às agendas
que ele mesmo criou: as suas, ele não enxerga. Para recomeçar, apague a agenda "Tony" e o
`dados/agenda.json`.

Cada data recebe uma confiança de 0 a 1 (`tony/datas.py`): palavra de compromisso, hora e data no
assunto somam; e-mail em massa (com link de descadastro) perde. A partir de 0,6 vira evento; de 0,3 a
0,6 fica para revisar. Os limites estão em `coleta` no `config.exemplo.yaml`.

## Usar

```bash
uv run tony
```

| Comando | O que faz |
|---|---|
| `/bom` | marca a última resposta como boa |
| `/ruim <motivo>` | marca a última resposta como ruim |
| `/nova` | começa uma conversa nova |
| `/prompt` | mostra o prompt de sistema montado |
| `/sair` | encerra |

Cada conversa começa do zero: desde a v4 o Tony não guarda memória entre conversas. O que ele sabe
sobre você vem só das notas da pasta `memoria.inteligencia`.

## Ferramentas

Ficam em `tony/ferramentas/`, uma função por arquivo, e são descobertas sozinhas: o modelo lê o nome,
a docstring e os tipos para decidir quando usar. Na v4 a pasta está vazia: as ferramentas das notas e
do IMAP saíram, e as da agenda entram nas próximas etapas. Para criar uma, veja a docstring de
`tony/ferramentas/__init__.py`.

## O Tony fala primeiro

```bash
uv run tony dia               # o resumo do dia: provas, entregas e pendências dos próximos 7 dias, tirado das notas
uv run tony dia --notificar   # o mesmo, como notificação na área de trabalho
uv run tony agendar --hora 08:00   # todo dia nesse horário (timer do systemd do seu usuário)
```

Se o PC estava desligado na hora, o resumo roda ao ligar; se a rede ainda não subiu, o systemd tenta
de novo a cada 2 minutos (até 6 vezes). Se as 6 falharem, chega uma notificação avisando. Para ver o
que aconteceu: `journalctl --user -u tony-dia`. Para desligar: `systemctl --user disable --now tony-dia.timer`.

O timer roda a pasta de onde o `tony agendar` foi chamado. Para ele usar só o que está na `main`
(produção), deixe uma pasta presa nela e agende de lá:

```bash
git worktree add ../tony-producao main && cp config.local.yaml ../tony-producao/
cd ../tony-producao && uv sync && uv run tony agendar --hora 08:00
```

## Testar

```bash
uv run tony testar                 # todas as falas de testes/falas.yaml
uv run tony testar tamanho ambiguo # só algumas
uv run tony testar --vezes 8       # mais repetições, placar mais confiável
```

Cada fala roda várias vezes (a resposta varia) numa conversa nova, com a memória de exemplo de
`exemplos/inteligencia/`. `antes` põe uma conversa curta antes da fala, `tarefa: dia` julga o resumo
do dia e `chama: [ferramentas]` confere no código quais ferramentas ele chamou (`[]` = nenhuma). Um
segundo modelo, o juiz (`testes.juiz` no config), confere cada resposta contra o critério `espera` e
o placar sai por fala, comparado com a rodada anterior:

```
segunda-pessoa   ✓✓✓✓  4/4   (antes: 0/4)
```

As respostas e os motivos do juiz ficam em `dados/testes/` (fora do git).

O que não depende do modelo tem testes de código, sem rede e em menos de um segundo:

```bash
uv run python -m unittest discover testes
```

## Como o Tony evolui

1. **Personalidade** — `personalidade/*.md`. Edite o texto e faça commit: o log de cada sessão
   registra a versão da personalidade que estava em uso.
2. **Retorno** — `logs/*.jsonl` guarda cada fala, resposta e marcação `/bom`/`/ruim`.
3. **Medida** — `tony testar` antes e depois de cada mudança: só fica a mudança que não piora o placar.
4. **Produção** — o trabalho é feito na branch `develop` e só vai para a `main` com os testes de
   código passando, o placar sem piorar e sem conflito.

## Estrutura

```
tony/
├── config.exemplo.yaml   padrões (config.local.yaml sobrescreve)
├── personalidade/        quem o Tony é, como fala, regras
├── scripts/              assistentes para configurar o Google e o Telegram
├── testes/              falas de teste (falas.yaml) e testes de código (test_*.py)
├── exemplos/             memória de exemplo usada nos testes
├── docs/                 documentação do projeto (notas do Obsidian): regras, roadmap, diário
│   └── Inteligência/     o que o Tony sabe sobre você: fora do git, menos os modelos vazios
└── tony/
    ├── main.py           loop do terminal e comandos
    ├── cliente.py        único arquivo que conhece o Ollama
    ├── conversa.py       histórico, prompt de sistema e laço de ferramentas
    ├── ferramentas/      uma ferramenta por arquivo, descobertas sozinhas (vazia até a agenda)
    ├── memoria.py        personalidade e notas da Inteligência
    ├── dia.py            resumo do dia e o timer que o agenda
    ├── google.py         OAuth e clientes das APIs do Google
    ├── coleta.py         e-mails → datas → eventos.json, bloqueados
    ├── datas.py          o extrator de datas (sem IA)
    ├── agenda.py         a agenda "Tony" no Google Agenda, sem duplicar
    ├── contas.py         os comandos autorizar, coletar, eventos e bloquear
    ├── registro.py       log da sessão
    ├── testes.py         falas de teste e juiz
    └── config.py         leitura da configuração
```

As decisões de projeto, com o motivo de cada uma, estão em [DECISOES.md](DECISOES.md); o que mudou em cada versão, em [CHANGELOG.md](CHANGELOG.md); para onde ele vai, em [ROADMAP.md](ROADMAP.md).

## Licença

[MIT](LICENSE)
