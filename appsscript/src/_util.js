/**
 * Utilitários do Tony no Apps Script: datas como texto "AAAA-MM-DD" (sem fuso, como o `date` do Python)
 * e expressões regulares com limite de palavra que entende acento.
 *
 * No Apps Script todos os arquivos dividem o mesmo escopo global; nos testes (`node --test`), o
 * `testes/carregar.js` carrega os arquivos num contexto só, do mesmo jeito.
 */

/** O `\b` do Python entende "amanhã" como uma palavra; o do JavaScript não. Este entende. */
const LIMITE_DE_PALAVRA = '(?:(?<=[\\p{L}\\p{N}_])(?![\\p{L}\\p{N}_])|(?<![\\p{L}\\p{N}_])(?=[\\p{L}\\p{N}_]))';

/** Uma RegExp escrita como no Python: `\b` vira o limite com acento; sempre com a flag `u`. */
function regex(fonte, flags) {
  return new RegExp(fonte.split('\\b').join(LIMITE_DE_PALAVRA), (flags || '') + 'u');
}

const DIAS = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'];

function _dois(n) {
  return String(n).padStart(2, '0');
}

/** "AAAA-MM-DD", ou null se o dia não existe (31/02, 29/02 fora de ano bissexto). */
function fazerData(ano, mes, dia) {
  if (mes < 1 || mes > 12 || dia < 1) return null;
  const d = new Date(Date.UTC(ano, mes - 1, dia));
  if (d.getUTCFullYear() !== ano || d.getUTCMonth() !== mes - 1 || d.getUTCDate() !== dia) return null;
  return `${String(ano).padStart(4, '0')}-${_dois(mes)}-${_dois(dia)}`;
}

function _utc(data) {
  const [a, m, d] = data.split('-').map(Number);
  return Date.UTC(a, m - 1, d);
}

function somarDias(data, dias) {
  const d = new Date(_utc(data) + dias * 86400000);
  return `${d.getUTCFullYear()}-${_dois(d.getUTCMonth() + 1)}-${_dois(d.getUTCDate())}`;
}

/** Dias de `de` até `ate` (pode ser negativo). */
function diasEntre(de, ate) {
  return Math.round((_utc(ate) - _utc(de)) / 86400000);
}

/** Segunda = 0 ... domingo = 6, como o `weekday()` do Python. */
function diaDaSemana(data) {
  return (new Date(_utc(data)).getUTCDay() + 6) % 7;
}

function partes(data) {
  const [ano, mes, dia] = data.split('-').map(Number);
  return { ano, mes, dia };
}

/** "dd/mm" */
function ddmm(data) {
  return `${data.slice(8, 10)}/${data.slice(5, 7)}`;
}

/** Os primeiros `n` caracteres de verdade (o `texto[:n]` do Python; emoji conta um). */
function fatiar(texto, n) {
  return Array.from(texto).slice(0, n).join('');
}

/** Ordena por data e hora (sem hora vem antes), como o `key=lambda e: (e["data"], e["hora"] or "")`. */
function porDataEHora(a, b) {
  const ka = `${a.data} ${a.hora || ''}`;
  const kb = `${b.data} ${b.hora || ''}`;
  return ka < kb ? -1 : ka > kb ? 1 : 0;
}
