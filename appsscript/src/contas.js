/**
 * As três contas do Tony no Apps Script (a `tony/contas.py` e a `tony/faccat.py` em JavaScript).
 *
 * - `pessoal`: a conta onde o script roda; Gmail pela API avançada, sem token.
 * - `pessoal2`: outra conta Google. O script não enxerga o Gmail dela; usa a mesma autorização que o
 *   Python já tem (o token OAuth do projeto `tony-513620`) e chama a API REST do Gmail, que devolve o
 *   mesmo formato da API avançada. Propriedades: `GOOGLE_CLIENTE_ID`, `GOOGLE_CLIENTE_SEGREDO`,
 *   `TOKEN_PESSOAL2` (o refresh token).
 * - `faccat`: o App da Web da Faccat (só os prazos do Classroom e os e-mails que ele entrega).
 *   Propriedades: `FACCAT_URL`, `FACCAT_CHAVE`.
 *
 * Os ids da pessoal2 levam o prefixo `pessoal2.` e os da Faccat `faccat.`, como no Python.
 */

const CONTAS_DO_TONY = [
  { nome: 'pessoal', email: 'josiascardosodias@gmail.com', tipo: 'gmail' },
  { nome: 'pessoal2', email: 'josiasdiascardoso@gmail.com', tipo: 'oauth' },
  { nome: 'faccat', email: '', tipo: 'apps-script' },
];

class AutorizacaoVencida extends Error {}

/** Um access token para a conta, pelo refresh token; guardado por 50 minutos. */
function tokenDeAcesso(conta) {
  const cache = typeof CACHE_FALSO !== 'undefined' ? CACHE_FALSO : CacheService.getScriptCache();
  const chaveCache = `acesso-${conta.nome}`;
  const guardado = cache.get(chaveCache);
  if (guardado) return guardado;
  const r = _buscar('https://oauth2.googleapis.com/token', {
    method: 'post', muteHttpExceptions: true,
    payload: { client_id: segredo('GOOGLE_CLIENTE_ID'), client_secret: segredo('GOOGLE_CLIENTE_SEGREDO'),
      refresh_token: segredo(`TOKEN_${conta.nome.toUpperCase()}`), grant_type: 'refresh_token' },
  });
  const corpo = JSON.parse(r.getContentText());
  if (r.getResponseCode() !== 200) {
    if (corpo.error === 'invalid_grant') {
      throw new AutorizacaoVencida(`a autorização da ${conta.nome} venceu: no PC, uv run tony autorizar --conta ${conta.nome} ` +
        'e depois appsscript/configurar.py --tokens');
    }
    throw new Error(`o Google recusou o token da ${conta.nome}: ${corpo.error || r.getResponseCode()}`);
  }
  cache.put(chaveCache, corpo.access_token, 50 * 60);
  return corpo.access_token;
}

/** O Gmail de outra conta pela API REST, com o mesmo jeito do `gmailDaConta()`. */
function gmailPorToken(conta) {
  const base = 'https://gmail.googleapis.com/gmail/v1/users/me/messages';
  const pedir = (caminho, parametros) => {
    const consulta = Object.entries(parametros || {}).filter(([, v]) => v !== undefined)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
    const r = _buscar(`${base}${caminho}${consulta ? '?' + consulta : ''}`, {
      headers: { Authorization: `Bearer ${tokenDeAcesso(conta)}` }, muteHttpExceptions: true });
    if (r.getResponseCode() !== 200) throw new Error(`Gmail da ${conta.nome} respondeu ${r.getResponseCode()}`);
    return JSON.parse(r.getContentText());
  };
  return {
    buscar(q) {
      const ids = [];
      let pagina;
      do {
        const r = executar(() => pedir('', { q, pageToken: pagina, maxResults: 100 }));
        for (const m of r.messages || []) ids.push(m.id);
        pagina = r.nextPageToken;
      } while (pagina);
      return ids;
    },
    mensagem(id) {
      return executar(() => pedir(`/${id}`, { format: 'full' }));
    },
    anexo(idDaMensagem, idDoAnexo) {
      return pedir(`/${idDaMensagem}/attachments/${idDoAnexo}`);
    },
  };
}

/** O App da Web da Faccat: uma chamada por coleta traz os prazos e os e-mails novos. */
function fonteFaccat() {
  let resposta = null;
  const buscar = (depoisDe, filtro) => {
    if (resposta) return resposta;
    const url = `${segredo('FACCAT_URL')}?chave=${encodeURIComponent(segredo('FACCAT_CHAVE'))}` +
      `&desde=${Math.floor(depoisDe.getTime() / 1000)}&filtro=${encodeURIComponent(filtro)}`;
    let dados;
    try {
      dados = JSON.parse(_buscar(url, { muteHttpExceptions: true, followRedirects: true }).getContentText());
    } catch (e) {
      throw new Error('o App da Web da Faccat não respondeu direito'); // a URL e a chave nunca aparecem no erro
    }
    if (dados.erro) throw new Error(`o App da Web da Faccat recusou: ${dados.erro}`);
    resposta = dados;
    return resposta;
  };
  return {
    preparar(depoisDe, filtro) { buscar(depoisDe, filtro); },
    prazos() {
      return ((resposta || {}).prazos || []).map(p => ({
        id: `classroom.${p.id}`, email: '', remetente: 'classroom', nome: p.turma, titulo: `[${p.turma}] ${p.titulo}`,
        data: p.prazo, hora: p.hora || null, descricao: (p.descricao || p.titulo).trim(), origem: 'classroom',
        confianca: 1, link: p.link || '', recebido: p.atualizado_em || '' }));
    },
    * mensagens(depoisDe, filtro) {
      for (const e of buscar(depoisDe, filtro).emails || []) {
        const { nome, endereco } = _remetente(e.de || '');
        const texto = (e.texto || '').trim();
        yield { id: e.id, de: endereco.toLowerCase(), nome, assunto: (e.assunto || '').trim(), recebido: new Date(Number(e.data)),
          texto, trecho: texto.split(/\s+/).join(' ').slice(0, 160), convites: e.convites || [], emailDaConta: '',
          emMassa: Boolean(e.em_massa) };
      }
    },
  };
}

/** A fonte de cada conta. */
function fonteDe(conta) {
  if (typeof FONTE_FALSA !== 'undefined') return FONTE_FALSA;
  if (conta.tipo === 'gmail') return fonteGmail(gmailDaConta());
  if (conta.tipo === 'oauth') return fonteGmail(gmailPorToken(conta));
  if (conta.tipo === 'apps-script') return fonteFaccat();
  throw new Error(`tipo de conta desconhecido: ${conta.tipo}`);
}
