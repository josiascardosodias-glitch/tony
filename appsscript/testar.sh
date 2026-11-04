#!/usr/bin/env bash
# Testes do Tony no Apps Script: gera os casos com o Python (as respostas certas) e roda o node --test.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python scripts/casos_appsscript.py
node --test appsscript/testes/*.test.js
