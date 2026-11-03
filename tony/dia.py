"""O Tony fala primeiro: `tony dia` escreve o resumo do dia; `tony agendar` instala um timer do systemd
(do seu usuário, sem sudo) que roda `tony dia --notificar` todo dia, como notificação na área de trabalho.

Até a coleta de e-mails (etapas 3 a 6 da v4), o resumo sai só da Inteligência.
"""

import subprocess
from datetime import datetime
from pathlib import Path

from . import config
from .cliente import Cliente
from .conversa import Conversa, calendario
from .memoria import carregar_personalidade, ler_inteligencia
from .registro import Registro

PEDIDO_DIA = (
    "[Mensagem agendada: a pessoa não falou nada; você é quem começa.] Escreva a notificação que abre "
    "o dia dela: em até 3 frases, o que importa hoje e nos próximos 7 dias (provas, entregas, "
    "pendências), tirado só do que está nas suas notas sobre ela. Você não lê e-mail: não diga que "
    "olhou e-mails. Use o calendário abaixo para as datas; não calcule de cabeça. Se não houver "
    "nada marcado, diga isso em uma frase curta. Sem saudação longa e sem pergunta no fim."
)


def pedido_do_dia(hoje: datetime) -> str:
    return f"{PEDIDO_DIA}\n\nCalendário:\n{calendario(hoje, 8)}"


def resumo_do_dia(cfg: dict) -> str:
    conversa = Conversa(
        Cliente(cfg), cfg["contexto"]["limite"], carregar_personalidade(config.caminho(cfg["personalidade"])),
        ler_inteligencia(config.caminho(cfg["memoria"]["inteligencia"])),
    )
    return "".join(conversa.responder(pedido_do_dia(datetime.now()))).strip()


def dia(cfg: dict, notificar: bool) -> None:
    texto = resumo_do_dia(cfg)
    print(texto)
    Registro(config.caminho(cfg["logs"]), origem="dia").anotar("dia", texto=texto)
    if notificar:
        subprocess.run(["notify-send", "--app-name=Tony", "Tony", texto], check=False)


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
