---
criado: 2026-10-24
tags: [tony, email, pendencia]
fonte: "[[2026-10-24]]"
---

# Senha de app do Gmail para o Tony

Travei em: teste do e-mail real do Tony. Falta criar a senha de app do Gmail (precisa da verificação
em duas etapas) e definir o filtro do domínio da faculdade.

Passo a passo (do README do Tony):

1. Ativar a verificação em duas etapas e criar a senha em <https://myaccount.google.com/apppasswords>.
2. Guardar fora do repositório:
   ```bash
   mkdir -p ~/.config/tony && read -rs s && printf '%s' "$s" > ~/.config/tony/senha-email && chmod 600 ~/.config/tony/senha-email
   ```
3. Passar ao Claude o e-mail e o domínio da faculdade (para o `email.filtro`) e testar com a caixa real.

Relacionado: [[Tony - Próximas atualizações]] · [[Tony - Como usar e evoluir]] · [[Tony - Diário de bordo]]
