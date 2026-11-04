# Política de privacidade do Tony

O Tony é um assistente pessoal, de uso próprio do autor deste repositório. Ele não é oferecido a outras
pessoas: o único usuário é o dono das contas Google que o autorizam.

## O que o Tony acessa

- **Gmail, só leitura** (`gmail.readonly`): os e-mails novos, para achar datas de compromissos. Nenhum
  e-mail é alterado, enviado ou apagado.
- **Google Agenda, só as agendas que ele mesmo cria** (`calendar.app.created`): a agenda "Tony", onde
  os compromissos achados viram eventos. As outras agendas não são vistas.

## O que é guardado e onde

- Só o que precisa para a agenda: título, data, hora, a frase do e-mail onde a data apareceu, o
  remetente e o link do e-mail. O corpo do e-mail não é guardado.
- Os dados ficam na própria conta Google do usuário (propriedades do script no Google Apps Script) ou
  no computador dele. Nada é vendido, compartilhado ou usado para outra finalidade.
- Nas perguntas livres pelo Telegram, um modelo de linguagem recebe a pergunta e a lista de
  compromissos dos próximos dias (título, data e a frase), nunca o e-mail inteiro.

## Como revogar

Em https://myaccount.google.com/permissions, remova o acesso do "Tony". Apagar a agenda "Tony" apaga os
eventos criados por ele.

## Contato

josiascardosodias@gmail.com
