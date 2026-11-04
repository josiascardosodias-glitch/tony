/**
 * Responde perguntas de agenda sem IA (o `tony/consulta.py` em JavaScript): entende o período ("hoje",
 * "sexta", "semana que vem", "12/11") e monta a resposta com os eventos guardados. O modelo só entra
 * quando a mensagem não é uma pergunta de agenda (`ehDeAgenda` devolve false).
 *
 * Datas são "AAAA-MM-DD"; `hoje` também.
 */

const MESES_NOMES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro',
  'outubro', 'novembro', 'dezembro'];
const SOBRE_AGENDA = regex('\\b(agenda|compromisso|marcad[oa]s?|tenho|tem algo|tem alguma|o que tem|prova|' +
  'entrega|evento|reuni[ãa]o|prazo|pr[óo]xim[oa]s dias|livre)\\b', 'i');
const PADRAO_DIAS = 7; // "o que eu tenho?" sem período: a próxima semana

function _primeiroDoMesSeguinte(data) {
  const { ano, mes } = partes(data);
  return mes === 12 ? fazerData(ano + 1, 1, 1) : fazerData(ano, mes + 1, 1);
}

function _nomeDoDia(dia, hoje) {
  if (dia === hoje) return 'hoje';
  if (dia === somarDias(hoje, 1)) return 'amanhã';
  return `${DIAS[diaDaSemana(dia)].split('-')[0]}, ${ddmm(dia)}`;
}

/** Na pergunta, "e sexta?" é a sexta: aqui não há "segunda chamada" para confundir. */
function _diasSoltos(texto, hoje) {
  const nomes = { segunda: 0, 'terça': 1, terca: 1, quarta: 2, quinta: 3, sexta: 4 };
  return Object.entries(nomes)
    .filter(([nome]) => regex(`\\b${nome}\\b`).test(texto))
    .map(([, n]) => somarDias(hoje, ((n - diaDaSemana(hoje)) % 7 + 7) % 7));
}

/** [início, fim, nome do período] que a mensagem pede, ou null se ela não fala de um período. */
function periodo(texto, hoje) {
  const t = texto.toLowerCase();
  const domingo = somarDias(hoje, 6 - diaDaSemana(hoje));
  if (/fim de semana|final de semana/u.test(t)) {
    const sabado = somarDias(hoje, ((5 - diaDaSemana(hoje)) % 7 + 7) % 7);
    return [sabado, somarDias(sabado, 1), 'no fim de semana'];
  }
  if (/semana que vem|pr[óo]xima semana/u.test(t)) {
    const segunda = somarDias(domingo, 1);
    return [segunda, somarDias(segunda, 6), 'na semana que vem'];
  }
  if (regex('\\b(ess?a|nesta|nessa|esta) semana\\b|\\bsemana\\b').test(t)) return [hoje, domingo, 'até domingo'];
  if (/m[êe]s que vem|pr[óo]ximo m[êe]s/u.test(t)) {
    const inicio = _primeiroDoMesSeguinte(hoje);
    const fim = somarDias(_primeiroDoMesSeguinte(inicio), -1);
    return [inicio, fim, `em ${MESES_NOMES[partes(inicio).mes - 1]}`];
  }
  if (regex('\\b(ess?e|neste|nesse|este) m[êe]s\\b|\\bm[êe]s\\b').test(t)) {
    return [hoje, somarDias(_primeiroDoMesSeguinte(hoje), -1), 'até o fim do mês'];
  }
  const dia = regex('\\bdia (\\d{1,2})\\b').exec(t);
  if (dia && !regex('\\bdia \\d{1,2}\\s*(/|de )').test(t)) {
    const n = Number(dia[1]);
    const { ano, mes } = partes(hoje);
    let alvo = fazerData(ano, mes, n);
    if (alvo && alvo < hoje) {
      const seguinte = partes(_primeiroDoMesSeguinte(hoje));
      alvo = fazerData(seguinte.ano, seguinte.mes, n);
    }
    if (alvo) return [alvo, alvo, _nomeDoDia(alvo, hoje)];
  }
  // "hoje", "amanhã", "sexta", "12/11", "20 de novembro": o mesmo leitor das datas dos e-mails
  const ajustado = t.replace(regex('\\b(e|na|no|pra|para) (?=segunda|terça|terca|quarta|quinta|sexta)', 'g'), 'na ');
  const datas = [...new Set(_datasDaFrase(ajustado, hoje).concat(_diasSoltos(t, hoje)))].sort();
  if (datas.length) {
    const [primeira, ultima] = [datas[0], datas[datas.length - 1]];
    return [primeira, ultima, primeira === ultima ? _nomeDoDia(primeira, hoje) : 'nesses dias'];
  }
  if (/hoje/u.test(t)) return [hoje, hoje, 'hoje']; // "o que tenho hoje" (sem hora)
  return null;
}

function ehDeAgenda(texto, hoje) {
  return Boolean(periodo(texto, hoje) || SOBRE_AGENDA.test(texto));
}

function linha(evento, hoje) {
  const dia = evento.data;
  const quando = diasEntre(hoje, dia) < 2 ? _nomeDoDia(dia, hoje) : `${fatiar(DIAS[diaDaSemana(dia)], 3)} ${ddmm(dia)}`;
  const hora = evento.hora ? `, ${evento.hora}` : '';
  const resumo = fatiar(evento.descricao.split('\n')[0], 140);
  return `• ${quando}${hora} — ${evento.titulo}\n  ${resumo}`;
}

/** A resposta para uma pergunta de agenda, só com os eventos do período. */
function responderAgenda(texto, eventos, hoje) {
  const achado = periodo(texto, hoje);
  const [inicio, fim, nome] = achado || [hoje, somarDias(hoje, PADRAO_DIAS), 'nos próximos 7 dias'];
  const noPeriodo = eventos.filter(e => inicio <= e.data && e.data <= fim).sort(porDataEHora);
  if (!noPeriodo.length) return `Nada marcado ${nome}.`;
  const cabeca = `${noPeriodo.length === 1 ? 'Marcado' : `${noPeriodo.length} coisas marcadas`} ${nome}:`;
  return cabeca + '\n\n' + noPeriodo.map(e => linha(e, hoje)).join('\n');
}

/** A agenda dos próximos dias, curta, para o prompt (título, data, hora e a frase: nunca o e-mail). */
function paraOModelo(eventos, hoje, dias) {
  const fim = somarDias(hoje, dias === undefined ? 30 : dias);
  const linhas = eventos.slice().sort(porDataEHora)
    .filter(e => hoje <= e.data && e.data <= fim)
    .map(e => `- ${DIAS[diaDaSemana(e.data)]}, ${ddmm(e.data)}/${e.data.slice(0, 4)}` +
      `${e.hora ? ' às ' + e.hora : ''}: ${e.titulo} (${fatiar(e.descricao.split(/\r\n|\r|\n/)[0] || '', 120)})`);
  return linhas.join('\n') || '(nada marcado)';
}

// --- Resumo do dia (o `tony dia`) -----------------------------------------------------------------

const DIAS_A_FRENTE = 7;

function resumoDoDia(banco, hoje) {
  const fim = somarDias(hoje, DIAS_A_FRENTE);
  const proximos = Object.values(banco.eventos).filter(e => hoje <= e.data && e.data <= fim).sort(porDataEHora);
  const deHoje = proximos.filter(e => e.data === hoje);
  const depois = proximos.filter(e => e.data !== hoje);
  const partesDoTexto = [];
  if (deHoje.length) partesDoTexto.push('Hoje:\n' + deHoje.map(e => linha(e, hoje)).join('\n'));
  if (depois.length) partesDoTexto.push(`Nos próximos ${DIAS_A_FRENTE} dias:\n` + depois.map(e => linha(e, hoje)).join('\n'));
  if (!partesDoTexto.length) partesDoTexto.push(`Nada marcado para hoje nem para os próximos ${DIAS_A_FRENTE} dias.`);
  const revisar = Object.values(banco.revisar || {}).filter(e => e.data >= hoje).length;
  if (revisar) partesDoTexto.push(`${revisar} data(s) esperando você decidir: /revisar no Telegram.`);
  return partesDoTexto.join('\n\n');
}
