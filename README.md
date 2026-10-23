# Tony

Um agente de IA pessoal construído do zero em Python, para aprender como agentes funcionam por dentro.

**Versão 1: só conversa.** O foco desta versão não é ser útil, é conversar bem e melhorar com o uso:
a personalidade fica em arquivos de texto versionados, o Tony lembra da conversa anterior, e cada
resposta pode ser marcada como boa ou ruim para guiar os próximos ajustes.

## Instalar

Requisitos: [uv](https://docs.astral.sh/uv/) e [Ollama](https://ollama.com).

```bash
git clone <este repositório> && cd tony
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

## Como o Tony evolui

1. **Personalidade** — `personalidade/*.md`. Edite o texto e faça commit: o log de cada sessão
   registra a versão da personalidade que estava em uso.
2. **Memória** — as notas da pasta `memoria.inteligencia` entram no prompt; ao sair, a conversa vira
   um resumo em `dados/resumos/`, lido no início da próxima.
3. **Retorno** — `logs/*.jsonl` guarda cada fala, resposta e marcação `/bom`/`/ruim`.

## Estrutura

```
tony/
├── config.exemplo.yaml   padrões (config.local.yaml sobrescreve)
├── personalidade/        quem o Tony é, como fala, regras
└── tony/
    ├── main.py           loop do terminal e comandos
    ├── cliente.py        único arquivo que conhece o Ollama
    ├── conversa.py       histórico, prompt de sistema e resumo quando o contexto enche
    ├── memoria.py        personalidade, notas e resumos
    ├── registro.py       log da sessão
    └── config.py         leitura da configuração
```

As decisões de projeto, com o motivo de cada uma, estão em [DECISOES.md](DECISOES.md).
