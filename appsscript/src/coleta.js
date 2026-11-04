/**
 * A coleta no Apps Script (o `tony/coleta.py` em JavaScript): busca os e-mails novos pela API avançada
 * do Gmail (só leitura), acha as datas e guarda em `eventos`. Sem IA.
 *
 * A API avançada devolve as mensagens no mesmo formato que o Python lê (`format: "full"`), e os ids são
 * os mesmos: o estado do PC é importado sem conversão.
 *
 * O caminho de um e-mail:
 * 1. A busca já pede só o que chegou depois da última coleta, sem os bloqueados (`-from:`) e com o
 *    filtro (sem Promoções e Social). E-mail bloqueado nem é baixado.
 * 2. O remetente é conferido de novo contra os bloqueados (a busca do Gmail é por palavra).
 * 3. As datas saem do assunto, do corpo e dos convites `.ics` (`datas.js`).
 * 4. Confiança alta vira evento; média vai para `revisar`; baixa é descartada.
 * 5. O mesmo compromisso (`chave`) entra uma vez só, venha de quantos e-mails vier.
 */

const COLETA = {
  filtro: '-category:promotions -category:social',
  primeiraVezDias: 30,
  aceitarAPartirDe: 0.6,
  revisarAPartirDe: 0.3,
};
const VISTOS_GUARDADOS = 2000;  // ids de e-mails já processados que o estado guarda, por conta
const PENALIDADE_EM_MASSA = 0.4;  // newsletter e marketing perdem confiança
const MAXIMO_POR_RODADA = 150;  // e-mails por rodada (o Apps Script corta a execução em 6 minutos)
const ESPERAS = [2, 5, 15, 30];  // segundos entre tentativas quando o Google pede calma

/** Tenta de novo quando o Google recusa por limite ou falha do lado dele. */
function executar(pedido, esperar) {
  for (let i = 0; ; i++) {
    try {
      return pedido();
    } catch (e) {
      const passageiro = /rate limit|ratelimit|429|quota|backend error|internal error|50\d|service unavailable/i.test(String(e));
      if (i >= ESPERAS.length || !passageiro) throw e;
      (esperar || (s => Utilities.sleep(s * 1000)))(ESPERAS[i]);
    }
  }
}

// --- Bloqueados -----------------------------------------------------------------------------------

function lerBloqueados() {
  const dados = ler('bloqueados', { enderecos: [], dominios: [] });
  return { enderecos: dados.enderecos.map(e => e.toLowerCase()),
    dominios: dados.dominios.map(d => d.toLowerCase().replace(/^@/, '')) };
}

function bloqueado(endereco, bloqueados) {
  endereco = endereco.toLowerCase();
  const dominio = endereco.split('@').pop();
  return bloqueados.enderecos.includes(endereco) ||
    bloqueados.dominios.some(d => dominio === d || dominio.endsWith('.' + d));
}

/** A busca do Gmail: depois da data, com o filtro e sem os bloqueados. */
function consultaGmail(filtro, bloqueados, depoisDe) {
  return [`after:${Math.floor(depoisDe.getTime() / 1000)}`, filtro]
    .concat(bloqueados.enderecos.map(e => `-from:${e}`), bloqueados.dominios.map(d => `-from:${d}`))
    .filter(Boolean).join(' ');
}

// --- Mensagens ------------------------------------------------------------------------------------

/** O texto de um `body.data`: a API avançada às vezes devolve base64 web-safe, às vezes os bytes. */
function _decodificar(dados) {
  if (typeof DECODIFICAR_FALSO !== 'undefined') return DECODIFICAR_FALSO(dados);
  const bytes = Array.isArray(dados) ? dados : Utilities.base64DecodeWebSafe(dados);
  return Utilities.newBlob(bytes).getDataAsString('UTF-8');
}

const _ENTIDADES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };

function _desescaparHtml(texto) {
  return texto.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (inteiro, nome) => {
    if (nome[0] === '#') {
      const n = nome[1].toLowerCase() === 'x' ? parseInt(nome.slice(2), 16) : parseInt(nome.slice(1), 10);
      return Number.isFinite(n) && n > 0 && n < 0x110000 ? String.fromCodePoint(n) : inteiro;
    }
    return _ENTIDADES[nome.toLowerCase()] ?? inteiro;
  });
}

function _semHtml(texto) {
  texto = texto.replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ');
  texto = texto.replace(/<br\s*\/?>|<\/p>|<\/div>|<\/li>|<\/tr>/gi, '\n');
  return _desescaparHtml(texto.replace(/<[^>]+>/g, ' '));
}

function* _partes(parte) {
  yield parte;
  for (const filha of parte.parts || []) yield* _partes(filha);
}

/** Uma mensagem da API (formato `full`) em texto: o text/plain, ou o HTML sem as tags. */
function lerMensagem(gmail, bruta) {
  const cabecalhos = {};
  for (const c of bruta.payload.headers || []) cabecalhos[c.name.toLowerCase()] = c.value;
  const { nome, endereco } = _remetente(cabecalhos.from || '');
  const texto = { 'text/plain': '', 'text/html': '' };
  const convites = [];
  for (const parte of _partes(bruta.payload)) {
    const tipo = parte.mimeType || '', corpo = parte.body || {};
    let dados = corpo.data;
    if (!dados && corpo.attachmentId && tipo === 'text/calendar') {
      dados = executar(() => gmail.anexo(bruta.id, corpo.attachmentId)).data;
    }
    if (!dados) continue;
    if (tipo === 'text/calendar' || (parte.filename || '').toLowerCase().endsWith('.ics')) convites.push(_decodificar(dados));
    else if (tipo in texto && !texto[tipo]) texto[tipo] = _decodificar(dados);
  }
  const corpo = texto['text/plain'] || _semHtml(texto['text/html']);
  const recebido = new Date(Number(bruta.internalDate));
  return {
    id: bruta.id, de: endereco.toLowerCase(), nome, assunto: (cabecalhos.subject || '').trim(), recebido,
    texto: corpo.replace(/[ \t\r\f\v]+/g, ' ').trim(), trecho: _desescaparHtml(bruta.snippet || ''), convites,
    emailDaConta: '',
    emMassa: 'list-unsubscribe' in cabecalhos || ['bulk', 'list'].includes((cabecalhos.precedence || '').toLowerCase()),
  };
}

/** "Nome <a@b.com>" → {nome, endereco}, como o parseaddr do Python nos casos comuns. */
function _remetente(from) {
  const m = /^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/.exec(from);
  if (m) return { nome: m[1].trim(), endereco: m[2].trim() };
  return { nome: '', endereco: from.trim() };
}

function linkDaMensagem(msg) {
  return msg.emailDaConta
    ? `https://mail.google.com/mail/u/?authuser=${msg.emailDaConta}#all/${msg.id}`
    : `https://mail.google.com/mail/u/0/#all/${msg.id}`;
}

// --- Eventos --------------------------------------------------------------------------------------

/** O assunto sem Re:/Fwd:/[etiqueta]: é o que aparece na agenda. */
function titulo(assunto) {
  const limpo = assunto.replace(/^\s*((re|res|fw|fwd|enc|tr)\s*:\s*|\[[^\]]*\]\s*)+/i, '').trim();
  return limpo || '(sem assunto)';
}

/** Data e hora de Brasília de um instante: {data: "AAAA-MM-DD", hora: "HH:MM"}. */
function emBrasilia(instante) {
  const local = new Date(instante.getTime() - 3 * 3600000); // UTC-3, sem horário de verão desde 2019
  return { data: local.toISOString().slice(0, 10), hora: local.toISOString().slice(11, 16) };
}

function _isoBrasilia(instante) {
  const { data } = emBrasilia(instante);
  const local = new Date(instante.getTime() - 3 * 3600000).toISOString().slice(11, 19);
  return `${data}T${local}-03:00`;
}

function evento(msg, data, n, conta, prefixo, agora) {
  let descricao = data.frase;
  if (msg.trecho && !data.frase.includes(msg.trecho)) descricao += `\n\n${msg.trecho}`;
  return {
    id: `${prefixo}${msg.id}-${n}`, email: msg.id, conta, remetente: msg.de, nome: msg.nome,
    titulo: data.titulo || titulo(msg.assunto), data: data.data, hora: data.hora, descricao,
    origem: data.origem, confianca: data.confianca, link: linkDaMensagem(msg),
    recebido: _isoBrasilia(msg.recebido), criado_em: _isoBrasilia(agora).slice(0, 19), evento_agenda: null,
  };
}

/** [eventos, para revisar] de uma mensagem. Data antes de `hoje` não interessa à agenda. */
function processar(msg, conta, hoje, prefixo, agora) {
  const datas = acharDatas(msg.assunto, msg.texto, emBrasilia(msg.recebido));
  if (msg.emMassa) for (const d of datas) d.confianca = Math.round(Math.max(d.confianca - PENALIDADE_EM_MASSA, 0) * 100) / 100;
  for (const convite of msg.convites) {
    try {
      datas.push(...datasDoIcs(convite));
    } catch (e) { /* convite quebrado: ficam as datas do texto */ }
  }
  const aceitos = [], duvidosos = [];
  datas.forEach((data, i) => {
    if (data.data < hoje) return;
    if (data.confianca >= COLETA.aceitarAPartirDe) aceitos.push(evento(msg, data, i + 1, conta, prefixo, agora));
    else if (data.confianca >= COLETA.revisarAPartirDe) duvidosos.push(evento(msg, data, i + 1, conta, prefixo, agora));
  });
  return [aceitos, duvidosos];
}

// --- A rodada -------------------------------------------------------------------------------------

/** A API avançada do Gmail da conta onde o script roda. */
function gmailDaConta() {
  return {
    buscar(q) {
      const ids = [];
      let pagina;
      do {
        const r = executar(() => Gmail.Users.Messages.list('me', { q, pageToken: pagina, maxResults: 100 }));
        for (const m of r.messages || []) ids.push(m.id);
        pagina = r.nextPageToken;
      } while (pagina);
      return ids;
    },
    mensagem(id) {
      return executar(() => Gmail.Users.Messages.get('me', id, { format: 'full' }));
    },
    anexo(idDaMensagem, idDoAnexo) {
      return Gmail.Users.Messages.Attachments.get('me', idDaMensagem, idDoAnexo);
    },
  };
}

/**
 * Uma rodada da coleta numa conta. `fonte` dá as mensagens já lidas ({mensagens(depoisDe, filtro, vistos)})
 * e, na Faccat, os prazos ({prazos()}). Devolve {emails, eventos, revisar, bloqueados, repetidos}.
 */
function coletar(fonte, conta, agora, primeira) {
  agora = agora || new Date();
  const prefixo = primeira ? '' : `${conta.nome}.`; // ids do Gmail são por conta: o prefixo evita colisão
  const hoje = emBrasilia(agora).data;
  const banco = ler('eventos', { eventos: {}, revisar: {} });
  const estado = ler(`coleta-${conta.nome}`, { ultima: null, vistos: [] });
  const bloqueados = lerBloqueados();

  // Uma hora de folga para trás: o `after:` do Gmail arredonda, e e-mail repetido é barrado pelos `vistos`.
  const depoisDe = estado.ultima ? new Date(new Date(estado.ultima).getTime() - 3600000)
    : new Date(agora.getTime() - COLETA.primeiraVezDias * 86400000);
  const filtro = consultaGmail(COLETA.filtro, bloqueados, depoisDe).split(' ').slice(1).join(' ');
  const vistos = new Set(estado.vistos);
  const fora = new Set([...(banco.descartados || []), ...(banco.removidos || []), ...(banco.repetidos || [])]);
  const resumo = { emails: 0, eventos: 0, revisar: 0, bloqueados: 0, repetidos: juntarRepetidos(banco) };
  const ocupadas = new Set([...Object.values(banco.eventos).map(chave), ...chavesFora(banco)]);
  const emRevisar = {};
  for (const [id, e] of Object.entries(banco.revisar)) emRevisar[chave(e)] = id;

  function entrar(e, secao) {
    const k = chave(e);
    if (fora.has(e.id) || e.id in banco[secao] || ocupadas.has(k) || (secao === 'revisar' && k in emRevisar)) {
      if (!(e.id in banco[secao]) && !fora.has(e.id)) {
        (banco.repetidos = banco.repetidos || []).push(e.id);
        fora.add(e.id);
        resumo.repetidos++;
      }
      return false;
    }
    if (secao === 'eventos') {
      if (k in emRevisar) {
        tirarRepetido(banco, 'revisar', emRevisar[k], e); // data certa tira a dúvida do mesmo compromisso
        delete emRevisar[k];
        resumo.repetidos++;
      }
      ocupadas.add(k);
    } else {
      emRevisar[k] = e.id;
    }
    banco[secao][e.id] = e;
    return true;
  }

  if (fonte.preparar) fonte.preparar(depoisDe, filtro);
  for (const prazo of fonte.prazos ? fonte.prazos() : []) { // prazos do Classroom: a data vem pronta
    const e = Object.assign({}, prazo, { id: `${prefixo}${prazo.id}`, conta: conta.nome,
      criado_em: _isoBrasilia(agora).slice(0, 19), evento_agenda: null });
    if (e.data >= hoje && entrar(e, 'eventos')) resumo.eventos++;
  }
  let lidos = 0, completa = true;
  for (const msg of fonte.mensagens(depoisDe, filtro, vistos)) {
    if (vistos.has(msg.id)) continue;
    if (lidos++ >= MAXIMO_POR_RODADA) { completa = false; break; } // o resto fica para a próxima rodada
    if (!primeira) msg.emailDaConta = conta.email || '';
    estado.vistos.push(msg.id);
    vistos.add(msg.id);
    if (bloqueado(msg.de, bloqueados)) { resumo.bloqueados++; continue; }
    resumo.emails++;
    const [aceitos, duvidosos] = processar(msg, conta.nome, hoje, prefixo, agora);
    resumo.eventos += aceitos.filter(e => entrar(e, 'eventos')).length;
    resumo.revisar += duvidosos.filter(e => entrar(e, 'revisar')).length;
  }
  if (completa) estado.ultima = agora.toISOString(); // só avança quando a rodada leu tudo
  estado.vistos = estado.vistos.slice(-VISTOS_GUARDADOS);
  guardar('eventos', banco);
  guardar(`coleta-${conta.nome}`, estado);
  return resumo;
}

/** A fonte da conta onde o script roda: a busca vai ao Gmail, e só os ids não vistos são baixados. */
function fonteGmail(gmail) {
  return {
    * mensagens(depoisDe, filtro, vistos) {
      for (const id of gmail.buscar(`after:${Math.floor(depoisDe.getTime() / 1000)} ${filtro}`.trim())) {
        if (!vistos.has(id)) yield lerMensagem(gmail, gmail.mensagem(id));
      }
    },
  };
}
