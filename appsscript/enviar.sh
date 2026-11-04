#!/usr/bin/env bash
# Envia o Tony para o Apps Script: testes, o _conhecimento.js (personalidade e Inteligência) e o clasp push.
set -euo pipefail
cd "$(dirname "$0")"
./testar.sh
uv run python gerar_conhecimento.py
npx @google/clasp push --force
