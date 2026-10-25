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

## 2026-10-23 — v0.2: revisão

26. **Uma mudança por rodada na revisão.** *Por quê:* se o placar piorar, sabe-se exatamente o que
    causou. *Fora:* várias mudanças de uma vez.
27. **O revisor também é outro modelo (`gpt-oss:120b-cloud`, temperatura 0,3)**, pelo mesmo motivo do
    juiz. Proposta = trocar um trecho exato de um arquivo; se o trecho não existir exatamente uma vez,
    o erro volta ao revisor (até 3 tentativas). Só `personalidade/` pode mudar; commit é manual.
28. **Aceitar não é manter.** Aceitar aplica e testa; depois de ver o placar e as falas marcadas, você
    decide se a mudança fica. Desfeita, as marcações continuam pendentes e o placar daquela versão é
    apagado (não serve de comparação).
29. **As falas marcadas são testadas no contexto delas** (as duas trocas anteriores), com o motivo do
    `/ruim` como critério. *Por quê:* no teste da revisão, "valeu, era isso" fora de contexto não era a
    mesma situação. Daí veio o campo `antes` nas falas de teste.
30. **Comparação fala por fala:** o "antes" de cada fala é o resultado mais recente dela, juntando todas
    as rodadas. *Por quê:* uma rodada parcial (`tony testar ambiguo`) apagava a comparação das outras.

## 2026-10-24 — v0.3: memória

31. **Memória acumulada em um arquivo só (`dados/memoria.md`)**, com no máximo 40 linhas. Quando um
    resumo deixa de ser o último, o modelo o junta à memória; o último resumo continua inteiro no prompt.
    *Por quê:* o tamanho do prompt fica sob controle por mais conversas que existam, e nada é lido
    duas vezes. *Fora:* os N últimos resumos inteiros (esquece tudo antes de N) e resumo por semana
    (mais peças, prompt maior).
32. **A memória marca até qual resumo já entrou** (`<!-- até: ... -->` na primeira linha). Se a
    consolidação falhar, os resumos seguintes ficam pendentes e entram na próxima vez — nenhum se perde.
33. **Consolidação com temperatura 0,2**, com o modelo do Tony. É organizar fatos, não conversar.
34. **O código entrega datas e calendário; o modelo só consulta.** Sem a data da conversa, o modelo
    inventava as datas da memória (2/4); com a data mas sem calendário, errava "sexta que vem" (2/6,
    caía no sábado). Com 14 dias listados, 6/6. *Regra:* conta de calendário é do código.
35. **`/lembrar` escreve no vault, numa nota só dele** (`Tony - Lembretes.md` na pasta da
    Inteligência), depois de mostrar o fato e pedir confirmação. Nunca edita notas que você escreveu.
    *Por quê:* fica visível e editável no Obsidian, e a pasta já é lida a cada conversa.
36. **Cada seção de memória do prompt diz quando usá-la.** Só a regra na personalidade não bastava:
    numa pergunta de git, o Tony puxava o app da última conversa (1/4 a 7/8, oscilando). Com o aviso
    junto do resumo, 12/12 — e continuou lembrando quando perguntado (8/8). *Por quê:* o resumo é a
    última coisa do prompt e pesa mais; a instrução precisa estar colada nele.
37. **Critério de teste também se corrige.** Duas falhas eram do juiz, não do Tony (o motivo dito
    pelo próprio Tony contado como "inventado"; "SQL" não aceito como resposta a "o que eu decidi
    estudar antes de Node?"). Antes de mexer na personalidade, ler a resposta que falhou.

## 2026-10-24 — Primeira conversa real (com o Claude)

38. **A consolidação diz de quem é cada fato.** O resumo é escrito pelo Tony em primeira pessoa; a
    consolidação, num pedido à parte, transformou "eu não tenho acesso a arquivos" em "o usuário não
    possui acesso". Agora o pedido explica que "eu" é o Tony e manda nomear o sujeito. Fala de teste
    com o resumo real que causou o erro: 2/6 antes, 6/6 depois. Testes de memória podem trazer um
    `resumo` fixo, para testar só a consolidação.
39. **Com quem não é o Josias, o Tony fala dele na terceira pessoa.** Proposta do `tony revisar`;
    fala `outra-pessoa`: 0/6 antes, 6/6 depois, sem piorar `segunda-pessoa`.
40. **Ter opinião.** "Quando discordar, diga" não bastava: diante de uma ideia ruim ele listava riscos
    e devolvia a decisão (`discorda` 0/8). A regra agora manda começar dizendo que não acha boa ideia.
    Contra-teste `concorda-quando-faz-sentido` para ele não discordar de tudo. A proposta do revisor
    (acrescentar outra linha sobre "depende") foi testada e desfeita: 0/4 na fala marcada.
41. **Pergunta só quando precisa da resposta.** A pergunta de praxe no fim era a raiz de três falhas:
    `sem-pergunta-de-praxe`, `encerramento` e `lembra-demais` (a opinião nova vinha com "você usa isso
    no seu projeto de tarefas?", e o placar caiu de 12/12 para 10/12). Com a regra no `tom.md`: 8/8
    nas cinco falas ligadas a isso, e 76/76 em duas rodadas seguidas.
42. **Cada problema achado em conversa real vira fala de teste**, conferida contra a personalidade
    antiga (tem que falhar) e a nova (tem que passar).

## 2026-10-24 — v2: ferramentas

43. **n8n fora da v2.** A ideia (vinda de outra conversa) era começar as ferramentas em workflows do
    n8n e trocar por código nativo aos poucos. As ferramentas da v2 são locais e simples, o projeto
    existe para aprender o laço no código, e os testes dependeriam do n8n no ar. Medido: 1,4 GB livres
    de 7,5 GB, Docker nativo. Fica como pergunta da v3 (e-mail, agendamento).
44. **Uma ferramenta = um arquivo com uma função do mesmo nome** em `tony/ferramentas/`, descoberta
    automaticamente; a lib `ollama` monta o esquema da docstring e dos tipos. O corpo é livre (pode
    até chamar um webhook) e troca sem mexer no laço. O que não vem do modelo (pastas, confirmação)
    vem do `ambiente`, preenchido pela sessão ou pelo teste.
45. **Argumentos validados antes de rodar, e todo erro volta ao modelo como texto** (`erro: ...`), para
    ele corrigir a chamada. Visto na sessão real: chamou a nota pelo título, recebeu o erro e acertou.
46. **Nome de nota aproximado.** Num teste, o `gemma4:31b-cloud` decidiu certo quando chamar (9/9),
    mas pediu a nota "Josias" em vez de "Tony - Sobre o Josias". `achar` aceita sem prefixo, sem `.md`
    e pedaço do nome, desde que só uma nota combine.
47. **As ferramentas só enxergam a pasta `Inteligência`**, a única que pode ir para a nuvem. Buscar no
    vault inteiro é uma decisão de privacidade, para depois.
48. **Inteligência inteira no prompt até 6000 caracteres; acima, só a lista** e ele lê sob demanda.
    *Por quê:* é a decisão 12 aplicada — com poucas notas, inteiras é melhor (ele não precisa decidir
    ler); a lista é para quando não couber.
49. **`lembrar` também é ferramenta**, com a mesma confirmação do `/lembrar`. O "não" vem explícito
    no resultado ("não pergunte de novo"): com "não confirmou", ele pedia a confirmação de novo (0/6 → 6/6).
50. **Testes de ferramenta sem juiz quando dá:** `chama` confere no código quais ferramentas foram
    chamadas; `lista` confere o formato. O juiz errava formato ("a linha não começa com '- '" numa
    linha que começava). A escrita vai para uma pasta temporária; `confirma: false` simula o "não".
51. **Mudança sem efeito medido não fica.** Um aviso "não releia as notas" passou no teste também sem
    ele; foi retirado.
