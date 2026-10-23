# Tony

Um agente de IA pessoal construído do zero em Python, para aprender como agentes funcionam por dentro.

**v0.2: só conversa.** O foco desta versão não é ser útil, é conversar bem e melhorar com o uso:
a personalidade fica em arquivos de texto versionados, o Tony lembra da conversa anterior, e cada
resposta pode ser marcada como boa ou ruim para guiar os próximos ajustes.

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
| `/nova` | encerra a conversa (com resumo) e começa outra |
| `/prompt` | mostra o prompt de sistema montado |
| `/sair` | encerra, guardando um resumo para a próxima vez |

## Testar

```bash
uv run tony testar                 # todas as falas de testes/falas.yaml
uv run tony testar tamanho ambiguo # só algumas
uv run tony testar --vezes 8       # mais repetições, placar mais confiável
```

Cada fala roda várias vezes (a resposta varia) numa conversa nova, com a memória de exemplo de
`exemplos/inteligencia/`. Um segundo modelo, o juiz (`testes.juiz` no config), confere cada resposta
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
   um resumo em `dados/resumos/`, lido no início da próxima.
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
    ├── conversa.py       histórico, prompt de sistema e resumo quando o contexto enche
    ├── memoria.py        personalidade, notas e resumos
    ├── registro.py       log da sessão
    ├── testes.py         falas de teste e juiz
    ├── revisao.py        propostas de mudança a partir das marcações
    └── config.py         leitura da configuração
```

As decisões de projeto, com o motivo de cada uma, estão em [DECISOES.md](DECISOES.md); o que mudou em cada versão, em [CHANGELOG.md](CHANGELOG.md); para onde ele vai, em [ROADMAP.md](ROADMAP.md).

## Licença

[MIT](LICENSE)
