/**
 * Acha datas em e-mails, sem IA: a mesma lógica do `tony/datas.py`, em JavaScript.
 *
 * Cada data achada vem com a frase onde apareceu e uma `confianca` de 0 a 1:
 * - convite `.ics`: 1.0 (a data vem pronta);
 * - no texto: 0.3 de base, +0.4 se a frase tem palavra de compromisso (prova, entrega, prazo, até…),
 *   +0.2 se tem hora, +0.2 se a data está no assunto.
 * Data no passado, mais de um ano à frente, em citação de resposta ("Em ... escreveu:") ou em rodapé
 * não conta, nem o dia do próprio e-mail sem uma hora depois da chegada.
 *
 * `recebido` é {data: "AAAA-MM-DD", hora: "HH:MM"}, já no horário de Brasília.
 */

const MESES = {
  janeiro: 1, jan: 1, fevereiro: 2, fev: 2, 'março': 3, marco: 3, mar: 3, abril: 4, abr: 4, maio: 5, mai: 5,
  junho: 6, jun: 6, julho: 7, jul: 7, agosto: 8, ago: 8, setembro: 9, set: 9, outubro: 10, out: 10,
  novembro: 11, nov: 11, dezembro: 12, dez: 12,
};
const SEMANA = { segunda: 0, 'terça': 1, terca: 1, quarta: 2, quinta: 3, sexta: 4, 'sábado': 5, sabado: 5, domingo: 6 };

const COMPROMISSO = regex(
  '\\b(prova|avalia[çc][ãa]o|exame|entrega|entregar|prazo|vencimento|vence|vencer|reuni[ãa]o|encontro|' +
  'consulta|apresenta[çc][ãa]o|semin[áa]rio|aula|palestra|evento|inscri[çc][ãa]o|inscri[çc][õo]es|' +
  'matr[íi]cula|pagamento|boleto|fatura|até|data limite|agendad[oa]|marcad[oa]|remarcad[oa]|adiad[oa]|' +
  'in[íi]cio|come[çc]a|termina|encerra|deadline|defesa|entrevista|agendamento|hor[áa]rio|compromisso|' +
  'lembrete|confirmad[oa]|confirma[çc][ãa]o)\\b', 'i');
const RODAPE = regex('escreveu:|wrote:|enviado (em|do)|cancelar (a )?inscri|descadastr|unsubscribe|' +
  'pol[íi]tica de privacidade|todos os direitos|©', 'i');
const CITACAO = regex('^(Em .{5,120}escreveu:|On .{5,120}wrote:|-{2,} ?Mensagem original|-{2,} ?Original Message|' +
  'De: .+\\n(Enviado|Enviada|Data|Sent):)', 'mi');

const _MES = Object.keys(MESES).sort((a, b) => b.length - a.length).join('|');
const _DIA_DA_SEMANA = Object.keys(SEMANA).join('|');
const NUMERICA = regex('(?<![\\d/.:])(\\d{1,2})/(\\d{1,2})(?:/(\\d{4}|\\d{2}))?(?![\\d/])', 'g');
const EXTENSO = regex(`\\b(\\d{1,2})º?\\s+de\\s+(${_MES})\\.?(?:\\s+de\\s+(\\d{4}))?\\b`, 'gi');
const RELATIVA = regex('\\b(depois de amanhã|amanhã|hoje)\\b', 'gi');
const SEMANAL = regex('(?:\\b(na|no|nesta|neste|esta|este|até|até a|para|pra)\\s+)?(?:\\b(pr[óo]xim[oa])\\s+)?' +
  `\\b(${_DIA_DA_SEMANA})(-feira)?(?:\\s+(que vem))?\\b`, 'gi');
const _HORA = '(?<![\\d/])([01]?\\d|2[0-3])(?:h([0-5]\\d)?|:([0-5]\\d))(?:\\s*h(?:oras|rs)?)?(?![\\d/])' +
  '|(?<![\\d/])([01]?\\d|2[0-3])\\s*horas\\b';
const HORA = regex(_HORA, 'i');
const HORA_TODAS = regex(_HORA, 'gi');

const FRASE = /(?<=[.!?])\s+|\n+/u;
// "2 de dez. às 14h" é uma frase só: o ponto da abreviação sai antes de cortar as frases
const ABREVIACAO = regex('\\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|seg|ter|qua|qui|sex|s[áa]b|dom)\\.', 'gi');
const LIMITE_FUTURO = 400;    // dias
const ANO_SEGUINTE_ATE = 183; // sem ano, só vira o ano que vem se cair em até 6 meses

/** Tira o que não é deste e-mail: a mensagem citada numa resposta, linhas com > e a assinatura. */
function limparCorpo(texto) {
  const citacao = CITACAO.exec(texto);
  if (citacao) texto = texto.slice(0, citacao.index);
  texto = texto.split('\n-- \n')[0];
  const linhas = texto.split(/\r\n|\r|\n/);
  if (linhas.length > 1 && linhas[linhas.length - 1] === '') linhas.pop(); // como o splitlines() do Python
  return linhas.filter(l => !l.trimStart().startsWith('>')).join('\n');
}

/** A data com o ano escrito ou, sem ano, a próxima vez que esse dia/mês acontece a partir da base. */
function _ano(dia, mes, ano, base) {
  if (ano) return fazerData(Number(ano) + (ano.length === 2 ? 2000 : 0), mes, dia);
  const anoBase = partes(base).ano;
  const candidata = fazerData(anoBase, mes, dia);
  if (!candidata) return null;
  if (candidata >= somarDias(base, -1)) return candidata;
  const seguinte = fazerData(anoBase + 1, mes, dia);
  // "29/09" escrito em novembro é uma data que passou, não setembro do ano que vem
  return seguinte && diasEntre(base, seguinte) <= ANO_SEGUINTE_ATE ? seguinte : null;
}

/** "sexta" é a próxima sexta (hoje, se hoje é sexta); "próxima sexta"/"sexta que vem" pula hoje. */
function _semana(diaDaSemanaAlvo, proxima, base) {
  const falta = ((diaDaSemanaAlvo - diaDaSemana(base)) % 7 + 7) % 7;
  return somarDias(base, falta || (proxima ? 7 : 0));
}

function _hora(frase) {
  const m = HORA.exec(frase);
  if (!m) return null;
  const hora = m[1] || m[4];
  const minutos = m[2] || m[3] || '00';
  return `${String(Number(hora)).padStart(2, '0')}:${minutos}`;
}

function _datasDaFrase(frase, base) {
  const datas = [];
  const semHora = frase.replace(HORA_TODAS, ' '); // "19:30" não é dia 19 do mês 30
  for (const m of semHora.matchAll(NUMERICA)) {
    const dia = Number(m[1]), mes = Number(m[2]);
    if (!m[3] && m[1].length === 1 && m[2].length === 1) continue; // "3/4" sem ano é fração
    if (dia >= 1 && dia <= 31 && mes >= 1 && mes <= 12) datas.push(_ano(dia, mes, m[3], base));
  }
  for (const m of frase.matchAll(EXTENSO)) {
    datas.push(_ano(Number(m[1]), MESES[m[2].toLowerCase()], m[3], base));
  }
  for (const m of frase.matchAll(RELATIVA)) {
    const palavra = m[1].toLowerCase();
    if (palavra === 'hoje' && !HORA.test(frase)) continue; // "hoje segue o material" não é compromisso
    datas.push(somarDias(base, { hoje: 0, 'amanhã': 1 }[palavra] ?? 2));
  }
  for (const m of frase.matchAll(SEMANAL)) {
    const [, antes, proxima, nome, feira, queVem] = m;
    const n = SEMANA[nome.toLowerCase()];
    // "segunda chamada" e "quarta parte" não são dias: sem uma marca, só sábado e domingo contam
    if (feira || proxima || queVem || antes || n >= 5) datas.push(_semana(n, Boolean(proxima || queVem), base));
  }
  return datas.filter(Boolean);
}

/** Todas as datas de compromisso do assunto e do corpo, uma por data (fica a de maior confiança). */
function acharDatas(assunto, corpo, recebido) {
  const base = recebido.data;
  const achadas = {};
  const frases = [[assunto, 'assunto']].concat(
    limparCorpo(corpo).replace(ABREVIACAO, '$1').split(FRASE).map(f => [f, 'corpo']));
  for (let [frase, origem] of frases) {
    frase = (frase || '').replace(/\s+/gu, ' ').trim();
    if (!frase || RODAPE.test(frase)) continue;
    for (const dia of _datasDaFrase(frase, base)) {
      if (dia < base || diasEntre(base, dia) > LIMITE_FUTURO) continue;
      const hora = _hora(frase);
      if (dia === base && (!hora || hora <= recebido.hora)) continue; // o próprio aviso, não um compromisso
      const confianca = 0.3 + 0.4 * COMPROMISSO.test(frase) + 0.2 * Boolean(hora) + 0.2 * (origem === 'assunto');
      const nova = { data: dia, hora, frase: fatiar(frase, 300), origem, confianca: Math.round(Math.min(confianca, 1) * 100) / 100, titulo: '' };
      const atual = achadas[dia];
      if (!atual || nova.confianca > atual.confianca) {
        if (atual && !nova.hora) nova.hora = atual.hora;
        achadas[dia] = nova;
      }
    }
  }
  return Object.values(achadas).sort(porDataEHora);
}

// --- Convites .ics --------------------------------------------------------------------------------

function _desescapar(valor) {
  return valor.replace(/\\n/gi, '\n').replace(/\\([,;\\])/g, '$1');
}

/** Os eventos de um convite .ics. Hora em UTC ("...Z") vira horário de Brasília (UTC-3, sem horário de verão desde 2019). */
function datasDoIcs(texto) {
  const linhas = texto.replace(/\r\n[ \t]|\n[ \t]/g, '').split(/\r?\n/); // desdobra as linhas longas
  const datas = [];
  let evento = null;
  for (const linha of linhas) {
    if (linha === 'BEGIN:VEVENT') { evento = {}; continue; }
    if (linha === 'END:VEVENT') {
      if (evento && evento.DTSTART) {
        const m = /^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})\d{2}(Z?))?$/.exec(evento.DTSTART.trim());
        if (m) {
          let data = `${m[1]}-${m[2]}-${m[3]}`, hora = null;
          if (m[4]) {
            let minutos = Number(m[4]) * 60 + Number(m[5]);
            if (m[6] === 'Z') minutos -= 180;
            if (minutos < 0) { minutos += 1440; data = somarDias(data, -1); }
            hora = `${_dois(Math.floor(minutos / 60))}:${_dois(minutos % 60)}`;
          }
          const titulo = _desescapar(evento.SUMMARY || '').trim();
          const descricao = _desescapar(evento.DESCRIPTION || '').trim();
          datas.push({ data, hora, frase: fatiar(descricao || titulo, 300), origem: 'ics', confianca: 1, titulo });
        }
      }
      evento = null;
      continue;
    }
    if (!evento) continue;
    const m = /^([A-Z-]+)(;[^:]*)?:(.*)$/.exec(linha);
    if (m && !(m[1] in evento)) evento[m[1]] = m[3];
  }
  return datas;
}
