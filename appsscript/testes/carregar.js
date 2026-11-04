// Carrega os arquivos de src/ num contexto só, como o Apps Script faz (todos dividem o escopo global).
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function carregar(extras = {}) {
  const contexto = vm.createContext({ console, ...extras });
  const pasta = path.join(__dirname, '..', 'src');
  for (const arquivo of fs.readdirSync(pasta).filter(a => a.endsWith('.js')).sort()) {
    vm.runInContext(fs.readFileSync(path.join(pasta, arquivo), 'utf8'), contexto, { filename: arquivo });
  }
  // const/let/function do topo ficam no escopo global do contexto: um Proxy dá acesso pelo nome
  return new Proxy({}, { get: (_, nome) => vm.runInContext(String(nome), contexto) });
}

module.exports = { carregar };
