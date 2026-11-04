/**
 * Onde o Tony guarda os dados no Apps Script: as propriedades do script (só este script lê), no lugar
 * dos arquivos `dados/*.json` do PC. Não usa o Drive: o acesso ao Drive pelo Apps Script seria ao Drive
 * inteiro.
 *
 * Cada propriedade guarda no máximo 9 KB, então um JSON maior é dividido em pedaços
 * (`eventos#0`, `eventos#1`…, e `eventos#n` com quantos são). O total do script é 500 KB.
 *
 * Nomes: `eventos` (o eventos.json), `coleta-<conta>` (o estado de cada conta), `telegram`, `bloqueados`,
 * `agenda`. Segredos ficam em propriedades soltas, sem pedaços: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`,
 * `OLLAMA_CHAVE`, `WEBHOOK_SEGREDO`.
 */

const PEDACO = 8000; // caracteres por propriedade (o limite é 9 KB por valor, e um caractere pode ter mais de um byte)

/** As propriedades do script; nos testes, um objeto que imita o PropertiesService. */
function _propriedades() {
  return typeof PROPRIEDADES_FALSAS !== 'undefined' ? PROPRIEDADES_FALSAS : PropertiesService.getScriptProperties();
}

function ler(nome, padrao) {
  const props = _propriedades();
  const n = props.getProperty(`${nome}#n`);
  if (n === null) return padrao === undefined ? null : JSON.parse(JSON.stringify(padrao));
  let texto = '';
  for (let i = 0; i < Number(n); i++) texto += props.getProperty(`${nome}#${i}`) || '';
  return JSON.parse(texto);
}

function guardar(nome, dados) {
  const props = _propriedades();
  const texto = JSON.stringify(dados);
  const pedacos = {};
  for (let i = 0; i * PEDACO < texto.length || i === 0; i++) pedacos[`${nome}#${i}`] = texto.slice(i * PEDACO, (i + 1) * PEDACO);
  const antes = Number(props.getProperty(`${nome}#n`) || 0);
  const agora = Object.keys(pedacos).length;
  pedacos[`${nome}#n`] = String(agora);
  props.setProperties(pedacos); // tudo de uma vez: quem lê não vê metade nova e metade velha
  for (let i = agora; i < antes; i++) props.deleteProperty(`${nome}#${i}`);
}

function segredo(nome) {
  const valor = _propriedades().getProperty(nome);
  if (!valor) throw new Error(`falta a propriedade ${nome} do script (Configurações do projeto > Propriedades do script)`);
  return valor;
}

/** Quanto do limite de 500 KB está em uso (para o /status). */
function espacoUsado() {
  const tudo = _propriedades().getProperties();
  return Object.entries(tudo).reduce((soma, [k, v]) => soma + k.length + v.length, 0);
}
