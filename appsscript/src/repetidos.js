/**
 * O mesmo compromisso uma vez só (a `coleta.chave` e o `juntar_repetidos` do Python, em JavaScript).
 *
 * O mesmo compromisso: mesmo remetente, mesmo dia e mesma hora (o convite e o ingresso do mesmo evento
 * são dois e-mails, mas um compromisso só). Os prazos do Classroom têm todos o mesmo remetente e muitas
 * vezes a mesma hora (23:59): ali o título também conta.
 */

/** A chave como texto (JSON de uma lista), para servir de chave de objeto e de Set. */
function chave(evento) {
  const k = evento.remetente === 'classroom'
    ? [evento.remetente, evento.data, evento.hora, evento.titulo]
    : [evento.remetente || '', evento.data, evento.hora];
  return JSON.stringify(k);
}

/** Entre repetidos fica o que já está no Google; depois, o que chegou primeiro. */
function _comparaPreferido(a, b) {
  const ka = [a.evento_agenda ? 0 : 1, a.recebido || '', a.id];
  const kb = [b.evento_agenda ? 0 : 1, b.recebido || '', b.id];
  for (let i = 0; i < 3; i++) {
    if (ka[i] < kb[i]) return -1;
    if (ka[i] > kb[i]) return 1;
  }
  return 0;
}

function tirarRepetido(banco, secao, id, fica) {
  const saiu = banco[secao][id];
  delete banco[secao][id];
  (banco.repetidos = banco.repetidos || []).push(id);
  if (saiu.evento_agenda && saiu.evento_agenda !== (fica || {}).evento_agenda) {
    (banco.apagar_no_google = banco.apagar_no_google || []).push(saiu.evento_agenda); // a sincronização apaga
  }
}

/**
 * Deixa um evento por compromisso em `eventos` e em `revisar`; o que está em `revisar` e já está nos
 * eventos sai. Os que saem vão para `repetidos`. Devolve quantos saíram.
 */
function juntarRepetidos(banco) {
  let saiu = 0;
  const grupos = {};
  for (const e of Object.values(banco.eventos)) (grupos[chave(e)] = grupos[chave(e)] || []).push(e);
  const nosEventos = {};
  for (const [k, grupo] of Object.entries(grupos)) {
    const [fica, ...resto] = grupo.slice().sort(_comparaPreferido);
    nosEventos[k] = fica;
    for (const e of resto) {
      tirarRepetido(banco, 'eventos', e.id, fica);
      saiu++;
    }
  }
  const vistosEmRevisar = new Set();
  const revisar = Object.entries(banco.revisar || {}).sort((a, b) => _comparaPreferido(a[1], b[1]));
  for (const [id, e] of revisar) {
    const k = chave(e);
    if (k in nosEventos || vistosEmRevisar.has(k)) {
      tirarRepetido(banco, 'revisar', id, nosEventos[k] || {});
      saiu++;
    }
    vistosEmRevisar.add(k);
  }
  return saiu;
}

/** Compromissos que você descartou ou removeu: outro e-mail sobre eles também não entra. */
function chavesFora(banco) {
  return new Set((banco.chaves_fora || []).map(k => JSON.stringify(k)));
}
