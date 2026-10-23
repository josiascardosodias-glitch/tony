
Tony — Documento de contexto e planejamento inicial

Projeto: Tony, assistente pessoal inteligente
Status: Conceito inicial — pesquisa e definição de arquitetura
Linguagem principal prevista: Python
Modelo de linguagem previsto: Um modelo local executado pelo Ollama
Ambiente previsto: Máquina local Linux, com possibilidade de utilizar uma máquina virtual
Versionamento: Git e GitHub

---

1. Visão geral do projeto

Tony será um assistente pessoal inteligente, desenvolvido e mantido por mim. A ideia é construir um agente próprio, com nome, identidade, instruções, responsabilidades e funcionalidades definidas de acordo com as minhas necessidades.

O objetivo não é simplesmente instalar ou utilizar um agente pronto de outra pessoa. Quero desenvolver meu próprio projeto, controlar sua evolução e adicionar funcionalidades gradualmente.

Tony deverá receber solicitações em linguagem natural, compreender o que preciso e, quando necessário, utilizar ferramentas para executar tarefas no computador ou consultar informações.

O projeto será desenvolvido por etapas, com implementação de funcionalidades, correções de bugs, melhorias e documentação contínua.

Princípios iniciais

- Criar um agente próprio, com código e regras controlados por mim.
- Utilizar Python como linguagem principal.
- Utilizar o Ollama como infraestrutura local para executar um modelo de linguagem.
- Permitir interação por linguagem natural.
- Desenvolver ferramentas que o agente possa utilizar para realizar tarefas.
- Manter o código versionado no GitHub.
- Executar o agente localmente, sem depender necessariamente de um serviço de IA hospedado na nuvem.
- Construir uma arquitetura que permita adicionar novas funcionalidades sem precisar reconstruir o projeto inteiro.

---

2. O que é Tony e qual é a relação com o Ollama?

Uma distinção importante para a arquitetura:

Tony será o agente. Ollama será a infraestrutura que executa o modelo de linguagem utilizado pelo agente.

O Ollama não precisa ser modificado ou transformado em outro produto para que Tony tenha identidade própria.

Tony poderá ter seu próprio nome, suas instruções, suas ferramentas e seu comportamento, enquanto utiliza um modelo disponibilizado pelo Ollama.

Responsabilidades

Componente| Responsabilidade
Tony| Representar o assistente, interpretar objetivos, organizar o fluxo de trabalho e coordenar ferramentas.
Python| Implementar a lógica, executar operações, controlar permissões e conectar os componentes.
Ollama| Executar o modelo de linguagem localmente e disponibilizar uma forma de enviar solicitações e receber respostas.
Modelo de linguagem| Interpretar linguagem natural, compreender contexto e produzir respostas ou propostas de ações.
Ferramentas| Executar tarefas concretas, como localizar, ler ou processar arquivos.
Git/GitHub| Versionar o código, registrar mudanças, documentar o projeto e permitir sua manutenção.

O modelo pode sugerir uma ação, mas não tem acesso automático aos arquivos ou ao sistema operacional. Tony, por meio do código Python e das ferramentas autorizadas, é que pode realizar essas operações.

---

3. Como funcionará a interação com o agente?

A interação inicial deverá ser simples: eu escrevo uma solicitação em linguagem natural, e Tony organiza o que precisa ser feito.

Exemplo conceitual:

1. Eu solicito: “Tony, encontre o documento da escola e veja se ele contém alguma data importante.”
2. Tony interpreta o objetivo.
3. O agente identifica quais ferramentas seriam necessárias.
4. O código Python executa as operações autorizadas, como localizar e ler o documento.
5. O conteúdo relevante é enviado ao modelo de linguagem.
6. Tony apresenta a resposta, indicando as datas encontradas.

Esse fluxo não exige que eu escreva comandos técnicos para cada tarefa. As ferramentas são implementadas previamente; a linguagem natural serve para solicitar seu uso.

Linguagem natural e comandos técnicos

A linguagem natural poderá ser utilizada para conversar com Tony.

Por baixo dessa interação, Python continuará responsável pela lógica e pelas operações. Não é necessário escrever scripts novos a cada solicitação.

Por exemplo, eu posso pedir para Tony resumir um documento. O agente utiliza a ferramenta de leitura adequada, obtém o conteúdo e pede ao modelo que produza o resumo.

O modelo não substitui a ferramenta que efetivamente abre o documento.

---

4. Python, bibliotecas e ferramentas

Python será a linguagem principal do projeto.

A princípio, não é necessário aprender ou utilizar várias linguagens para construir Tony. É possível implementar a estrutura inicial, a comunicação com o modelo e as ferramentas em Python.

Bibliotecas poderão ser adicionadas conforme as necessidades.

Exemplos de responsabilidades que poderão exigir bibliotecas

- Comunicação com o modelo executado pelo Ollama.
- Leitura de diferentes formatos de documentos.
- Manipulação de arquivos e diretórios.
- Integração com serviços externos.
- Processamento de informações e datas.
- Criação de uma interface de interação.

O acesso básico ao sistema de arquivos pode ser realizado com recursos disponíveis no próprio Python. Bibliotecas adicionais serão úteis para formatos específicos ou funcionalidades mais complexas.

A escolha das bibliotecas deverá ocorrer durante o planejamento técnico, conforme os requisitos reais de cada funcionalidade.

---

5. Acesso aos arquivos da máquina local

Uma das funcionalidades consideradas é permitir que Tony localize e consulte documentos armazenados no computador.

A ideia inicial é definir quais diretórios e arquivos o agente poderá acessar.

Tony poderá receber uma solicitação simples e utilizar ferramentas Python para localizar o material correspondente.

Exemplo de fluxo

- Definir os diretórios autorizados.
- Receber uma solicitação em linguagem natural.
- Identificar o arquivo ou a categoria de arquivos procurada.
- Localizar e ler o conteúdo permitido.
- Enviar o conteúdo relevante ao modelo.
- Responder à solicitação.

Importante: informar o caminho de um arquivo ao modelo não significa que ele poderá abri-lo. O código precisa disponibilizar uma ferramenta que faça a leitura e entregue o conteúdo ao modelo.

Também será necessário definir limites de acesso. Tony não deve poder acessar, modificar ou excluir qualquer arquivo indiscriminadamente.

---

6. Primeira funcionalidade considerada: assistente de e-mails

Uma das ideias iniciais para Tony é utilizá-lo como assistente de e-mails, começando pela caixa de entrada da escola.

O objetivo seria permitir que Tony:

- Consulte e-mails relevantes.
- Identifique mensagens que contenham datas específicas.
- Extraia datas de provas, entregas, reuniões ou outros compromissos.
- Organize as informações encontradas.
- Apresente um resumo dos compromissos identificados.

Exemplo conceitual

Eu solicito:

“Tony, verifica meus e-mails da escola e me diz quais têm datas de entrega.”

Tony deverá consultar as mensagens autorizadas, analisar seu conteúdo e apresentar as datas encontradas.

Limitação da pesquisa inicial

Durante a conversa, decidimos deixar de lado, temporariamente, os detalhes de APIs, requisições, endpoints e autenticação para compreender a arquitetura conceitual.

Isso não significa que essas etapas possam ser ignoradas em uma implementação real.

A integração efetiva com uma caixa de e-mail poderá exigir uma API, autenticação, permissões específicas ou outra forma autorizada de acesso.

Essa integração será planejada quando a funcionalidade de e-mails entrar na fase de implementação.

---

7. Ollama: utilização como modelo local

O Ollama será considerado para executar um modelo de linguagem localmente.

A proposta é utilizar um modelo compatível com o Ollama e conectar Tony a ele.

O modelo poderá auxiliar na interpretação de solicitações, na análise de documentos e na produção de respostas.

O que não é necessário fazer inicialmente

Não é necessário:

- Treinar um modelo de linguagem do zero.
- Criar uma infraestrutura própria de treinamento.
- Modificar o Ollama para dar um nome próprio ao agente.
- Publicar os pesos do modelo junto com o código de Tony.

O primeiro caminho a investigar é a utilização de um modelo existente, executado localmente pelo Ollama.

O que precisará ser definido

- Qual modelo será utilizado.
- Quanto de memória e processamento ele exige.
- Se o modelo funciona adequadamente no computador escolhido.
- Como Python fará a comunicação com o Ollama.
- Quais recursos do modelo serão necessários para o agente.

A escolha do modelo deverá considerar o desempenho da máquina e as tarefas previstas.

---

8. Instalação e execução local

Tony deverá ser mantido em um repositório GitHub e executado na minha máquina.

A ideia inicial é semelhante à instalação de um projeto de software convencional:

1. Obter o código do repositório.
2. Preparar o ambiente Python.
3. Instalar as dependências do projeto.
4. Instalar e configurar o Ollama, caso ainda não esteja disponível.
5. Baixar um modelo compatível.
6. Configurar Tony para utilizar o modelo.
7. Executar o agente localmente.

Em uma etapa posterior, o projeto poderá ser preparado para oferecer um comando próprio no terminal, como "tony", para iniciar o assistente.

Isso exigirá configurar o projeto como um pacote executável ou criar uma forma equivalente de inicialização.

Máquina local e máquina virtual

Tony poderá ser executado em uma máquina virtual, desde que o ambiente tenha os recursos necessários.

Entretanto, a localização dos arquivos importa:

- Se Tony estiver executando dentro de uma máquina virtual, ele terá acesso aos arquivos disponibilizados naquele ambiente.
- Para acessar documentos do sistema hospedeiro, será necessário disponibilizar esses arquivos à máquina virtual de maneira apropriada.
- O modelo local também precisará de recursos de processamento e memória suficientes.

A decisão entre executar Tony diretamente no Linux ou dentro de uma máquina virtual ficará para o planejamento técnico.

---

9. GitHub e evolução do projeto

O repositório do Tony será utilizado para manter o código, a documentação e o histórico de desenvolvimento.

Quero que o projeto evolua gradualmente, com novas funcionalidades, correções e melhorias.

Organização conceitual do desenvolvimento

Cada alteração deverá poder ser registrada no Git.

Exemplos:

- Adicionar uma ferramenta de leitura de arquivos.
- Melhorar a interpretação de datas.
- Corrigir um erro no fluxo de execução.
- Adicionar suporte a outro formato de documento.
- Melhorar as instruções do agente.
- Adicionar integração com uma caixa de e-mail.

O GitHub permitirá acompanhar as mudanças e recuperar versões anteriores.

O código versionado será o projeto Tony. O Ollama e os pesos do modelo serão componentes separados, salvo se houver uma decisão futura específica de distribuição.

---

10. Identidade, instruções e comportamento do Tony

Tony deverá ter uma identidade definida por mim.

Essa identidade poderá incluir:

- Nome e descrição do assistente.
- Objetivo principal.
- Tom de comunicação.
- Instruções de comportamento.
- Limites de atuação.
- Tipos de tarefas que deve priorizar.
- Regras sobre quando pedir esclarecimentos.
- Regras sobre quando solicitar confirmação antes de executar ações.

Essas características poderão ser definidas por instruções enviadas ao modelo e pela lógica do próprio agente.

A identidade do Tony não exige que o modelo seja treinado novamente.

A personalização inicial será feita por meio das instruções, do contexto e das ferramentas disponíveis.

---

11. Cuidados com permissões e segurança

Como Tony poderá acessar arquivos e, futuramente, serviços pessoais, será importante definir limites claros.

O agente não deverá receber acesso irrestrito ao computador apenas porque utiliza um modelo local.

Pontos a considerar:

- Restringir o acesso aos diretórios necessários.
- Separar leitura de escrita e exclusão.
- Solicitar confirmação antes de operações destrutivas ou sensíveis.
- Evitar armazenar senhas, tokens e credenciais no repositório.
- Definir como os dados pessoais serão tratados.
- Considerar que documentos e e-mails podem conter informações sensíveis.
- Registrar as ações importantes executadas pelo agente.

Executar o modelo localmente pode reduzir a necessidade de enviar solicitações a um serviço de IA externo, mas não garante, por si só, que todos os dados permanecerão locais. Isso dependerá da arquitetura e das integrações utilizadas.

---

12. Publicação do projeto, licenças e autoria

A intenção é publicar o código do Tony no GitHub, mantendo o projeto organizado e documentado.

Utilizar Ollama ou um modelo de linguagem existente não torna automaticamente Tony um projeto plagiado.

Entretanto, é necessário respeitar as licenças dos componentes utilizados.

Pontos importantes

- O código desenvolvido para Tony deverá ter uma licença escolhida para o repositório, caso eu queira autorizar outras pessoas a utilizá-lo ou modificá-lo.
- As bibliotecas utilizadas possuem suas próprias licenças.
- O modelo escolhido no Ollama também possui uma licença específica.
- Caso o modelo seja distribuído junto com Tony, será necessário verificar as condições aplicáveis à redistribuição.
- Código gerado por IA não dispensa a verificação de possíveis semelhanças com código de terceiros.

Uma possibilidade é publicar o código do Tony e documentar que ele utiliza Ollama, deixando que cada pessoa instale o Ollama e baixe separadamente um modelo compatível.

A licença definitiva deverá ser escolhida depois de definir como o projeto será compartilhado.

Esta seção registra cuidados gerais, não constitui um parecer jurídico.

---

13. Escopo inicial e decisões ainda pendentes

O conceito está definido, mas a arquitetura técnica ainda não foi fechada.

Definições já estabelecidas

- Tony será meu próprio agente.
- Python será a linguagem principal.
- Ollama será considerado como mecanismo para executar o modelo de linguagem.
- A interação deverá ocorrer em linguagem natural.
- O agente terá ferramentas para executar tarefas concretas.
- O código será mantido no GitHub.
- A execução local é um objetivo importante.
- O projeto deverá permitir evolução incremental.
- A leitura e análise de e-mails da escola é uma das primeiras funcionalidades imaginadas.

Decisões para a fase de planejamento

1. Definir o primeiro objetivo funcional do Tony.
2. Escolher o modelo de linguagem.
3. Definir a estrutura do projeto Python.
4. Escolher como o usuário interagirá com Tony inicialmente: terminal ou interface.
5. Definir quais ferramentas serão implementadas primeiro.
6. Estabelecer permissões para arquivos locais.
7. Decidir se Tony será executado diretamente no Linux ou em uma máquina virtual.
8. Planejar a integração com e-mails.
9. Definir testes, documentação e estratégia de versionamento.
10. Escolher a licença do projeto, se ele for publicado para reutilização por outras pessoas.

---

14. Caminho sugerido para o primeiro protótipo

Para evitar começar com muitas integrações ao mesmo tempo, o protótipo poderá ser dividido em etapas.

Etapa 1 — Tony conversa

Criar uma estrutura mínima que permita enviar uma mensagem em linguagem natural ao modelo local e receber uma resposta.

Etapa 2 — Tony utiliza uma ferramenta

Disponibilizar uma ferramenta simples de leitura de um arquivo autorizado.

Etapa 3 — Tony interpreta documentos

Permitir que o agente receba um pedido para localizar, ler e resumir um documento.

Etapa 4 — Tony organiza informações

Adicionar a capacidade de identificar datas e extrair informações relevantes de documentos.

Etapa 5 — Tony integra e-mails

Planejar e implementar uma integração autorizada com a caixa de entrada da escola.

Etapa 6 — Tony evolui como projeto

Organizar a instalação, os testes, a documentação, as versões e os novos recursos.

---

15. Resumo do conceito

Tony será um assistente pessoal próprio, construído em Python, que utilizará um modelo de linguagem executado pelo Ollama.

O modelo será responsável por auxiliar na compreensão de linguagem natural e na produção de respostas. O código Python coordenará o agente e executará as ferramentas autorizadas, como leitura de arquivos e, futuramente, consulta a e-mails.

O projeto será versionado no GitHub, executado localmente e desenvolvido por etapas.

O objetivo imediato não é construir um modelo de IA do zero, mas criar uma aplicação inteligente que reúna um modelo existente, instruções próprias, ferramentas e uma arquitetura que possa crescer conforme as minhas necessidades.

Próximo passo: transformar este contexto em um planejamento técnico do Tony, definindo o primeiro protótipo, a estrutura do projeto Python, o modelo local e o fluxo inicial de execução.

repositório: (ainda não existe).