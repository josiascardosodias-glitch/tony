# Decisões do Tony

Cada decisão: o que foi decidido, por quê e o que ficou de fora. A mais recente no fim.

## 2026-10-23 — Base da v1

1. **Nome: Tony.** Um nome só no pacote, no comando e no prompt.
2. **Motor: modelo na nuvem do Ollama**, chamado pelo Ollama instalado na máquina.
   *Por quê:* a máquina de desenvolvimento tem 7,5 GB de RAM e nenhuma GPU dedicada; um modelo local
   de 3–4B na CPU é lento e erra muito em chamada de ferramentas. Pela mesma API, voltar para um modelo
   local é trocar uma linha do config. *Fora:* modelo local desde o início; API de outro provedor.
3. **Cliente: biblioteca nativa `ollama`, isolada em `tony/cliente.py`.**
   *Por quê:* `num_ctx`, `keep_alive`, `think` e a checagem de capacidades são recursos nativos. A troca
   de provedor fica garantida por esse arquivo ser o único que conhece o Ollama.
   *Fora:* endpoint `/v1` compatível com OpenAI.
4. **Sem Modelfile.** Prompt, `num_ctx` e temperatura saem do config a cada requisição.
   *Por quê:* evitar duas fontes de verdade (Modelfile e config dizendo coisas diferentes).
5. ~~**A v1 só responde perguntas sobre uma pasta liberada**, só leitura.~~ *Substituída pela 10.*
   *Por quê:* entregar algo útil cedo, com o menor risco. Escrita, especialistas, embeddings e e-mail vêm depois.
6. *(Adiada para a v2 pela 10.)* **Ferramentas: uma função Python por arquivo em `tony/ferramentas/`, descoberta automaticamente.**
   A lib `ollama` gera o esquema a partir da docstring e dos tipos.
7. *(Adiada para a v2 pela 10.)* **Busca textual primeiro; embeddings depois**, comparando os dois com os mesmos testes.
   *Fora por enquanto:* Chroma (dependências pesadas para poucas centenas de notas).
8. **Repositório público; dados pessoais fora do git.** `config.local.yaml`, `logs/` e `dados/` no
   `.gitignore`; testes usam notas falsas em `exemplos/`.
9. **Sem frameworks de agente** (LangChain e similares) na v1: o laço é pequeno e o objetivo também é aprender.

## 2026-10-23 — Mudança de foco: a v1 é só diálogo

10. **A v1 só conversa, e o foco é a evolução do diálogo**, não a utilidade.
    *Por quê:* o projeto existe para aprender; começar pela conversa ensina prompt, contexto e memória
    antes de somar a complexidade das ferramentas. *Fora:* ferramentas, busca e especialistas (v2).
11. **Personalidade em `personalidade/*.md`, pública e versionada.** O log de cada sessão registra o
    commit da personalidade em uso (`*` = com edição não commitada).
    *Por quê:* ver no git como o "jeito" do Tony mudou e saber qual versão deu cada resposta.
12. **Memória em texto, sem busca:** as notas da pasta `memoria.inteligencia` entram inteiras no prompt,
    mais o resumo da última conversa. *Por quê:* são poucas notas; busca só faz sentido quando não couber.
13. **Conversa longa vira resumo, nunca corte silencioso.** Passando de 80% do `contexto.limite`
    (estimado em ≈ 4 caracteres por token), as mensagens antigas são resumidas pelo próprio modelo e as
    duas últimas trocas ficam inteiras. *Fora:* contar tokens pelo provedor (cada um conta diferente).
14. **Retorno com `/bom` e `/ruim <motivo>`** gravado no log `.jsonl` da sessão. É a base da etapa de
    revisão (o Tony propor mudanças na própria personalidade).
15. **Ambiente com `uv`.** O Python do sistema não tem `venv` nem `pip`; o `uv` resolve sem `sudo` e
    trava as versões no `uv.lock`.
16. **Temperatura 0,7.** O 0,3 do rascunho é bom para decisões estruturadas; para conversa, deixa o Tony
    repetitivo. Ajustável no config.
17. **Streaming:** a resposta aparece enquanto é gerada. Se der erro ou Ctrl+C no meio, a fala é
    descartada do histórico, para a conversa não ficar com uma pergunta sem resposta.

18. **Modelo: `gemma4:31b-cloud`.** Testado com a personalidade e as mesmas três falas contra
    `gpt-oss:120b-cloud` (também gratuito, mais formal) e `deepseek-v4.1-flash:cloud` (só no plano Pro).
    *Por quê:* tom mais próximo da personalidade, respostas em ~1 s, plano gratuito, e a família Gemma 4
    tem versões pequenas (`e2b`, `e4b`) para a troca futura por um modelo local.

19. **Licença MIT.** Qualquer pessoa pode usar e modificar, mantendo o crédito.
20. **Personalidade fala com o criador em segunda pessoa.** No teste, 8 de 8 respostas diziam "o projeto
    do Josias" para o próprio Josias; a identidade agora diz que quem conversa é o criador. Depois: 8 de 8 certas.

## 2026-10-23 — v0.2: falas de teste

21. **Falas de teste antes da revisão.** *Por quê:* sem uma medida, a revisão propõe mudanças sem saber
    se melhoram. *Fora:* construir a revisão primeiro, como estava no briefing.
22. **O juiz é outro modelo (`gpt-oss:120b-cloud`, temperatura 0).** *Por quê:* um modelo julgando as
    próprias respostas tende a ser bonzinho. Validado: com a personalidade antiga (terceira pessoa) o
    juiz deu 0/4; com a atual, 4/4.
23. **Saída estruturada por chamada de ferramenta.** Os modelos de nuvem do Ollama ignoram o parâmetro
    `format` (testados `gpt-oss` 120b e 20b, `beam`, `nemotron-3-nano` e `nemotron-3-super`: todos
    responderam em texto solto). O `estruturado()` do cliente oferece uma ferramenta `responder` cujos
    parâmetros são o esquema; o modelo a chama e os argumentos são o resultado. O resto do código não
    sabe desse detalhe. *Fora:* pedir JSON no prompt e torcer.
24. **Testes isolados:** conversa nova a cada repetição, sem resumo da última conversa e com memória de
    exemplo (`exemplos/inteligencia/`). *Por quê:* o placar só deve mudar quando mudam a personalidade
    ou o modelo — e qualquer pessoa consegue rodar.
25. **Placares privados por enquanto** (`dados/testes/`, fora do git). Publicar depois é fácil; o contrário não.
