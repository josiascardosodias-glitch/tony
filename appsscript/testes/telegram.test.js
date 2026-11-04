// O bot com Telegram, modelo e propriedades falsos (os testes do testes/test_telegram.py, mais o webhook).
const test = require('node:test');
const assert = require('node:assert/strict');
const { carregar } = require('./carregar');

const MEU_CHAT = 7000;
const AGORA = new Date('2026-11-03T13:00:00Z'); // 10:00 em Brasília, terça
const json = x => JSON.parse(JSON.stringify(x));

class Propriedades {
  constructor(dados) { this.dados = { ...dados }; }
  getProperty(k) { return k in this.dados ? this.dados[k] : null; }
  setProperties(o) { Object.assign(this.dados, o); }
  deleteProperty(k) { delete this.dados[k]; }
  getProperties() { return { ...this.dados }; }
}

const evento = (id, data, titulo, hora = null) => ({ id, email: id.slice(0, 2), conta: 'pessoal', remetente: 'x@y.com',
  nome: '', titulo, data, hora, descricao: `${titulo}, frase do e-mail.`, origem: 'corpo', confianca: 0.9, link: '',
  recebido: '', criado_em: '', evento_agenda: null });

/** Um Tony com Telegram e Ollama falsos: `enviadas` (sendMessage), `chamadas` (o resto), `modelo` (prompts). */
function montar({ modeloFalha = false } = {}) {
  const props = new Propriedades({ 'TELEGRAM_TOKEN': '123:SEGREDO', 'TELEGRAM_CHAT_ID': String(MEU_CHAT),
    'OLLAMA_CHAVE': 'chave', 'WEBHOOK_SEGREDO': 'abc' });
  const s = { enviadas: [], chamadas: [], modelo: [], apagados: [] };
  const resposta = (codigo, corpo) => ({ getResponseCode: () => codigo, getContentText: () => JSON.stringify(corpo) });
  const buscar = (url, opcoes) => {
    const dados = JSON.parse(opcoes.payload);
    if (url.startsWith('https://ollama.com')) {
      s.modelo.push(dados.messages);
      return modeloFalha ? resposta(503, { error: 'sobrecarregado' }) : resposta(200, { message: { content: 'Resposta do modelo.' } });
    }
    const metodo = url.split('/').pop();
    if (metodo === 'sendMessage') s.enviadas.push({ texto: dados.text, botoes: (dados.reply_markup || {}).inline_keyboard });
    else s.chamadas.push([metodo, dados]);
    return resposta(200, { ok: true, result: {} });
  };
  const calendario = {
    Calendars: { insert: () => ({ id: 'agenda-1' }) },
    Events: { remove: (agenda, id) => s.apagados.push(id), list: () => ({ items: [] }), insert: () => ({ id: 'ev-novo' }) },
  };
  const tony = carregar({ PROPRIEDADES_FALSAS: props, BUSCAR_FALSO: buscar, CALENDARIO_FALSO: calendario,
    TRAVA_FALSA: { tryLock: () => true, releaseLock: () => {} } });
  tony.guardar('eventos', { eventos: { 'm1-1': evento('m1-1', '2026-11-05', 'Oktober Summit', '08:30') },
    revisar: { 'r1-1': evento('r1-1', '2026-11-10', 'Talvez reunião') } });
  tony.guardar('agenda', { id: 'agenda-1' });
  return { tony, s, props };
}

const mensagem = (texto, chat = MEU_CHAT, n = 1) => ({ update_id: n, message: { chat: { id: chat }, text: texto } });
const clique = (dados, n = 2) => ({ update_id: n, callback_query: { id: `c${n}`, data: dados,
  message: { chat: { id: MEU_CHAT }, message_id: 9, text: '?' } } });

test('pergunta de agenda não gasta token', () => {
  const { tony, s } = montar();
  tony.tratar(mensagem('o que eu tenho quinta?'), AGORA);
  assert.equal(s.modelo.length, 0);
  assert.match(s.enviadas[0].texto, /Oktober Summit/);
});

test('conversa livre vai ao modelo com a agenda, sem o que está em revisar', () => {
  const { tony, s } = montar();
  tony.tratar(mensagem('me explica o que é uma closure'), AGORA);
  assert.equal(s.modelo.length, 1);
  const sistema = s.modelo[0][0].content;
  assert.match(sistema, /Oktober Summit/);
  assert.match(sistema, /terça-feira, 03\/11\/2026, 10:00/);
  assert.doesNotMatch(sistema, /Talvez reunião/);
  assert.equal(s.enviadas[0].texto, 'Resposta do modelo.');
});

test('a conversa continua entre mensagens e esquece depois de 30 minutos', () => {
  const { tony, s } = montar();
  tony.tratar(mensagem('oi Tony, tudo certo?'), AGORA);
  tony.tratar(mensagem('e o que você acha disso?', MEU_CHAT, 2), new Date(AGORA.getTime() + 5 * 60000));
  assert.equal(s.modelo[1].length, 4); // sistema, fala 1, resposta 1, fala 2
  tony.tratar(mensagem('e agora?', MEU_CHAT, 3), new Date(AGORA.getTime() + 60 * 60000));
  assert.equal(s.modelo[2].length, 2); // conversa nova
  assert.equal(tony.responder('/nova', AGORA), 'Conversa nova.');
  assert.equal(tony.ler('conversa'), null);
});

test('modelo fora do ar: avisa, e a fala não fica no histórico', () => {
  const { tony, s } = montar({ modeloFalha: true });
  tony.tratar(mensagem('me conta uma piada'), AGORA);
  assert.match(s.enviadas[0].texto, /Não consegui falar com o modelo agora \(Ollama respondeu 503: sobrecarregado\)/);
  assert.equal(tony.ler('conversa'), null);
});

test('outro chat é ignorado', () => {
  const { tony, s } = montar();
  tony.tratar(mensagem('o que eu tenho quinta?', 666), AGORA);
  tony.tratar(mensagem('me conta um segredo', 666), AGORA);
  assert.deepEqual([s.enviadas.length, s.modelo.length], [0, 0]);
});

test('revisar chega com botões uma vez; muitas viram uma mensagem e o /revisar mostra uma por uma', () => {
  const { tony, s } = montar();
  tony.avisarRevisar(null, false, AGORA);
  tony.avisarRevisar(null, false, AGORA);
  assert.equal(s.enviadas.length, 1);
  assert.equal(s.enviadas[0].botoes[0][0].callback_data, 'aceitar:r1-1');
  const revisar = {};
  for (let n = 0; n < 5; n++) revisar[`r${n}-9`] = evento(`r${n}-9`, '2026-11-10', `Promo ${n}`);
  tony.guardar('eventos', { eventos: {}, revisar });
  tony.avisarRevisar(null, false, AGORA);
  assert.match(s.enviadas[1].texto, /5 datas/);
  tony.responder('/revisar', AGORA);
  assert.equal(s.enviadas.length, 7);
});

test('botão descartar e botão de outro chat', () => {
  const { tony, s } = montar();
  const outro = clique('aceitar:r1-1');
  outro.callback_query.message.chat.id = 666;
  tony.tratar(outro, AGORA);
  assert.ok('r1-1' in tony.ler('eventos').revisar);
  tony.tratar(clique('descartar:r1-1'), AGORA);
  const banco = tony.ler('eventos');
  assert.deepEqual(json([banco.revisar, banco.descartados]), [{}, ['r1-1']]);
  assert.deepEqual(s.chamadas.map(([m]) => m), ['answerCallbackQuery', 'editMessageText']);
});

test('aceitar deixa o botão de remover', () => {
  const { tony, s } = montar();
  tony.tratar(clique('aceitar:r1-1'), AGORA);
  const editada = s.chamadas[s.chamadas.length - 1][1];
  assert.match(editada.text, /aceito: Talvez reunião .* Está na agenda\./);
  assert.equal(editada.reply_markup.inline_keyboard[0][0].callback_data, 'remover:r1-1');
});

test('remover pede confirmação e só o "Sim, tirar" apaga', () => {
  const { tony, s } = montar();
  const banco = tony.ler('eventos');
  banco.eventos['m1-1'].evento_agenda = 'ev-1';
  tony.guardar('eventos', banco);
  assert.equal(tony.responder('/remover', AGORA), '');
  assert.equal(s.enviadas[0].botoes[0][0].callback_data, 'remover:m1-1');
  tony.tratar(clique('remover:m1-1'), AGORA);
  assert.match(s.enviadas[1].texto, /Tiro da agenda\?/);
  assert.ok('m1-1' in tony.ler('eventos').eventos);
  tony.tratar(clique('deixar:m1-1', 3), AGORA);
  assert.ok('m1-1' in tony.ler('eventos').eventos);
  tony.tratar(clique('tirar:m1-1', 4), AGORA);
  const depois = tony.ler('eventos');
  assert.deepEqual(json([depois.eventos, depois.removidos, s.apagados]), [{}, ['m1-1'], ['ev-1']]);
  assert.match(tony.responder('/remover', AGORA), /nenhum compromisso/);
});

test('comandos', () => {
  const { tony, s } = montar();
  assert.match(tony.responder('/ajuda', AGORA), /\/remover/);
  assert.match(tony.responder('/semana', AGORA), /Oktober Summit/);
  assert.match(tony.responder('/xyz', AGORA), /Não conheço/);
  assert.equal(s.modelo.length, 0);
});

test('coleta avisa o que pôs na agenda, com o botão de tirar', () => {
  const { tony, s } = montar();
  const fonte = { * mensagens() {
    yield { id: 'n1', de: 'rh@empresa.com', nome: 'RH', assunto: 'Entrevista', recebido: AGORA,
      texto: 'Sua entrevista é dia 12/11 às 14h.', trecho: '', convites: [], emailDaConta: '', emMassa: false };
  } };
  const tonyComFonte = carregar({ ...montarContexto(tony), FONTE_FALSA: fonte });
  tonyComFonte.rodarColeta(AGORA, false);
  const aviso = tonyComFonte.__enviadas.find(m => /Pus na agenda/.test(m.texto));
  assert.match(aviso.texto, /• 12\/11, 14:00 — Entrevista/);
  assert.equal(aviso.botoes[0][0].callback_data, 'remover:n1-1');
});

/** Um contexto novo com as mesmas propriedades do `tony` (para trocar a fonte da coleta). */
function montarContexto(tony) {
  const props = new Propriedades(tony.PROPRIEDADES_FALSAS.getProperties());
  const enviadas = [];
  const resposta = corpo => ({ getResponseCode: () => 200, getContentText: () => JSON.stringify(corpo) });
  return { PROPRIEDADES_FALSAS: props, __enviadas: enviadas, TRAVA_FALSA: tony.TRAVA_FALSA, CALENDARIO_FALSO: tony.CALENDARIO_FALSO,
    BUSCAR_FALSO: (url, op) => {
      if (url.endsWith('sendMessage')) {
        const d = JSON.parse(op.payload);
        enviadas.push({ texto: d.text, botoes: (d.reply_markup || {}).inline_keyboard });
      }
      return resposta({ ok: true, result: {} });
    } };
}

test('webhook: segredo errado não faz nada; reenvio do mesmo update_id é ignorado', () => {
  const { tony, s } = montar();
  const post = (k, atualizacao) => ({ parameter: { k }, postData: { contents: JSON.stringify(atualizacao) } });
  const contexto = carregar({ ...montarContexto(tony), ContentService: { createTextOutput: t => t } });
  assert.equal(contexto.doPost(post('errado', mensagem('/ajuda', MEU_CHAT, 10))), 'ok');
  assert.equal(contexto.__enviadas.length, 0);
  contexto.doPost(post('abc', mensagem('/ajuda', MEU_CHAT, 10)));
  contexto.doPost(post('abc', mensagem('/ajuda', MEU_CHAT, 10))); // o Telegram reenviando (302)
  contexto.doPost(post('abc', mensagem('/semana', MEU_CHAT, 9)));  // atrasado: já passou
  assert.equal(contexto.__enviadas.length, 1);
  contexto.doPost(post('abc', mensagem('/semana', MEU_CHAT, 11)));
  assert.equal(contexto.__enviadas.length, 2);
  assert.equal(s.enviadas.length, 0);
});

test('erro do Telegram não mostra o token', () => {
  const tony = carregar({ PROPRIEDADES_FALSAS: new Propriedades({ TELEGRAM_TOKEN: '123:SEGREDO', TELEGRAM_CHAT_ID: '1' }),
    BUSCAR_FALSO: url => { throw new Error(`falhou ${url}`); } });
  assert.throws(() => tony.enviar('oi'), e => !String(e.message).includes('SEGREDO') && /<token>/.test(e.message));
  const recusa = carregar({ PROPRIEDADES_FALSAS: new Propriedades({ TELEGRAM_TOKEN: '1:X', TELEGRAM_CHAT_ID: '1' }),
    BUSCAR_FALSO: () => ({ getContentText: () => JSON.stringify({ ok: false, description: 'chat not found' }) }) });
  assert.throws(() => recusa.enviar('oi'), /chat not found/);
});
