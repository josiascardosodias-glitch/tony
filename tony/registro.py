"""Log da sessão em JSON Lines (uma linha JSON por evento): a matéria-prima para o Tony evoluir."""

import json
from datetime import datetime
from pathlib import Path


class Registro:
    def __init__(self, pasta: Path, **inicio):
        pasta.mkdir(parents=True, exist_ok=True)
        self.arquivo = pasta / f"{datetime.now():%Y-%m-%d_%H%M%S}.jsonl"
        self.turno = 0
        self.anotar("inicio", **inicio)

    def anotar(self, tipo: str, **dados) -> None:
        evento = {"hora": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, **dados}
        with self.arquivo.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")

    def turno_completo(self, fala: str, resposta: str, segundos: float, ferramentas: list[dict] = ()) -> None:
        self.turno += 1
        extra = {"ferramentas": list(ferramentas)} if ferramentas else {}
        self.anotar("turno", turno=self.turno, usuario=fala, tony=resposta, segundos=round(segundos, 1), **extra)

    def marcar(self, valor: str, motivo: str = "") -> bool:
        """Marca o último turno como 'bom' ou 'ruim'. Devolve False se ainda não houve turno."""
        if not self.turno:
            return False
        self.anotar("marca", turno=self.turno, valor=valor, motivo=motivo)
        return True
