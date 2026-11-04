/**
 * A conversa livre com o modelo (o `tony/conversa.py` e o `tony/cliente.py` em JavaScript): o único
 * caminho do Tony que gasta token. Pergunta de agenda nunca chega aqui (`ehDeAgenda`).
 *
 * No Apps Script cada mensagem é uma execução nova: o histórico fica na propriedade `conversa` e é
 * esquecido depois de 30 minutos sem mensagem. O prompt de sistema é montado no começo da conversa,
 * como no Python: personalidade, a hora de agora, a Inteligência e a agenda dos próximos 30 dias
 * (nunca o e-mail). A personalidade e a Inteligência vêm do `_conhecimento.js`, gerado na hora do envio
 * (`appsscript/enviar.sh`) e fora do git, porque a Inteligência é pessoal.
 */

const MODELO = 'gemma4:31b';            // o `gemma4:31b-cloud` do Python, chamado direto na nuvem
const OLLAMA_URL = 'https://ollama.com/api/chat';
const TEMPERATURA = 0.7;
const LIMITE_DE_CONTEXTO = 8192;        // tokens; passando de 80%, o começo da conversa vira resumo
const ESQUECER_APOS_MIN = 30;
const CARACTERES_POR_TOKEN = 4;
const TROCAS_MANTIDAS = 2;
const PEDIDO_RESUMO_PARCIAL = 'Resuma o trecho de conversa abaixo em poucas linhas, em português, para você mesmo ' +
  'continuar a conversa depois: assuntos, decisões, o que ficou pendente e o tom. Se houver um resumo ' +
  'anterior no início, incorpore-o.';

class ErroDoModelo extends Error {}

/** Chama o modelo na nuvem do Ollama e devolve o texto da resposta. */
function chamarModelo(mensagens) {
  const resposta = _buscar(OLLAMA_URL, {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: `Bearer ${segredo('OLLAMA_CHAVE')}` },
    payload: JSON.stringify({ model: MODELO, messages: mensagens, stream: false, options: { temperature: TEMPERATURA } }),
  });
  const codigo = resposta.getResponseCode();
  let corpo;
  try {
    corpo = JSON.parse(resposta.getContentText());
  } catch (e) {
    throw new ErroDoModelo(`resposta inválida do Ollama (HTTP ${codigo})`);
  }
  if (codigo !== 200) throw new ErroDoModelo(`Ollama respondeu ${codigo}: ${corpo.error || 'erro sem descrição'}`);
  return ((corpo.message || {}).content || '').trim();
}

/** O UrlFetchApp, ou o falso dos testes. */
function _buscar(url, opcoes) {
  return typeof BUSCAR_FALSO !== 'undefined' ? BUSCAR_FALSO(url, opcoes) : UrlFetchApp.fetch(url, opcoes);
}

function _parteFixa(agora, agenda) {
  const { data, hora } = emBrasilia(agora);
  const partesDoPrompt = [typeof PERSONALIDADE !== 'undefined' ? PERSONALIDADE : '',
    `# Agora\n\n${DIAS[diaDaSemana(data)]}, ${ddmm(data)}/${data.slice(0, 4)}, ${hora}.`];
  if (typeof INTELIGENCIA !== 'undefined' && INTELIGENCIA) {
    partesDoPrompt.push(`# O que você sabe sobre quem está conversando com você\n\n${INTELIGENCIA}`);
  }
  if (agenda) {
    partesDoPrompt.push(`# A agenda dela nos próximos 30 dias\n\n${agenda}\n\n(É o que o código achou nos ` +
      'e-mails dela. Você não lê os e-mails: o que não está aqui, você não sabe.)');
  }
  return partesDoPrompt.join('\n\n');
}

function _promptDeSistema(c) {
  return c.resumo ? `${c.fixo}\n\n# O começo desta conversa (resumido)\n\n${c.resumo}` : c.fixo;
}

function _tokens(c) {
  return Math.floor((_promptDeSistema(c) + c.mensagens.map(m => m.content).join('')).length / CARACTERES_POR_TOKEN);
}

/** Troca as mensagens antigas por um resumo, em vez de deixá-las cair em silêncio. */
function _resumirComeco(c) {
  const falas = c.mensagens.map((m, i) => (m.role === 'user' ? i : -1)).filter(i => i >= 0);
  if (falas.length <= TROCAS_MANTIDAS) return;
  const corte = falas[falas.length - TROCAS_MANTIDAS];
  const nomes = { user: 'Pessoa', assistant: 'Tony' };
  const transcricao = c.mensagens.slice(0, corte).filter(m => m.content).map(m => `${nomes[m.role]}: ${m.content}`).join('\n');
  const trecho = c.resumo ? `Resumo anterior:\n${c.resumo}\n\n` : '';
  c.resumo = chamarModelo([{ role: 'system', content: PEDIDO_RESUMO_PARCIAL }, { role: 'user', content: trecho + transcricao }]);
  c.mensagens = c.mensagens.slice(corte);
}

/** Uma fala na conversa livre. `eventos` é a lista de eventos (para a agenda do prompt). */
function conversar(texto, eventos, agora) {
  let c = ler('conversa', null);
  if (!c || !c.ultima || agora.getTime() - new Date(c.ultima).getTime() > ESQUECER_APOS_MIN * 60000) {
    c = { fixo: _parteFixa(agora, paraOModelo(eventos, emBrasilia(agora).data)), resumo: '', mensagens: [] };
  }
  c.ultima = agora.toISOString();
  const mensagens = c.mensagens.concat([{ role: 'user', content: texto }]);
  let resposta;
  try {
    resposta = chamarModelo([{ role: 'system', content: _promptDeSistema(c) }].concat(mensagens));
  } catch (e) {
    if (!(e instanceof ErroDoModelo) && !/timed out|tempo|Address unavailable|DNS/i.test(String(e))) throw e;
    return `Não consegui falar com o modelo agora (${e.message}). Perguntas de agenda continuam funcionando.`;
  }
  c.mensagens = mensagens.concat([{ role: 'assistant', content: resposta }]);
  if (_tokens(c) > 0.8 * LIMITE_DE_CONTEXTO) {
    try {
      _resumirComeco(c);
    } catch (e) { /* a resposta já saiu; tenta resumir de novo na próxima fala */ }
  }
  guardar('conversa', c);
  return resposta;
}

/** O /nova: a próxima fala começa uma conversa nova. */
function esquecerConversa() {
  guardar('conversa', null);
}
