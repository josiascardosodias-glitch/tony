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
