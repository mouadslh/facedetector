#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON=""
for candidate in python3.11 python3.12 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.10, 3.11 ou 3.12 est requis. Installez Python puis relancez ce script."
  exit 1
fi

if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/generate_sounds.py
streamlit run app.py
