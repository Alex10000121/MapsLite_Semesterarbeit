$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\backend")
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
