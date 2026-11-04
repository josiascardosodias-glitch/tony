"""Gera `src/_conhecimento.js` com a personalidade e a Inteligência, como o Python carrega
(`memoria.carregar_personalidade` e `memoria.ler_inteligencia`). Fica fora do git: a Inteligência é
pessoal. Roda no `enviar.sh`, antes do `clasp push`.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from tony import config  # noqa: E402
from tony.memoria import carregar_personalidade, ler_inteligencia  # noqa: E402

cfg = config.carregar()
personalidade = carregar_personalidade(config.caminho(cfg["personalidade"]))
inteligencia = ler_inteligencia(config.caminho(cfg["memoria"]["inteligencia"]))
saida = Path(__file__).resolve().parent / "src" / "_conhecimento.js"
# A hora muda o arquivo a cada envio: o clasp só manda tudo (e apaga o que sumiu) quando algo mudou.
saida.write_text("// Gerado por appsscript/gerar_conhecimento.py: não edite. Fora do git (a Inteligência é pessoal).\n"
                 f"// Enviado em {datetime.now().isoformat(timespec='seconds')}.\n"
                 f"const PERSONALIDADE = {json.dumps(personalidade, ensure_ascii=False)};\n"
                 f"const INTELIGENCIA = {json.dumps(inteligencia, ensure_ascii=False)};\n", encoding="utf-8")
print(f"{saida.name}: personalidade {len(personalidade)} caracteres, Inteligência {len(inteligencia)}")
