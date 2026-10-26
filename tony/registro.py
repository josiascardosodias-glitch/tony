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
        anotar(self.arquivo, tipo, **dados)

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


def anotar(arquivo: Path, tipo: str, **dados) -> None:
    evento = {"hora": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, **dados}
    with arquivo.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def conversa_sem_resumo(pasta: Path) -> tuple[Path, list[dict]] | None:
    """A última conversa, se ela acabou sem resumo (terminal fechado, queda de rede): (log, turnos).

    Olha só o log mais recente que tem conversa (os do `tony dia` e as sessões vazias não contam);
    os turnos depois do último resumo dele são os que ninguém resumiu.
    """
    for arquivo in sorted(pasta.glob("*.jsonl"), reverse=True) if pasta.is_dir() else []:
        eventos = [json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha.strip()]
        if not any(e["tipo"] == "turno" for e in eventos):
            continue
        turnos = []
        for e in eventos:
            if e["tipo"] == "resumo":
                turnos = []
            elif e["tipo"] == "turno":
                turnos.append(e)
        return (arquivo, turnos) if turnos else None
    return None
