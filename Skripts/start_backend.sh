#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
