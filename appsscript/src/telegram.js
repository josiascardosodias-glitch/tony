/**
 * O Tony no Telegram pelo Apps Script (o `tony/telegram.py` em JavaScript).
 *
 * - As mensagens chegam por webhook (`doPost` do App da Web). O segredo vai na URL (`?k=...`), porque o
 *   `doPost` não lê cabeçalhos; e só o seu chat (`TELEGRAM_CHAT_ID`) é atendido.
 * - O webhook responde em HTML (200): a resposta de texto do Apps Script é um 302, que trava a fila do
 *   Telegram. Mesmo assim, o Tony guarda o maior `update_id` já tratado e ignora o que vier repetido.
 * - Pergunta de agenda é respondida pelo código (zero token); pergunta livre vai ao modelo.
 * - Data de confiança média chega com Aceitar e Descartar; `/remover` (ou o 🗑) tira um compromisso já
 *   aceito, com confirmação.
 */

const AJUDA = `Pode perguntar do jeito que quiser: "o que tenho amanhã?", "e sexta?", "semana que vem".

/hoje · /semana · /proximos — o que está marcado
/revisar — as datas que eu não tive certeza
/remover — tirar da agenda um compromisso que já aceitei
/coletar — olhar os e-mails agora
/nova — esquecer esta conversa`;

const MAXIMO_DE_UMA_VEZ = 3;   // mais datas novas que isso numa coleta viram uma mensagem só
const REMOVER_NO_MAXIMO = 30;  // botões do /remover: os compromissos mais próximos

// --- API do Telegram ------------------------------------------------------------------------------

class ErroDoTelegram extends Error {}

function chamarTelegram(metodo, dados) {
  const token = segredo('TELEGRAM_TOKEN');
  let corpo;
  try {
    const r = _buscar(`https://api.telegram.org/bot${token}/${metodo}`, {
      method: 'post', contentType: 'application/json', payload: JSON.stringify(dados || {}), muteHttpExceptions: true });
    corpo = JSON.parse(r.getContentText());
  } catch (e) {
    throw new ErroDoTelegram(String(e.message || e).split(token).join('<token>')); // o token vai na URL: nunca no erro
  }
  if (!corpo.ok) throw new ErroDoTelegram(`${metodo}: ${corpo.description || 'erro sem descrição'}`);
  return corpo.result;
}

function _chatId() {
  return Number(segredo('TELEGRAM_CHAT_ID'));
}

function enviar(texto, botoes) {
  const dados = { chat_id: _chatId(), text: texto.slice(0, 4000) };
  if (botoes && botoes.length) dados.reply_markup = { inline_keyboard: botoes };
  return chamarTelegram('sendMessage', dados);
}

// --- Estado ---------------------------------------------------------------------------------------

function _estado() {
  return ler('telegram', { maior_update: 0, avisados: [] });
}

function _salvarEstado(estado) {
  estado.avisados = estado.avisados.slice(-2000);
  guardar('telegram', estado);
}

function _eventos() {
  return ler('eventos', { eventos: {}, revisar: {} });
}

// --- Botões ---------------------------------------------------------------------------------------

function botoesDeRevisar(id) {
  return [[{ text: '✅ Aceitar', callback_data: `aceitar:${id}` }, { text: '🗑 Descartar', callback_data: `descartar:${id}` }]];
}

function quando(e) {
  return `${ddmm(e.data)}${e.hora ? ' ' + e.hora : ''}`;
}

/** Uma linha com o botão que pede para remover (a confirmação vem depois). */
function botaoRemover(e, comTitulo) {
  const texto = comTitulo === false ? '🗑 Remover da agenda' : `🗑 ${quando(e)} · ${e.titulo}`;
  return [{ text: fatiar(texto, 60), callback_data: `remover:${e.id}` }];
}

// --- Coleta ---------------------------------------------------------------------------------------

/** Coleta as contas, leva para a agenda e avisa o que entrou. Uma conta com problema não para as outras. */
function rodarColeta(agora, avisarVazio) {
  agora = agora || new Date();
  const antes = new Set(Object.keys(_eventos().eventos));
  let lidos = 0;
  CONTAS_DO_TONY.forEach((conta, i) => {
    try {
      lidos += coletar(fonteDe(conta), conta, agora, i === 0).emails;
    } catch (e) {
      console.warn(`a coleta de ${conta.nome} falhou: ${e}`);
      if (e instanceof AutorizacaoVencida) avisarUmaVezPorDia(conta.nome, e.message, agora, avisarVazio);
      else if (avisarVazio) enviar(`A coleta de ${conta.nome} falhou agora (${e.message || e}). Tento de novo na próxima.`);
    }
  });
  try {
    sincronizar(emBrasilia(agora).data);
  } catch (e) {
    console.warn(`a agenda falhou: ${e}`);
  }
  const banco = _eventos();
  const novos = Object.entries(banco.eventos).filter(([i]) => !antes.has(i)).map(([, e]) => e).sort(porDataEHora);
  if (novos.length) {
    const linhas = novos.map(e => `• ${quando(e).replace(' ', ', ')} — ${e.titulo}`).join('\n');
    if (novos.length <= REMOVER_NO_MAXIMO) {
      enviar(`Pus na agenda:\n${linhas}\n\nNão é compromisso? Toque para tirar.`, novos.map(e => botaoRemover(e)));
    } else {
      enviar(`Pus na agenda:\n${linhas}\n\n/remover tira o que não for compromisso.`);
    }
  }
  avisarRevisar(banco, false, agora);
  if (avisarVazio && !novos.length) enviar(`Olhei ${lidos} e-mail(s) novo(s): nada para a agenda.`);
}

/** Uma vez por dia por conta (ou sempre, num /coletar): a autorização venceu e como renovar. */
function avisarUmaVezPorDia(conta, texto, agora, sempre) {
  const estado = _estado();
  const hoje = emBrasilia(agora).data;
  estado.avisos_autorizacao = estado.avisos_autorizacao || {};
  if (estado.avisos_autorizacao[conta] === hoje && !sempre) return;
  enviar(`Não consegui olhar os e-mails de ${conta}: ${texto}.`);
  estado.avisos_autorizacao[conta] = hoje;
  _salvarEstado(estado);
}

/** Cada data de confiança média chega uma vez, com os botões. Muitas de uma vez viram uma mensagem só. */
function avisarRevisar(banco, todas, agora) {
  banco = banco || _eventos();
  const hoje = emBrasilia(agora || new Date()).data;
  const estado = _estado();
  const novas = Object.entries(banco.revisar).sort((a, b) => (a[1].data < b[1].data ? -1 : a[1].data > b[1].data ? 1 : 0))
    .filter(([i, e]) => !estado.avisados.includes(i) && e.data >= hoje);
  if (novas.length > MAXIMO_DE_UMA_VEZ && !todas) {
    enviar(`Tenho ${novas.length} datas que não sei se são compromisso. Mande /revisar para ver uma por uma.`);
    estado.avisados.push(...novas.map(([i]) => i));
    _salvarEstado(estado);
    return;
  }
  for (const [id, e] of novas) {
    enviar(`Isto é compromisso?\n\n${e.titulo}\n${ddmm(e.data)}${e.hora ? ' às ' + e.hora : ''}\n` +
      `${fatiar(e.descricao.split('\n')[0], 200)}\n(de ${e.remetente})`, botoesDeRevisar(id));
    estado.avisados.push(id);
    _salvarEstado(estado);
  }
}

// --- Mensagens ------------------------------------------------------------------------------------

function tratar(atualizacao, agora) {
  if (atualizacao.callback_query) return botao(atualizacao.callback_query);
  const mensagem = atualizacao.message || {};
  if ((mensagem.chat || {}).id !== _chatId()) {
    console.warn(`mensagem ignorada de outro chat: ${(mensagem.chat || {}).id}`);
    return;
  }
  const texto = (mensagem.text || '').trim();
  if (!texto) return;
  const resposta = responder(texto, agora);
  if (resposta) enviar(resposta);
}

function responder(texto, agora) {
  const hoje = emBrasilia(agora).data;
  const banco = _eventos();
  const eventos = Object.values(banco.eventos);
  const comando = texto.startsWith('/') ? texto.split(/\s+/)[0].split('@')[0].toLowerCase() : '';
  if (['/start', '/ajuda', '/help'].includes(comando)) return AJUDA;
  if (['/hoje', '/semana', '/proximos'].includes(comando)) {
    return responderAgenda({ '/hoje': 'hoje', '/semana': 'essa semana', '/proximos': 'o mês' }[comando], eventos, hoje);
  }
  if (comando === '/revisar') {
    const pendentes = Object.entries(banco.revisar).filter(([, e]) => e.data >= hoje).map(([i]) => i);
    const estado = _estado();
    estado.avisados = estado.avisados.filter(i => !pendentes.includes(i));
    _salvarEstado(estado);
    avisarRevisar(banco, true, agora);
    return pendentes.length ? '' : 'Nada para revisar.';
  }
  if (comando === '/coletar') {
    rodarColeta(agora, true);
    return '';
  }
  if (comando === '/remover') return listarParaRemover(agora);
  if (comando === '/nova') {
    esquecerConversa();
    return 'Conversa nova.';
  }
  if (comando) return 'Não conheço esse comando. /ajuda mostra o que eu faço.';
  if (ehDeAgenda(texto, hoje)) return responderAgenda(texto, eventos, hoje);
  return conversar(texto, eventos, agora);
}

/** Os compromissos de hoje em diante, um botão cada; o toque pede confirmação. */
function listarParaRemover(agora) {
  const hoje = emBrasilia(agora).data;
  const futuros = Object.values(_eventos().eventos).filter(e => e.data >= hoje).sort(porDataEHora);
  if (!futuros.length) return 'Não tenho nenhum compromisso na agenda para tirar.';
  const extra = futuros.length > REMOVER_NO_MAXIMO ? `\n(os ${REMOVER_NO_MAXIMO} mais próximos; tem ${futuros.length})` : '';
  enviar(`Qual compromisso eu tiro da agenda?${extra}`, futuros.slice(0, REMOVER_NO_MAXIMO).map(e => botaoRemover(e)));
  return '';
}

function botao(clique) {
  const mensagem = clique.message || {};
  if ((mensagem.chat || {}).id !== _chatId()) return;
  const dados = clique.data || '';
  const acao = dados.split(':')[0], id = dados.slice(acao.length + 1);
  let botoesDepois = null, resultado;
  if (acao === 'remover') { // primeiro toque: só pergunta
    const e = _eventos().eventos[id];
    chamarTelegram('answerCallbackQuery', { callback_query_id: clique.id, text: e ? '' : 'esse já não está na agenda.' });
    if (!e) return; // a lista continua com os outros botões
    enviar(`Tiro da agenda?\n\n${e.titulo}\n${quando(e)}\n(de ${e.remetente})\n\nOutro e-mail sobre o mesmo compromisso também não volta.`,
      [[{ text: '🗑 Sim, tirar', callback_data: `tirar:${id}` }, { text: '↩ Deixar', callback_data: `deixar:${id}` }]]);
    return;
  }
  if (acao === 'deixar') {
    resultado = 'ficou na agenda.';
  } else if (acao === 'tirar') {
    resultado = remover(id);
  } else {
    resultado = decidir(id, acao === 'aceitar');
    if (acao === 'aceitar' && resultado.startsWith('aceito')) {
      try {
        sincronizar();
        resultado += ' Está na agenda.';
      } catch (e) {
        resultado += ' Vai para a agenda na próxima coleta.';
      }
      const e = _eventos().eventos[id];
      if (e) botoesDepois = [botaoRemover(e, false)]; // mudou de ideia depois? dá para tirar daqui mesmo
    }
  }
  chamarTelegram('answerCallbackQuery', { callback_query_id: clique.id, text: resultado.slice(0, 190) });
  const editar = { chat_id: _chatId(), message_id: mensagem.message_id, text: `${mensagem.text || ''}\n\n→ ${resultado}`.slice(0, 4000) };
  if (botoesDepois) editar.reply_markup = { inline_keyboard: botoesDepois };
  chamarTelegram('editMessageText', editar);
}

// --- Webhook --------------------------------------------------------------------------------------

/** Trata uma atualização uma vez só. Devolve true se tratou. */
function receber(atualizacao, agora) {
  const estado = _estado();
  if (atualizacao.update_id <= (estado.maior_update || 0)) return false; // reenvio do Telegram
  estado.maior_update = atualizacao.update_id;
  _salvarEstado(estado); // antes de tratar: uma mensagem que derruba o Tony não volta em loop
  try {
    tratar(atualizacao, agora || new Date());
  } catch (e) {
    console.error(`erro tratando a atualização ${atualizacao.update_id}: ${e.stack || e}`);
    try {
      enviar(`Deu um erro aqui (${e.message || e}). Tenta de novo daqui a pouco.`);
    } catch (e2) { /* sem Telegram, só o registro */ }
  }
  return true;
}

function _comTrava(fn) {
  const trava = typeof TRAVA_FALSA !== 'undefined' ? TRAVA_FALSA : LockService.getScriptLock();
  if (!trava.tryLock(28000)) return null; // outra execução está gravando; o Telegram reenvia
  try {
    return fn();
  } finally {
    trava.releaseLock();
  }
}

function doPost(e) {
  // Para o Telegram, HTML: a resposta de texto (ContentService) vem como um redirecionamento 302, que o
  // Telegram trata como erro e reenvia sem parar, travando a fila. O HtmlService responde 200 direto.
  const resposta = () => HtmlService.createHtmlOutput('ok');
  if (e && e.parameter && e.parameter.faccat) { // o script da Faccat mandando prazos e e-mails
    const segredoDaFaccat = _propriedades().getProperty('FACCAT_SEGREDO');
    if (!segredoDaFaccat || e.parameter.faccat !== segredoDaFaccat || !e.postData) return resposta();
    let saida;
    try {
      saida = _comTrava(() => ({ ok: true, ...receberFaccat(JSON.parse(e.postData.contents), new Date()) })) || { ok: false, erro: 'ocupado' };
    } catch (erro) {
      saida = { ok: false, erro: String(erro.message || erro) };
    }
    return ContentService.createTextOutput(JSON.stringify(saida)).setMimeType(ContentService.MimeType.JSON);
  }
  if (e && e.parameter && e.parameter.admin) { // o PC (appsscript/configurar.py), não o Telegram
    const admin = _propriedades().getProperty('ADMIN_SEGREDO');
    if (!admin || e.parameter.admin !== admin || !e.postData) return resposta();
    let saida;
    try {
      saida = _comTrava(() => ({ ok: true, ...administrar(JSON.parse(e.postData.contents)) })) || { ok: false, erro: 'ocupado' };
    } catch (erro) {
      saida = { ok: false, erro: String(erro.message || erro) };
    }
    return ContentService.createTextOutput(JSON.stringify(saida)).setMimeType(ContentService.MimeType.JSON);
  }
  if (!e || !e.parameter || e.parameter.k !== segredo('WEBHOOK_SEGREDO') || !e.postData) return resposta();
  let atualizacao;
  try {
    atualizacao = JSON.parse(e.postData.contents);
  } catch (erro) {
    return resposta();
  }
  _comTrava(() => receber(atualizacao, new Date()));
  return resposta();
}

/** Abrir a URL no navegador não mostra nada (e não diz que o Tony está ali). */
function doGet() {
  return ContentService.createTextOutput('');
}
