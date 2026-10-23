"""Lê a configuração: config.exemplo.yaml (padrões, no git) + config.local.yaml (seus valores, fora do git)."""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent


def _mesclar(base: dict, extra: dict) -> dict:
    """Sobrescreve `base` com `extra`, entrando nos dicionários aninhados."""
    for chave, valor in extra.items():
        if isinstance(valor, dict) and isinstance(base.get(chave), dict):
            _mesclar(base[chave], valor)
        else:
            base[chave] = valor
    return base


def carregar() -> dict:
    cfg = yaml.safe_load((RAIZ / "config.exemplo.yaml").read_text(encoding="utf-8"))
    local = RAIZ / "config.local.yaml"
    if local.exists():
        _mesclar(cfg, yaml.safe_load(local.read_text(encoding="utf-8")) or {})
    return cfg


def caminho(valor: str) -> Path | None:
    """Caminho do config: `~` vira a home, relativo parte da raiz do projeto, vazio vira None."""
    if not valor:
        return None
    p = Path(valor).expanduser()
    return p if p.is_absolute() else RAIZ / p
