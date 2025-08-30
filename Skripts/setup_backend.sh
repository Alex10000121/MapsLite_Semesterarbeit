#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

echo "Backend-Setup fertig."
