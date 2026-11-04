// O JavaScript responde igual ao Python: os casos vêm de scripts/casos_appsscript.py.
const test = require('node:test');
const assert = require('node:assert/strict');
const casos = require('./casos.json');
const { carregar } = require('./carregar');

const tony = carregar();
const json = x => JSON.parse(JSON.stringify(x));

test('acharDatas igual ao achar_datas', () => {
  for (const c of casos.datas) {
    const achadas = tony.acharDatas(c.assunto, c.corpo, c.recebido).map(({ titulo, ...d }) => d);
    assert.deepEqual(json(achadas), c.esperado, `${JSON.stringify(c.corpo)} em ${c.recebido.data} ${c.recebido.hora}`);
  }
});

test('limparCorpo igual ao limpar_corpo', () => {
  for (const c of casos.limpeza) assert.equal(tony.limparCorpo(c.texto), c.esperado, JSON.stringify(c.texto));
});

test('periodo, ehDeAgenda e responderAgenda iguais', () => {
  for (const c of casos.consultas) {
    const onde = `${JSON.stringify(c.texto)} em ${c.hoje}`;
    assert.deepEqual(json(tony.periodo(c.texto, c.hoje)), c.periodo, onde);
    assert.equal(tony.ehDeAgenda(c.texto, c.hoje), c.agenda, onde);
    assert.equal(tony.responderAgenda(c.texto, c.eventos, c.hoje), c.resposta, onde);
  }
});

test('linha e paraOModelo iguais', () => {
  for (const c of casos.linhas) assert.equal(tony.linha(c.evento, c.hoje), c.linha);
  for (const c of casos.modelo) assert.equal(tony.paraOModelo(c.eventos, c.hoje), c.texto);
});

test('juntarRepetidos igual ao juntar_repetidos', () => {
  for (const c of casos.repetidos) {
    const banco = json(c.banco);
    assert.equal(tony.juntarRepetidos(banco), c.saiu, JSON.stringify(c.banco));
    assert.deepEqual(json(banco), c.depois, JSON.stringify(c.banco));
  }
});
