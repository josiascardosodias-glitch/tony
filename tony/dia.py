"""O Tony fala primeiro: `tony dia` escreve o resumo do dia; `tony agendar` instala um timer do systemd
(do seu usuário, sem sudo) que roda `tony dia --notificar` todo dia, como notificação na área de trabalho
e mensagem no Telegram.

Desde a v4 o resumo é montado pelo código, com o `eventos.json`: zero token. É uma lista do que está
marcado para hoje e os próximos 7 dias, e quantas datas esperam a sua decisão.
"""

import subprocess
from datetime import date, timedelta
from pathlib import Path

from . import config
from .coleta import ler_json
from .consulta import linha
from .registro import Registro

DIAS_A_FRENTE = 7


def resumo_do_dia(cfg: dict, hoje: date | None = None) -> str:
    hoje = hoje or date.today()
    banco = ler_json(config.caminho(cfg["coleta"]["eventos"]), {"eventos": {}, "revisar": {}})
    fim = (hoje + timedelta(days=DIAS_A_FRENTE)).isoformat()
    proximos = sorted((e for e in banco["eventos"].values() if hoje.isoformat() <= e["data"] <= fim),
                      key=lambda e: (e["data"], e["hora"] or ""))
    de_hoje = [e for e in proximos if e["data"] == hoje.isoformat()]
    depois = [e for e in proximos if e["data"] != hoje.isoformat()]
    partes = []
    if de_hoje:
        partes.append("Hoje:\n" + "\n".join(linha(e, hoje) for e in de_hoje))
    if depois:
        partes.append(f"Nos próximos {DIAS_A_FRENTE} dias:\n" + "\n".join(linha(e, hoje) for e in depois))
    if not partes:
        partes.append(f"Nada marcado para hoje nem para os próximos {DIAS_A_FRENTE} dias.")
    revisar = sum(e["data"] >= hoje.isoformat() for e in banco["revisar"].values())
    if revisar:
        partes.append(f"{revisar} data(s) esperando você decidir: /revisar no Telegram.")
    return "\n\n".join(partes)


def dia(cfg: dict, notificar: bool) -> None:
    texto = resumo_do_dia(cfg)
    print(texto)
    Registro(config.caminho(cfg["logs"]), origem="dia").anotar("dia", texto=texto)
    if not notificar:
        return
    subprocess.run(["notify-send", "--app-name=Tony", "Tony", texto], check=False)
    if config.caminho(cfg["telegram"]["token_arquivo"]).is_file():
        from .telegram import Telegram, credenciais

        Telegram(*credenciais(cfg)).enviar(f"Bom dia.\n\n{texto}")


# Restart: ao ligar o PC (Persistent=true), o timer dispara antes de a rede subir e o modelo na nuvem
# não responde. O systemd tenta de novo a cada 2 minutos, até 6 vezes na hora. OnFailure: só quando as
# 6 falham a unidade fica "failed" e o aviso sai; antes, a falha só aparecia no journalctl.
SERVICO = """[Unit]
Description=Tony: resumo do dia
StartLimitIntervalSec=1h
StartLimitBurst=6
OnFailure=tony-dia-falhou.service

[Service]
Type=oneshot
Restart=on-failure
RestartSec=2min
WorkingDirectory={raiz}
ExecStart={uv} run tony dia --notificar
"""
AVISO_DE_FALHA = """[Unit]
Description=Tony: aviso de que o resumo do dia falhou

[Service]
Type=oneshot
ExecStart=/usr/bin/notify-send --app-name=Tony --urgency=critical "Tony" "Não consegui fazer o resumo do dia: as 6 tentativas falharam. Para ver o motivo: journalctl --user -u tony-dia"
"""
# O bot fica sempre no ar (a coleta de hora em hora roda dentro dele); Restart=always cobre queda de
# rede e erro inesperado. default.target: sobe quando você entra na sessão.
BOT = """[Unit]
Description=Tony: Telegram e coleta dos e-mails
After=network-online.target

[Service]
Restart=always
RestartSec=30
WorkingDirectory={raiz}
ExecStart={uv} run tony telegram

[Install]
WantedBy=default.target
"""
TIMER = """[Unit]
Description=Tony: resumo do dia às {hora}

[Timer]
OnCalendar=*-*-* {hora}:00
Persistent=true

[Install]
WantedBy=timers.target
"""


def unidades(hora: str, raiz: Path, uv: str) -> dict[str, str]:
    """{nome do arquivo: conteúdo} das unidades do systemd que o `agendar` instala."""
    return {
        "tony-dia.service": SERVICO.format(raiz=raiz, uv=uv),
        "tony-dia-falhou.service": AVISO_DE_FALHA,
        "tony-dia.timer": TIMER.format(hora=hora),
        "tony-telegram.service": BOT.format(raiz=raiz, uv=uv),
    }


def agendar(hora: str) -> None:
    """Instala (ou atualiza) o timer. Persistent=true: se o PC estava desligado na hora, roda ao ligar."""
    uv = subprocess.run(["which", "uv"], capture_output=True, text=True).stdout.strip()
    if not uv:
        raise SystemExit("não achei o uv no PATH.")
    pasta = Path.home() / ".config/systemd/user"
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in unidades(hora, config.RAIZ, uv).items():
        (pasta / nome).write_text(conteudo, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "tony-dia.timer"], check=True)
    print(f"Agendado: todo dia às {hora}, a partir de {config.RAIZ}. Ver: systemctl --user list-timers tony-dia.timer · "
          f"Desligar: systemctl --user disable --now tony-dia.timer")
    if config.caminho(config.carregar()["telegram"]["token_arquivo"]).is_file():
        subprocess.run(["systemctl", "--user", "enable", "--now", "tony-telegram.service"], check=True)
        print("Telegram no ar: systemctl --user status tony-telegram · logs: journalctl --user -u tony-telegram")
