// O que não tem par direto no Python: o leitor de .ics (o Python usa a biblioteca icalendar), o resumo
// do dia (que lá lê o arquivo) e a chave dos prazos do Classroom.
const test = require('node:test');
const assert = require('node:assert/strict');
const { carregar } = require('./carregar');

const tony = carregar();
const json = x => JSON.parse(JSON.stringify(x));

test('ics: hora local, hora UTC vira Brasília, dia inteiro, linha dobrada e escapes', () => {
  const ics = [
    'BEGIN:VCALENDAR', 'BEGIN:VEVENT', 'DTSTART;TZID=America/Sao_Paulo:20261118T140000',
    'SUMMARY:Entrevista de estágio', 'END:VEVENT',
    'BEGIN:VEVENT', 'DTSTART:20261120T013000Z', 'SUMMARY:Show\\, à noite', 'DESCRIPTION:Linha um\\nLinha',
    '  dois', 'END:VEVENT',
    'BEGIN:VEVENT', 'DTSTART;VALUE=DATE:20261125', 'SUMMARY:Feriado da empresa', 'END:VEVENT',
    'BEGIN:VEVENT', 'SUMMARY:Sem data', 'END:VEVENT', 'END:VCALENDAR', ''].join('\r\n');
  assert.deepEqual(json(tony.datasDoIcs(ics)), [
    { data: '2026-11-18', hora: '14:00', frase: 'Entrevista de estágio', origem: 'ics', confianca: 1, titulo: 'Entrevista de estágio' },
    { data: '2026-11-19', hora: '22:30', frase: 'Linha um\nLinha dois', origem: 'ics', confianca: 1, titulo: 'Show, à noite' },
    { data: '2026-11-25', hora: null, frase: 'Feriado da empresa', origem: 'ics', confianca: 1, titulo: 'Feriado da empresa' },
  ]);
});

test('resumo do dia: hoje, próximos 7 dias e o que espera decisão', () => {
  const ev = (id, data, hora, titulo) => ({ id, data, hora, titulo, descricao: `${titulo}, frase.` });
  const banco = {
    eventos: { a: ev('a', '2026-11-03', '19:00', 'Prova'), b: ev('b', '2026-11-05', null, 'Entrega'),
      c: ev('c', '2026-11-20', null, 'Longe'), d: ev('d', '2026-11-01', null, 'Passou') },
    revisar: { r: ev('r', '2026-11-10', null, 'Talvez'), s: ev('s', '2026-10-01', null, 'Velho') },
  };
  assert.equal(tony.resumoDoDia(banco, '2026-11-03'),
    'Hoje:\n• hoje, 19:00 — Prova\n  Prova, frase.\n\nNos próximos 7 dias:\n• qui 05/11 — Entrega\n  Entrega, frase.' +
    '\n\n1 data(s) esperando você decidir: /revisar no Telegram.');
  assert.equal(tony.resumoDoDia({ eventos: {}, revisar: {} }, '2026-11-03'),
    'Nada marcado para hoje nem para os próximos 7 dias.');
});

test('chave: Classroom compara o título; o resto, remetente, dia e hora', () => {
  const base = { remetente: 'classroom', data: '2026-11-06', hora: '23:59' };
  assert.notEqual(tony.chave({ ...base, titulo: 'Lista 1' }), tony.chave({ ...base, titulo: 'Lista 2' }));
  const email = { remetente: 'a@x.com', data: '2026-11-05', hora: '08:30' };
  assert.equal(tony.chave({ ...email, titulo: 'Seu ingresso' }), tony.chave({ ...email, titulo: 'Pedido confirmado' }));
  assert.ok(tony.chavesFora({ chaves_fora: [['a@x.com', '2026-11-05', '08:30']] }).has(tony.chave(email)));
});
