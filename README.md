# Tony

Um agente de IA pessoal construído do zero em Python, para aprender como agentes funcionam por dentro.

**v2: conversa e ferramentas.** O foco não é ser útil, é conversar bem e melhorar com o uso: a
personalidade fica em arquivos de texto versionados, o Tony lembra da última conversa e das mais
antigas, e cada resposta pode ser marcada como boa ou ruim para guiar os próximos ajustes. Desde a
v2 ele tem ferramentas para consultar as notas sobre você e guardar fatos (com sua confirmação).
Falas de teste medem cada mudança (placar da v2: 108/108).

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

## Usar

```bash
uv run tony
```

| Comando | O que faz |
|---|---|
| `/bom` | marca a última resposta como boa |
| `/ruim <motivo>` | marca a última resposta como ruim |
| `/lembrar <fato>` | guarda um fato numa nota da pasta `memoria.inteligencia` (pede confirmação) |
| `/nova` | encerra a conversa (com resumo) e começa outra |
| `/prompt` | mostra o prompt de sistema montado |
| `/sair` | encerra, guardando um resumo para a próxima vez |

## Ferramentas

Ficam em `tony/ferramentas/`, uma função por arquivo, e são descobertas sozinhas: o modelo lê o nome,
a docstring e os tipos para decidir quando usar.

| Ferramenta | O que faz |
|---|---|
| `listar_notas` | lista as notas da pasta `memoria.inteligencia` |
| `ler_nota` | lê uma nota (aceita o nome aproximado) |
| `buscar_notas` | procura palavras nas notas |
| `lembrar` | guarda um fato na nota de lembretes, depois da sua confirmação |

Só a pasta `memoria.inteligencia` é acessível. Enquanto as notas cabem em
`memoria.inteligencia_inteira_ate` caracteres, elas vão inteiras no prompt; acima disso, só a lista, e
o Tony lê sob demanda. Para criar uma ferramenta, veja a docstring de `tony/ferramentas/__init__.py`.

## Testar

```bash
uv run tony testar                 # todas as falas de testes/falas.yaml
uv run tony testar tamanho ambiguo # só algumas
uv run tony testar --vezes 8       # mais repetições, placar mais confiável
```

Cada fala roda várias vezes (a resposta varia) numa conversa nova, com a memória de exemplo de
`exemplos/inteligencia/`. Uma fala pode trazer a sua própria memória (`ultima_conversa`, `memoria`), e
`tarefa: resumo` ou `tarefa: memoria` julgam o resumo da conversa ou a memória depois dele, em vez de
uma resposta. `chama: [ferramentas]` confere no código quais ferramentas ele chamou (`[]` = nenhuma);
nos testes, elas rodam sobre a memória de exemplo e a escrita vai para uma pasta temporária. Um segundo modelo, o juiz (`testes.juiz` no config), confere cada resposta
contra o critério `espera` e o placar sai por fala, comparado com a rodada anterior:

```
segunda-pessoa   ✓✓✓✓  4/4   (antes: 0/4)
```

As respostas e os motivos do juiz ficam em `dados/testes/` (fora do git).

## Revisar

```bash
uv run tony revisar
```

Lê as respostas marcadas com `/ruim` nos logs e pede a um segundo modelo, o revisor (`revisao.revisor`
no config), **uma** mudança na personalidade, mostrada como diff:

- **aceitar** — a mudança é aplicada e testada: placar completo antes e depois, mais as próprias falas
  marcadas (com a conversa que veio antes delas). No fim, você decide se ela fica;
- **outra proposta** — o revisor tenta algo diferente;
- **descartar** — as marcações não eram problema e não serão propostas de novo.

Só arquivos de `personalidade/` são alterados, e o commit fica com você.

## Como o Tony evolui

1. **Personalidade** — `personalidade/*.md`. Edite o texto e faça commit: o log de cada sessão
   registra a versão da personalidade que estava em uso.
2. **Memória** — as notas da pasta `memoria.inteligencia` entram no prompt; ao sair, a conversa vira
   um resumo em `dados/resumos/`, lido inteiro no início da próxima. O resumo anterior, que deixa de
   ser o último, é consolidado em `dados/memoria.md`: uma lista de até 40 fatos com data, que também
   entra no prompt. `/lembrar` grava um fato na pasta da Inteligência, com a sua confirmação.
3. **Retorno** — `logs/*.jsonl` guarda cada fala, resposta e marcação `/bom`/`/ruim`.
4. **Medida** — `tony testar` antes e depois de cada mudança: só fica a mudança que não piora o placar.
5. **Revisão** — `tony revisar` junta tudo: das marcações a uma mudança testada, uma por rodada.

## Estrutura

```
tony/
├── config.exemplo.yaml   padrões (config.local.yaml sobrescreve)
├── personalidade/        quem o Tony é, como fala, regras
├── testes/falas.yaml     falas de teste e o critério de cada uma
├── exemplos/             memória de exemplo usada nos testes
└── tony/
    ├── main.py           loop do terminal e comandos
    ├── cliente.py        único arquivo que conhece o Ollama
    ├── conversa.py       histórico, prompt de sistema, laço de ferramentas, resumos e memória
    ├── ferramentas/      uma ferramenta por arquivo, descobertas sozinhas
    ├── memoria.py        personalidade, notas, resumos, memória e lembretes
    ├── registro.py       log da sessão
    ├── testes.py         falas de teste e juiz
    ├── revisao.py        propostas de mudança a partir das marcações
    └── config.py         leitura da configuração
```

As decisões de projeto, com o motivo de cada uma, estão em [DECISOES.md](DECISOES.md); o que mudou em cada versão, em [CHANGELOG.md](CHANGELOG.md); para onde ele vai, em [ROADMAP.md](ROADMAP.md).

## Licença

[MIT](LICENSE)
