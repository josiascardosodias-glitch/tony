/**
 * A agenda "Tony" no Google Agenda (o `tony/agenda.py` em JavaScript), pela API avançada da Agenda com o
 * acesso `calendar.app.created`: o Tony cria e mexe só nas agendas que ele mesmo criou.
 *
 * Sem duplicar, em três camadas:
 * 1. o evento já sincronizado guarda o id do Google em `evento_agenda`;
 * 2. no Google, cada evento leva o id do Tony em `extendedProperties.private.tony_id`, e antes de criar o
 *    Tony procura por ele;
 * 3. o mesmo compromisso (`chave`) é um evento só (`juntarRepetidos`).
 */

const NOME_DA_AGENDA = 'Tony';
const DESCRICAO_DA_AGENDA = 'Datas encontradas pelo Tony nos seus e-mails. Pode apagar a agenda inteira se quiser recomeçar.';
const FUSO = 'America/Sao_Paulo';

/** A API avançada da Agenda; nos testes, uma falsa. */
function _calendario() {
  return typeof CALENDARIO_FALSO !== 'undefined' ? CALENDARIO_FALSO : Calendar;
}

/** A agenda "Tony": a guardada, ou uma nova (e guardada) na primeira vez. */
function idDaAgenda() {
  const guardada = ler('agenda', {}).id;
  if (guardada) return guardada;
  const nova = executar(() => _calendario().Calendars.insert({ summary: NOME_DA_AGENDA, description: DESCRICAO_DA_AGENDA, timeZone: FUSO }));
  guardar('agenda', { id: nova.id, criada_em: new Date().toISOString() });
  return nova.id;
}

/** O evento como a API da Agenda espera. Com hora dura 1 hora; sem hora, é de dia inteiro. */
function corpoDoEvento(e) {
  const descricao = `${e.descricao}\n\nDe: ${e.nome || e.remetente} <${e.remetente}>\nE-mail: ${e.link}`;
  let quando;
  if (e.hora) {
    const [h, m] = e.hora.split(':').map(Number);
    const fimMin = h * 60 + m + 60;
    const fimData = fimMin >= 1440 ? somarDias(e.data, 1) : e.data;
    const fim = `${String(Math.floor(fimMin % 1440 / 60)).padStart(2, '0')}:${String(fimMin % 60).padStart(2, '0')}`;
    quando = { start: { dateTime: `${e.data}T${e.hora}:00`, timeZone: FUSO }, end: { dateTime: `${fimData}T${fim}:00`, timeZone: FUSO } };
  } else {
    quando = { start: { date: e.data }, end: { date: somarDias(e.data, 1) } }; // o fim é exclusivo
  }
  return Object.assign({ summary: e.titulo, description: descricao }, quando,
    { extendedProperties: { private: { tony_id: e.id } } });
}

function _jaExiste(agenda, tonyId) {
  const r = executar(() => _calendario().Events.list(agenda, { privateExtendedProperty: `tony_id=${tonyId}`, maxResults: 1, showDeleted: false }));
  return (r.items || []).length ? r.items[0].id : null;
}

/** Apaga um evento da agenda; o que já foi apagado à mão (404/410) não é erro. */
function _apagar(agenda, eventoAgenda) {
  try {
    executar(() => _calendario().Events.remove(agenda, eventoAgenda));
  } catch (e) {
    if (!/404|410|not found|deleted/i.test(String(e))) throw e;
  }
}

/** Leva os eventos de hoje em diante para a agenda. Devolve {criados, repetidos, ja_estavam}. */
function sincronizar(hoje) {
  hoje = hoje || emBrasilia(new Date()).data;
  const banco = ler('eventos', { eventos: {}, revisar: {} });
  const agenda = idDaAgenda();
  const resumo = { criados: 0, repetidos: juntarRepetidos(banco), ja_estavam: 0 };
  const emUso = new Set(Object.values(banco.eventos).map(e => e.evento_agenda));
  while ((banco.apagar_no_google || []).length) { // repetido que já tinha ido para o Google sozinho
    const eventoAgenda = banco.apagar_no_google[0];
    if (!emUso.has(eventoAgenda)) _apagar(agenda, eventoAgenda);
    banco.apagar_no_google.shift();
    guardar('eventos', banco);
  }
  const noGoogle = {};
  for (const e of Object.values(banco.eventos)) if (e.evento_agenda) noGoogle[chave(e)] = e.evento_agenda;
  for (const e of Object.values(banco.eventos).sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0))) {
    if (e.evento_agenda || e.data < hoje) continue;
    const k = chave(e);
    if (k in noGoogle) {
      e.evento_agenda = noGoogle[k];
      resumo.repetidos++;
    } else {
      const existente = _jaExiste(agenda, e.id);
      if (existente) {
        e.evento_agenda = existente;
        resumo.ja_estavam++;
      } else {
        e.evento_agenda = executar(() => _calendario().Events.insert(corpoDoEvento(e), agenda)).id;
        resumo.criados++;
      }
    }
    noGoogle[k] = e.evento_agenda;
    guardar('eventos', banco); // a cada evento: se cair no meio, não cria de novo o que já criou
  }
  return resumo;
}

function _guardarFora(banco, evento) {
  const fora = banco.chaves_fora = banco.chaves_fora || [];
  const k = JSON.parse(chave(evento));
  if (!fora.some(f => JSON.stringify(f) === JSON.stringify(k))) fora.push(k);
}

/** Tira uma data de "revisar": para os eventos (aceitar) ou para fora (descartar, sem volta na coleta). */
function decidir(id, aceitar) {
  const banco = ler('eventos', { eventos: {}, revisar: {} });
  banco.descartados = banco.descartados || [];
  const evento = banco.revisar[id];
  if (!evento) return `não há ${id} em revisar.`;
  delete banco.revisar[id];
  if (aceitar && Object.values(banco.eventos).some(e => chave(e) === chave(evento))) {
    (banco.repetidos = banco.repetidos || []).push(id);
    guardar('eventos', banco);
    return `aceito: ${evento.titulo} (${evento.data}) já estava na agenda por outro e-mail.`;
  }
  if (aceitar) {
    banco.eventos[id] = evento;
  } else {
    banco.descartados.push(id);
    _guardarFora(banco, evento);
  }
  guardar('eventos', banco);
  return `${aceitar ? 'aceito' : 'descartado'}: ${evento.titulo} (${evento.data}).`;
}

/**
 * Apaga o evento da agenda "Tony" e de `eventos`, e guarda o id em `removidos` e o compromisso em
 * `chaves_fora`: nem este e-mail nem outro sobre o mesmo compromisso trazem ele de volta.
 */
function remover(id) {
  const banco = ler('eventos', { eventos: {}, revisar: {} });
  const evento = banco.eventos[id];
  if (!evento) return `não há ${id} nos eventos.`;
  const juntos = Object.entries(banco.eventos)
    .filter(([i, e]) => i === id || chave(e) === chave(evento) || (evento.evento_agenda && e.evento_agenda === evento.evento_agenda))
    .map(([i]) => i);
  const noGoogle = [...new Set(juntos.map(i => banco.eventos[i].evento_agenda).filter(Boolean))].sort();
  if (noGoogle.length) {
    const agenda = idDaAgenda();
    for (const eventoAgenda of noGoogle) _apagar(agenda, eventoAgenda);
  }
  banco.removidos = banco.removidos || [];
  _guardarFora(banco, evento);
  for (const i of juntos) {
    delete banco.eventos[i];
    banco.removidos.push(i);
  }
  guardar('eventos', banco);
  const extra = juntos.length > 1 ? ` (e mais ${juntos.length - 1} e-mail(s) do mesmo compromisso)` : '';
  return `removido: ${evento.titulo} (${evento.data})${extra}.`;
}
