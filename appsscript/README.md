# Tony no Google Apps Script (v5, em construção)

O Tony rodando nos servidores do Google: coleta do Gmail, agenda "Tony", repetidos e o bot do Telegram,
sem o notebook. O plano está em `docs/Projeto/Tony - Próximas atualizações.md` (seção v5).

- `src/`: o que vai para o Apps Script (`clasp push`). Todos os arquivos dividem o escopo global;
  `_util.js` vem primeiro porque os outros usam o `regex()` dele já no carregamento.
- `testes/`: `node --test`. O `diferencial.test.js` confere o JavaScript contra as respostas do Python
  (`scripts/casos_appsscript.py` gera o `casos.json`, fora do git); o `unidade.test.js`, o que só existe aqui.

```bash
appsscript/testar.sh
```

| Arquivo | O que porta do Python |
|---|---|
| `src/_util.js` | datas "AAAA-MM-DD", `\b` com acento (`regex()`), dias da semana |
| `src/datas.js` | `tony/datas.py` (o `.ics` é lido sem biblioteca, com hora UTC convertida para Brasília) |
| `src/consulta.js` | `tony/consulta.py` e o resumo do `tony/dia.py` |
| `src/repetidos.js` | `coleta.chave`, `juntar_repetidos`, `chaves_fora` |
