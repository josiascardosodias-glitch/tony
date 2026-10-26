"""O Tony fala primeiro: `tony dia` escreve o resumo do dia; `tony agendar` instala um timer do systemd
(do seu usuário, sem sudo) que roda `tony dia --notificar` todo dia, como notificação na área de trabalho.
"""

import subprocess
from datetime import datetime
from pathlib import Path

from . import config
from .cliente import Cliente
from .conversa import Conversa, calendario
from .memoria import carregar_personalidade, inteligencia_para_prompt, ler_memoria, ultimo_resumo
from .registro import Registro

DIAS_DE_EMAIL = 3
PEDIDO_DIA = (
    "[Mensagem agendada: a pessoa não falou nada; você é quem começa.] Escreva a notificação que abre "
    "o dia dela: em até 3 frases, o que importa hoje e nos próximos 7 dias (provas, entregas, "
    "pendências), tirado só do que está {fontes}. "
    "Use o calendário abaixo para as datas; não calcule de cabeça. Se não houver "
    "nada marcado, diga isso em uma frase curta. Sem saudação longa e sem pergunta no fim."
)


def caixa_de_email(cfg: dict):
    """A caixa do config, ou None se o e-mail não está configurado (aí a ferramenta nem aparece)."""
    email = cfg["email"]
    if not email["usuario"]:
        return None
    from .ferramentas._email import caixa_imap
    arquivo = config.caminho(email["senha_arquivo"])
    if not arquivo or not arquivo.is_file():
        raise SystemExit(f"e-mail configurado, mas falta o arquivo da senha de app: {email['senha_arquivo']}")
    return caixa_imap(email["servidor"], email["usuario"], arquivo.read_text(encoding="utf-8").strip(), email["filtro"])


def pedido_do_dia(emails: list[dict] | None, hoje: datetime) -> str:
    datas = f"Calendário:\n{calendario(hoje, 8)}"
    if emails is None:  # sem dizer isso, ele escrevia "não achei nada nas notas e e-mails" (5/8)
        pedido = PEDIDO_DIA.format(fontes="nas suas notas, lembretes, memória e última conversa")
        return f"{pedido} Você não tem acesso a e-mail (não está configurado): não diga que olhou e-mails.\n\n{datas}"
    if not emails:
        trecho = f"(nenhum e-mail nos últimos {DIAS_DE_EMAIL} dias)"
    else:
        trecho = "\n\n".join(f"[{m['data']}] de {m['de']}\nAssunto: {m['assunto']}\n{m['texto']}" for m in emails)
    pedido = PEDIDO_DIA.format(fontes="nas suas notas, lembretes, memória, última conversa e nos e-mails abaixo")
    return f"{pedido}\n\n{datas}\n\nE-mails recentes:\n{trecho}"


def resumo_do_dia(cfg: dict) -> str:
    cliente = Cliente(cfg)
    pasta = config.caminho(cfg["memoria"]["inteligencia"])
    conversa = Conversa(
        cliente, cfg["contexto"]["limite"], carregar_personalidade(config.caminho(cfg["personalidade"])),
        inteligencia_para_prompt(pasta, cfg["memoria"]["inteligencia_inteira_ate"]),
        ultima_conversa=ultimo_resumo(config.caminho(cfg["memoria"]["resumos"])),
        memoria=ler_memoria(config.caminho(cfg["memoria"]["memoria"]))[0],
    )
    caixa = caixa_de_email(cfg)
    try:
        emails = caixa(DIAS_DE_EMAIL) if caixa else None
    except Exception as e:  # sem rede ou senha errada: o resumo sai sem os e-mails, e avisa
        print(f"[aviso] não consegui ler o e-mail: {e}")
        emails = None
    return "".join(conversa.responder(pedido_do_dia(emails, datetime.now()))).strip()


def dia(cfg: dict, notificar: bool) -> None:
    texto = resumo_do_dia(cfg)
    print(texto)
    Registro(config.caminho(cfg["logs"]), origem="dia").anotar("dia", texto=texto)
    if notificar:
        subprocess.run(["notify-send", "--app-name=Tony", "Tony", texto], check=False)


# Restart: ao ligar o PC (Persistent=true), o timer dispara antes de a rede subir e o modelo na nuvem
# não responde. O systemd tenta de novo a cada 2 minutos, até 6 vezes na hora.
SERVICO = """[Unit]
Description=Tony: resumo do dia
StartLimitIntervalSec=1h
StartLimitBurst=6

[Service]
Type=oneshot
Restart=on-failure
RestartSec=2min
WorkingDirectory={raiz}
ExecStart={uv} run tony dia --notificar
"""
TIMER = """[Unit]
Description=Tony: resumo do dia às {hora}

[Timer]
OnCalendar=*-*-* {hora}:00
Persistent=true

[Install]
WantedBy=timers.target
"""


def agendar(hora: str) -> None:
    """Instala (ou atualiza) o timer. Persistent=true: se o PC estava desligado na hora, roda ao ligar."""
    uv = subprocess.run(["which", "uv"], capture_output=True, text=True).stdout.strip()
    if not uv:
        raise SystemExit("não achei o uv no PATH.")
    pasta = Path.home() / ".config/systemd/user"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "tony-dia.service").write_text(SERVICO.format(raiz=config.RAIZ, uv=uv), encoding="utf-8")
    (pasta / "tony-dia.timer").write_text(TIMER.format(hora=hora), encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "tony-dia.timer"], check=True)
    print(f"Agendado: todo dia às {hora}. Ver: systemctl --user list-timers tony-dia.timer · "
          f"Desligar: systemctl --user disable --now tony-dia.timer")
