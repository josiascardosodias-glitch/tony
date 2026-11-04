/**
 * Faccat → Tony, sem URL pública (Tony v5.2).
 *
 * Cole este arquivo como um arquivo NOVO no projeto do Apps Script da Faccat (o que tem o doGet do Tony).
 * Ele não muda nada do que já existe: chama o mesmo doGet por dentro, com a chave que o projeto já tem
 * (TONY_CHAVE), e manda o resultado para o Tony de hora em hora. Depois, a implantação pública da
 * Faccat pode ser arquivada.
 *
 * Uma vez só, depois de colar:
 * 1. Configurações do projeto > Propriedades do script > adicionar TONY_URL com o endereço que o PC
 *    gerou (~/.config/tony/faccat-url-do-tony: `cat` no terminal e copie).
 * 2. Rode instalarGatilhoDoTony() no editor e aceite as permissões (chamar serviço externo e gatilhos).
 * 3. Rode enviarAoTony() uma vez e veja no registro "Tony recebeu".
 */

const TONY_FOLGA_MS = 60 * 60 * 1000;  // uma hora para trás: o Tony ignora o que já viu

function enviarAoTony() {
  const props = PropertiesService.getScriptProperties();
  const url = props.getProperty('TONY_URL');
  const chave = props.getProperty('TONY_CHAVE');
  if (!url || !chave) throw new Error('faltam as propriedades TONY_URL e/ou TONY_CHAVE');
  const ultimo = Number(props.getProperty('TONY_ULTIMO_ENVIO') || 0);
  const desde = ultimo ? ultimo - TONY_FOLGA_MS : Date.now() - 30 * 24 * 3600 * 1000;
  const agora = Date.now();

  // O mesmo pedido que o Tony fazia pela URL pública, agora por dentro do script.
  const saida = doGet({ parameter: { chave: chave, desde: String(Math.floor(desde / 1000)), filtro: '-category:promotions -category:social' } });
  const dados = JSON.parse(saida.getContent());
  if (dados.erro) throw new Error('o doGet recusou: ' + dados.erro);

  const resposta = UrlFetchApp.fetch(url, {
    method: 'post', contentType: 'application/json', payload: JSON.stringify(dados),
    muteHttpExceptions: true, followRedirects: true,
  });
  let corpo;
  try {
    corpo = JSON.parse(resposta.getContentText());
  } catch (e) {
    throw new Error('o Tony não respondeu direito (HTTP ' + resposta.getResponseCode() + ')');
  }
  if (!corpo.ok) throw new Error('o Tony recusou: ' + (corpo.erro || 'sem descrição'));
  props.setProperty('TONY_ULTIMO_ENVIO', String(agora));
  console.log('Tony recebeu: ' + corpo.prazos + ' prazo(s), ' + corpo.emails_novos + ' e-mail(s) novo(s).');
}

function instalarGatilhoDoTony() {
  for (const g of ScriptApp.getProjectTriggers()) {
    if (g.getHandlerFunction() === 'enviarAoTony') ScriptApp.deleteTrigger(g);
  }
  ScriptApp.newTrigger('enviarAoTony').timeBased().everyHours(1).create();
  console.log('gatilho do Tony instalado: enviarAoTony de hora em hora.');
}
