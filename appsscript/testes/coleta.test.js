// A coleta e a agenda com Gmail, Agenda e propriedades falsos. O principal: a mesma caixa de e-mail
// dá o mesmo `eventos` no Python e no JavaScript (casos de scripts/casos_appsscript.py).
const test = require('node:test');
const assert = require('node:assert/strict');
const casos = require('./casos.json');
const { carregar } = require('./carregar');

class Propriedades {
  constructor() { this.dados = {}; }
  getProperty(k) { return k in this.dados ? this.dados[k] : null; }
  setProperties(o) { Object.assign(this.dados, o); }
  deleteProperty(k) { delete this.dados[k]; }
  getProperties() { return { ...this.dados }; }
}

const decodificar = dados => Buffer.from(dados, 'base64url').toString('utf8');

/** Imita o Gmail dos testes Python: a busca tira os -from:, e o anexo .ics vem do `_ics`. */
function gmailFalso(caixa) {
  const porId = Object.fromEntries(caixa.map(m => [m.id, m]));
  return {
    buscas: [],
    buscar(q) {
      this.buscas.push(q);
      const bloqueados = q.split(' ').filter(p => p.startsWith('-from:')).map(p => p.slice(6));
      return caixa.filter(m => !bloqueados.some(b => m.payload.headers[0].value.includes(b))).map(m => m.id);
    },
    mensagem(id) { return JSON.parse(JSON.stringify(porId[id])); },
    anexo(idDaMensagem) { return { data: Buffer.from(porId[idDaMensagem]._ics).toString('base64url') }; },
  };
}

function novoTony() {
  const props = new Propriedades();
  const tony = carregar({ PROPRIEDADES_FALSAS: props, DECODIFICAR_FALSO: decodificar });
  return { tony, props };
}

const AGORA = new Date(casos.agora_coleta);
const json = x => JSON.parse(JSON.stringify(x));
const semCriadoEm = original => {
  const banco = json(original);
  for (const secao of ['eventos', 'revisar']) for (const e of Object.values(banco[secao])) delete e.criado_em;
  return banco;
};

test('coletar igual ao coletar do Python', () => {
  for (const c of casos.coletas) {
    const { tony } = novoTony();
    tony.guardar('bloqueados', { enderecos: ['spam@chato.com'], dominios: ['spam.org'] });
    const resumo = tony.coletar(tony.fonteGmail(gmailFalso(c.caixa)), { nome: 'pessoal', email: '' }, AGORA, true);
    const onde = c.caixa.map(m => m.id).join(',');
    assert.deepEqual(JSON.parse(JSON.stringify(resumo)), c.resumo, onde);
    assert.deepEqual(semCriadoEm(tony.ler('eventos')), c.banco, onde);
  }
});

test('segunda coleta não baixa de novo e a busca leva o after e os bloqueados', () => {
  const { tony } = novoTony();
  tony.guardar('bloqueados', { enderecos: ['spam@chato.com'], dominios: [] });
  const gmail = gmailFalso(casos.coletas[0].caixa);
  const conta = { nome: 'pessoal', email: '' };
  tony.coletar(tony.fonteGmail(gmail), conta, AGORA, true);
  const segunda = tony.coletar(tony.fonteGmail(gmail), conta, AGORA, true);
  assert.equal(segunda.emails, 0);
  assert.match(gmail.buscas[0], /^after:\d+ -category:promotions -category:social -from:spam@chato.com$/);
});

test('segunda conta: prefixo no id, link da conta, e o mesmo e-mail nas duas é um compromisso só', () => {
  const { tony } = novoTony();
  const caixa = casos.coletas[0].caixa;
  tony.coletar(tony.fonteGmail(gmailFalso(caixa)), { nome: 'pessoal', email: 'a@gmail.com' }, AGORA, true);
  tony.coletar(tony.fonteGmail(gmailFalso(caixa)), { nome: 'outra', email: 'b@gmail.com' }, AGORA, false);
  const banco = tony.ler('eventos');
  assert.ok('m1-1' in banco.eventos);
  assert.ok(!('outra.m1-1' in banco.eventos));
  assert.ok(banco.repetidos.includes('outra.m1-1'));
  assert.ok(tony.ler('coleta-outra').vistos.includes('m1'));
});

test('armazém divide JSON grande em pedaços e encolhe sem deixar sobra', () => {
  const { tony, props } = novoTony();
  tony.guardar('x', { texto: 'á'.repeat(20000) });
  assert.equal(props.getProperty('x#n'), '3');
  assert.equal(tony.ler('x').texto.length, 20000);
  tony.guardar('x', { texto: 'curto' });
  assert.deepEqual(Object.keys(props.dados).sort(), ['x#0', 'x#n']);
});

// --- Agenda ---------------------------------------------------------------------------------------

function calendarioFalso() {
  const cal = {
    agendas: [], eventos: [],
    Calendars: { insert: body => { const a = { id: `agenda-${cal.agendas.length + 1}`, ...body }; cal.agendas.push(a); return a; } },
    Events: {
      insert: (body, agenda) => { const e = { id: `ev-${cal.eventos.length + 1}`, agenda, ...body }; cal.eventos.push(e); return e; },
      list: (agenda, op) => ({ items: cal.eventos.filter(e => e.agenda === agenda &&
        `tony_id=${e.extendedProperties.private.tony_id}` === op.privateExtendedProperty) }),
      remove: (agenda, id) => {
        const antes = cal.eventos.length;
        cal.eventos = cal.eventos.filter(e => e.id !== id);
        if (cal.eventos.length === antes) throw new Error('API call to calendar.events.delete failed with error: Not Found (404)');
      },
    },
  };
  return cal;
}

function tonyComAgenda() {
  const props = new Propriedades();
  const cal = calendarioFalso();
  return { tony: carregar({ PROPRIEDADES_FALSAS: props, CALENDARIO_FALSO: cal }), cal };
}

const ev = (id, data, hora = '19:00', remetente = 'secretaria@faculdade.edu.br') => ({
  id, email: id.split('-')[0], conta: 'pessoal', remetente, nome: 'Secretaria', titulo: `Prova ${id}`, data, hora,
  descricao: 'A prova foi remarcada.', origem: 'corpo', confianca: 0.9, link: `https://mail.google.com/mail/u/0/#all/${id}`,
  recebido: '', criado_em: '', evento_agenda: null });

test('sincronizar cria uma vez, junta repetidos e não leva o passado', () => {
  const { tony, cal } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12'), 'm2-1': ev('m2-1', '2026-11-12'),
    'm3-1': ev('m3-1', '2026-11-20', null), 'm4-1': ev('m4-1', '2026-11-01') }, revisar: {} });
  assert.deepEqual({ ...tony.sincronizar('2026-11-03') }, { criados: 2, repetidos: 1, ja_estavam: 0 });
  assert.deepEqual({ ...tony.sincronizar('2026-11-03') }, { criados: 0, repetidos: 0, ja_estavam: 0 });
  assert.equal(cal.agendas.length, 1);
  assert.deepEqual(json(cal.eventos.map(e => [e.start, e.end])), [
    [{ dateTime: '2026-11-12T19:00:00', timeZone: 'America/Sao_Paulo' }, { dateTime: '2026-11-12T20:00:00', timeZone: 'America/Sao_Paulo' }],
    [{ date: '2026-11-20' }, { date: '2026-11-21' }]]);
});

test('evento às 23:30 termina no dia seguinte', () => {
  const { tony } = tonyComAgenda();
  assert.deepEqual({ ...tony.corpoDoEvento(ev('a-1', '2026-11-12', '23:30')).end }, { dateTime: '2026-11-13T00:30:00', timeZone: 'America/Sao_Paulo' });
});

test('eventos perdidos acham o que já estava no Google', () => {
  const { tony, cal } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12') }, revisar: {} });
  tony.sincronizar('2026-11-03');
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12') }, revisar: {} });
  assert.equal(tony.sincronizar('2026-11-03').ja_estavam, 1);
  assert.equal(cal.eventos.length, 1);
});

test('remover apaga no Google, leva o mesmo compromisso e não deixa voltar', () => {
  const { tony, cal } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12'), 'm3-1': ev('m3-1', '2026-11-20') }, revisar: {} });
  tony.sincronizar('2026-11-03');
  const banco = tony.ler('eventos');
  banco.eventos['m2-1'] = { ...ev('m2-1', '2026-11-12'), evento_agenda: banco.eventos['m1-1'].evento_agenda };
  tony.guardar('eventos', banco);
  assert.match(tony.remover('m2-1'), /removido: .* \(e mais 1 e-mail\(s\) do mesmo compromisso\)/);
  const depois = tony.ler('eventos');
  assert.deepEqual(Object.keys(depois.eventos), ['m3-1']);
  assert.deepEqual(json(depois.chaves_fora), [['secretaria@faculdade.edu.br', '2026-11-12', '19:00']]);
  assert.deepEqual(cal.eventos.map(e => e.id), ['ev-2']);
  assert.match(tony.remover('m3-1'), /removido/);
  cal.eventos = [];
  assert.match(tony.remover('x-1'), /não há/);
});

test('remover o que já foi apagado à mão não quebra', () => {
  const { tony, cal } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12') }, revisar: {} });
  tony.sincronizar('2026-11-03');
  cal.eventos = [];
  assert.match(tony.remover('m1-1'), /removido/);
});

test('aceitar, descartar e aceitar o que já está na agenda por outro e-mail', () => {
  const { tony } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'm1-1': ev('m1-1', '2026-11-12') },
    revisar: { 'r1-1': ev('r1-1', '2026-11-05'), 'r2-1': ev('r2-1', '2026-11-06'), 'r3-1': ev('r3-1', '2026-11-12') } });
  assert.match(tony.decidir('r1-1', true), /^aceito/);
  assert.match(tony.decidir('r2-1', false), /^descartado/);
  assert.match(tony.decidir('r3-1', true), /já estava na agenda/);
  assert.match(tony.decidir('r9-9', true), /não há/);
  const banco = tony.ler('eventos');
  assert.deepEqual(json([Object.keys(banco.eventos).sort(), banco.revisar, banco.descartados]), [['m1-1', 'r1-1'], {}, ['r2-1']]);
});

test('o executar tenta de novo só no erro passageiro', () => {
  const { tony } = novoTony();
  let vezes = 0;
  const esperas = [];
  assert.equal(tony.executar(() => { if (vezes++ < 2) throw new Error('Rate Limit Exceeded'); return 'ok'; }, s => esperas.push(s)), 'ok');
  assert.deepEqual(esperas, [2, 5]);
  assert.throws(() => tony.executar(() => { throw new Error('Not Found (404)'); }, () => {}), /404/);
});

// --- Repetidos entre as contas (etapa 4) ----------------------------------------------------------

const msg = (id, de, texto, extra = {}) => ({ id, de, nome: '', assunto: 'Aviso', recebido: new Date('2026-11-03T12:00:00Z'),
  texto, trecho: '', convites: [], emailDaConta: '', emMassa: false, ...extra });
const fonteCom = (mensagens, prazos = []) => ({ * mensagens() { yield* mensagens; }, prazos: () => prazos });
const prazo = (id, titulo, data = '2026-11-06', hora = '23:59') => ({ id: `classroom.${id}`, email: '', remetente: 'classroom', nome: 'IA',
  titulo, data, hora, descricao: titulo, origem: 'classroom', confianca: 1, link: '', recebido: '' });

test('o mesmo compromisso pelas três contas entra uma vez só', () => {
  const { tony } = novoTony();
  const convite = 'O evento será dia 05/11/2026 às 08:30.';
  const ingresso = 'Seu ingresso: o evento será dia 05/11/2026 às 08:30.';
  tony.coletar(fonteCom([msg('a1', 'contato@eventos.com', convite)]), { nome: 'pessoal' }, AGORA, true);
  tony.coletar(fonteCom([msg('b1', 'contato@eventos.com', ingresso)]), { nome: 'pessoal2', email: 'b@x.com' }, AGORA, false);
  tony.coletar(fonteCom([msg('c1', 'contato@eventos.com', convite)]), { nome: 'faccat' }, AGORA, false);
  tony.coletar(fonteCom([msg('d1', 'outro@eventos.com', convite)]), { nome: 'pessoal' }, AGORA, true); // outro remetente
  const banco = tony.ler('eventos');
  assert.deepEqual(Object.keys(banco.eventos).sort(), ['a1-1', 'd1-1']);
  assert.deepEqual(json(banco.repetidos), ['pessoal2.b1-1', 'faccat.c1-1']);
});

test('removido numa conta não volta por outra', () => {
  const { tony } = tonyComAgenda();
  tony.guardar('eventos', { eventos: { 'a1-1': { ...ev('a1-1', '2026-11-05', '08:30', 'contato@eventos.com') } }, revisar: {} });
  tony.remover('a1-1');
  tony.coletar(fonteCom([msg('b1', 'contato@eventos.com', 'O evento será dia 05/11/2026 às 08:30.')]),
    { nome: 'pessoal2' }, AGORA, false);
  assert.deepEqual(Object.keys(tony.ler('eventos').eventos), []);
});

test('Classroom: prazos diferentes na mesma hora ficam; o mesmo prazo duas vezes fica um', () => {
  const { tony } = novoTony();
  const prazos = [prazo('1', '[IA] Lista 1'), prazo('2', '[IA] Lista 2'), prazo('3', '[IA] Lista 1')];
  const r = tony.coletar(fonteCom([], prazos), { nome: 'faccat' }, AGORA, false);
  assert.deepEqual(Object.keys(tony.ler('eventos').eventos).sort(), ['faccat.classroom.1', 'faccat.classroom.2']);
  assert.equal(r.repetidos, 1);
});

test('data certa tira a dúvida do mesmo compromisso em revisar', () => {
  const { tony } = novoTony();
  tony.coletar(fonteCom([msg('a1', 'loja@x.com', 'Data: 05/11/2026 às 08:30')]), { nome: 'pessoal' }, AGORA, true);
  assert.ok('a1-1' in tony.ler('eventos').revisar);
  tony.coletar(fonteCom([msg('a2', 'loja@x.com', 'O evento será dia 05/11/2026 às 08:30.')]), { nome: 'pessoal' }, AGORA, true);
  const banco = tony.ler('eventos');
  assert.deepEqual([Object.keys(banco.eventos), Object.keys(banco.revisar)], [['a2-1'], []]);
});

test('Faccat: o que ela manda vira eventos com o prefixo da conta, sem URL pública', () => {
  const { tony } = novoTony();
  const envio = { prazos: [{ id: '9', turma: 'IA', titulo: 'Lista', prazo: '2026-11-09', hora: '19:30' }],
    emails: [{ id: 'f1', de: 'Prof <prof@faccat.br>', assunto: 'Prova', data: String(Date.parse('2026-11-03T12:00:00Z')),
      texto: 'A prova é dia 12/11 às 19h.' }] };
  assert.deepEqual(json(tony.receberFaccat(envio, AGORA)), { prazos: 1, emails_novos: 1 });
  assert.deepEqual(json(tony.receberFaccat(envio, AGORA)), { prazos: 1, emails_novos: 0 }); // o mesmo e-mail de novo
  tony.coletar(tony.fonteFaccat(AGORA), { nome: 'faccat' }, AGORA, false);
  const banco = tony.ler('eventos');
  assert.deepEqual(Object.keys(banco.eventos).sort(), ['faccat.classroom.9', 'faccat.f1-1']);
  assert.equal(banco.eventos['faccat.classroom.9'].titulo, '[IA] Lista');
});

test('Faccat calada há mais de 3 horas (ou que nunca mandou): a coleta avisa', () => {
  const { tony } = novoTony();
  assert.throws(() => tony.fonteFaccat(AGORA), /ainda não mandou nada/);
  tony.receberFaccat({ prazos: [], emails: [] }, AGORA);
  assert.doesNotThrow(() => tony.fonteFaccat(new Date(AGORA.getTime() + 2 * 3600000)));
  assert.throws(() => tony.fonteFaccat(new Date(AGORA.getTime() + 5 * 3600000)), /não manda nada há 5 horas/);
});

test('webhook da Faccat: só com o segredo certo', () => {
  const props = new Propriedades();
  props.setProperties({ FACCAT_SEGREDO: 'fac' });
  const tony = carregar({ PROPRIEDADES_FALSAS: props, TRAVA_FALSA: { tryLock: () => true, releaseLock: () => {} },
    HtmlService: { createHtmlOutput: t => t },
    ContentService: { createTextOutput: t => ({ setMimeType: () => t }), MimeType: { JSON: 'json' } } });
  const post = k => ({ parameter: { faccat: k }, postData: { contents: JSON.stringify({ prazos: [{ id: '1' }], emails: [] }) } });
  assert.equal(tony.doPost(post('errado')), 'ok');
  assert.equal(tony.ler('faccat-caixa'), null);
  assert.deepEqual(JSON.parse(tony.doPost(post('fac'))), { ok: true, prazos: 1, emails_novos: 0 });
});

test('pessoal2: token renovado, guardado, e autorização vencida vira aviso claro', () => {
  const props = new Propriedades();
  props.setProperties({ GOOGLE_CLIENTE_ID: 'id', GOOGLE_CLIENTE_SEGREDO: 's', TOKEN_PESSOAL2: 'r' });
  const cache = { d: {}, get(k) { return this.d[k] || null; }, put(k, v) { this.d[k] = v; } };
  let pedidos = 0, vencido = false;
  const tony = carregar({ PROPRIEDADES_FALSAS: props, CACHE_FALSO: cache, BUSCAR_FALSO: () => {
    pedidos++;
    return vencido ? { getResponseCode: () => 400, getContentText: () => '{"error":"invalid_grant"}' }
      : { getResponseCode: () => 200, getContentText: () => '{"access_token":"acesso-1"}' };
  } });
  assert.equal(tony.tokenDeAcesso({ nome: 'pessoal2' }), 'acesso-1');
  assert.equal(tony.tokenDeAcesso({ nome: 'pessoal2' }), 'acesso-1');
  assert.equal(pedidos, 1);
  cache.d = {};
  vencido = true;
  assert.throws(() => tony.tokenDeAcesso({ nome: 'pessoal2' }), /venceu: no PC, uv run tony autorizar --conta pessoal2/);
});

test('limparHtml tira as tags das descrições guardadas e corrige no Google', () => {
  const { tony, cal } = tonyComAgenda();
  const sujo = { ...ev('h1-1', '2026-11-12'), descricao: "Para adicionar o evento, <a href='https://x.com/a'>clique</a> &amp; pronto.\n\nTrecho <b>forte</b> <a href='" };
  tony.guardar('eventos', { eventos: { 'h1-1': sujo }, revisar: {} });
  tony.sincronizar('2026-11-03');
  const patches = [];
  cal.Events.patch = (body, agenda, id) => { patches.push([id, body.description]); return {}; };
  const limpos = tony.administrar({ acoes: ['limparHtml'] }).acoes.limparHtml;
  assert.deepEqual(json(limpos), ['h1-1']);
  const descricao = tony.ler('eventos').eventos['h1-1'].descricao;
  assert.equal(descricao, 'Para adicionar o evento, clique & pronto.\n\nTrecho forte');
  assert.equal(patches.length, 1);
  assert.doesNotMatch(patches[0][1], /<a|href/);
});

test('transição: sem nada da Faccat ainda, usa a URL antiga; depois do primeiro envio, só o que ela manda', () => {
  const { tony, props } = novoTony();
  props.setProperties({ FACCAT_URL: 'https://faccat.exemplo/exec', FACCAT_CHAVE: 'k' });
  const conta = { nome: 'faccat', tipo: 'apps-script' };
  assert.equal(typeof tony.fonteDe(conta).preparar, 'function'); // a antiga, pela URL
  tony.receberFaccat({ prazos: [], emails: [] }, new Date());
  assert.equal(tony.fonteDe(conta).preparar, undefined);           // a nova, pela caixa
});
