from . import ErroDaFerramenta, ambiente

MAX_NA_RESPOSTA = 15


def disponivel() -> bool:
    """Só aparece para o modelo quando há e-mail configurado."""
    return ambiente.caixa_de_email is not None


def ler_emails(dias: int = 7, termos: str = "") -> str:
    """Lê os e-mails da faculdade recebidos nos últimos dias (só leitura: não apaga nem marca como lido).
    Use para datas de provas, entregas e avisos.

    Args:
        dias: de quantos dias para trás (padrão 7, máximo 60)
        termos: palavras para filtrar pelo assunto ou texto (ex.: "prova"); vazio = todos
    """
    try:
        dias = max(1, min(int(dias), 60))
    except (TypeError, ValueError):
        raise ErroDaFerramenta(f"dias precisa ser um número, veio {dias!r}.")
    try:
        mensagens = ambiente.caixa_de_email(dias)
    except Exception as e:  # rede, senha, servidor: o modelo precisa saber que não leu
        raise ErroDaFerramenta(f"não consegui ler o e-mail ({type(e).__name__}: {e}).")
    palavras = [p for p in termos.casefold().split() if len(p) > 2]
    if palavras:
        mensagens = [m for m in mensagens
                     if any(p in f"{m['assunto']} {m['texto']}".casefold() for p in palavras)]
    if not mensagens:
        return f"nenhum e-mail nos últimos {dias} dias" + (f" com {termos!r}." if termos else ".")
    return "\n\n".join(f"[{m['data']}] de {m['de']}\nAssunto: {m['assunto']}\n{m['texto']}"
                       for m in mensagens[:MAX_NA_RESPOSTA])
