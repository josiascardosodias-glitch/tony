/**
 * As funções que se rodam pelo editor do Apps Script (ou pelos gatilhos).
 *
 * - `conferir()`: não grava nada. Lê os e-mails dos últimos 3 dias, roda o extrator de datas e testa a
 *   agenda criando e apagando uma agenda de teste. Serve para ver que o Tony funciona aqui e para dar
 *   as permissões na primeira vez.
 *
 * O webhook do Telegram (`doPost`) está no `telegram.js`.
 */

function conferir() {
  const gmail = gmailDaConta();
  const desde = new Date(Date.now() - 3 * 86400000);
  const ids = gmail.buscar(`after:${Math.floor(desde.getTime() / 1000)} ${COLETA.filtro}`);
  const hoje = emBrasilia(new Date()).data;
  let aceitos = 0, duvidosos = 0;
  const exemplos = [];
  for (const id of ids.slice(0, 40)) {
    const msg = lerMensagem(gmail, gmail.mensagem(id));
    const [a, d] = processar(msg, 'pessoal', hoje, '', new Date());
    aceitos += a.length;
    duvidosos += d.length;
    for (const e of a.slice(0, 1)) if (exemplos.length < 5) exemplos.push(`${e.data}${e.hora ? ' ' + e.hora : ''} — ${e.titulo}`);
  }
  const teste = Calendar.Calendars.insert({ summary: 'Tony (teste, pode apagar)', timeZone: FUSO });
  Calendar.Events.insert(corpoDoEvento({ id: 'teste-1', titulo: 'Teste do Tony', data: hoje, hora: null,
    descricao: 'teste', nome: '', remetente: 'tony', link: '' }), teste.id);
  Calendar.Calendars.remove(teste.id);
  const texto = [`Gmail: ${ids.length} e-mail(s) nos últimos 3 dias (li ${Math.min(ids.length, 40)}).`,
    `Datas: ${aceitos} para a agenda, ${duvidosos} para revisar.`, ...exemplos.map(e => `  ${e}`),
    'Agenda: criei e apaguei uma agenda de teste.', `Armazém: ${espacoUsado()} de 500000 bytes em uso.`].join('\n');
  console.log(texto);
  return texto;
}

// --- Gatilhos -------------------------------------------------------------------------------------

/** O gatilho de hora em hora: coleta as três contas, leva para a agenda e avisa no Telegram. */
function coletaDeHoraEmHora() {
  _comTrava(() => rodarColeta(new Date(), false));
}

/** O gatilho das 08:00: o resumo do dia, montado pelo código (zero token). */
function resumoDasOito() {
  const hoje = emBrasilia(new Date()).data;
  enviar(resumoDoDia(ler('eventos', { eventos: {}, revisar: {} }), hoje));
}

/** Troca os gatilhos do projeto pelos dois do Tony. Roda de novo sem duplicar. */
function instalarGatilhos() {
  for (const g of ScriptApp.getProjectTriggers()) ScriptApp.deleteTrigger(g);
  ScriptApp.newTrigger('coletaDeHoraEmHora').timeBased().everyHours(1).create();
  ScriptApp.newTrigger('resumoDasOito').timeBased().atHour(8).nearMinute(0).everyDays(1).inTimezone(FUSO).create();
  return ScriptApp.getProjectTriggers().map(g => g.getHandlerFunction());
}

// --- Administração pelo PC (appsscript/configurar.py) ---------------------------------------------

const SEGREDOS_ACEITOS = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'OLLAMA_CHAVE', 'WEBHOOK_SEGREDO', 'GOOGLE_CLIENTE_ID',
  'GOOGLE_CLIENTE_SEGREDO', 'TOKEN_PESSOAL2', 'FACCAT_URL', 'FACCAT_CHAVE'];
const DADOS_ACEITOS = ['eventos', 'coleta-pessoal', 'coleta-pessoal2', 'coleta-faccat', 'bloqueados', 'telegram', 'agenda'];

/**
 * Um pedido do PC: {segredos: {...}, dados: {...}, acoes: [...]}. Só com o `ADMIN_SEGREDO` na URL. Nunca
 * devolve segredos nem dados: só o que foi feito e os números para conferir.
 */
function administrar(pedido) {
  const feito = { segredos: [], dados: [], acoes: {} };
  const props = _propriedades();
  for (const [nome, valor] of Object.entries(pedido.segredos || {})) {
    if (!SEGREDOS_ACEITOS.includes(nome)) throw new Error(`segredo não aceito: ${nome}`);
    props.setProperty(nome, String(valor));
    feito.segredos.push(nome);
  }
  for (const [nome, valor] of Object.entries(pedido.dados || {})) {
    if (!DADOS_ACEITOS.includes(nome)) throw new Error(`dado não aceito: ${nome}`);
    guardar(nome, valor);
    feito.dados.push(nome);
  }
  const acoes = {
    conferir: () => {
      const banco = ler('eventos', { eventos: {}, revisar: {} });
      return { eventos: Object.keys(banco.eventos).length, revisar: Object.keys(banco.revisar).length,
        repetidos: (banco.repetidos || []).length, espaco: espacoUsado(),
        na_agenda: Object.values(banco.eventos).filter(e => e.evento_agenda).length,
        agenda: Boolean(ler('agenda', {}).id),
        segredos: SEGREDOS_ACEITOS.filter(n => props.getProperty(n)),
        gatilhos: typeof ScriptApp !== 'undefined' ? ScriptApp.getProjectTriggers().map(g => g.getHandlerFunction()) : [] };
    },
    juntarRepetidos: () => {
      const banco = ler('eventos', { eventos: {}, revisar: {} });
      const saiu = juntarRepetidos(banco);
      guardar('eventos', banco);
      return saiu;
    },
    contas: () => Object.fromEntries(CONTAS_DO_TONY.map(conta => {
      try { // só confere que cada fonte responde: não grava nada
        const fonte = fonteDe(conta);
        const desde = new Date(Date.now() - 86400000);
        if (fonte.preparar) fonte.preparar(desde, COLETA.filtro);
        let n = 0;
        for (const _ of fonte.mensagens(desde, COLETA.filtro, new Set())) if (++n >= 3) break;
        return [conta.nome, `ok (${n} e-mail(s) lidos${fonte.prazos ? `, ${fonte.prazos().length} prazo(s)` : ''})`];
      } catch (e) {
        return [conta.nome, `erro: ${e.message || e}`];
      }
    })),
    sincronizar: () => sincronizar(),
    limparHtml: () => { // descrições guardadas antes da v5.1 com tags cruas: limpa aqui e no Google
      const banco = ler('eventos', { eventos: {}, revisar: {} });
      const limpos = [];
      for (const secao of ['eventos', 'revisar']) {
        for (const e of Object.values(banco[secao])) {
          if (!TEM_HTML.test(e.descricao) && !/<\s*[a-z][^>]*$/i.test(e.descricao)) continue;
          e.descricao = e.descricao.split('\n').map(l => _trecho(l)).join('\n');
          if (secao === 'eventos' && e.evento_agenda) {
            executar(() => _calendario().Events.patch({ description: corpoDoEvento(e).description }, idDaAgenda(), e.evento_agenda));
          }
          limpos.push(e.id);
        }
      }
      guardar('eventos', banco);
      return limpos;
    },
    coletar: () => { rodarColeta(new Date(), false); return 'ok'; },
    instalarGatilhos: () => instalarGatilhos(),
    removerGatilhos: () => { for (const g of ScriptApp.getProjectTriggers()) ScriptApp.deleteTrigger(g); return []; },
  };
  for (const acao of pedido.acoes || []) {
    if (!(acao in acoes)) throw new Error(`ação desconhecida: ${acao}`);
    feito.acoes[acao] = acoes[acao]();
  }
  return feito;
}
