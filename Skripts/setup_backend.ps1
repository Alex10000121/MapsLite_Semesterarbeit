$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\backend")

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if (-Not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

Write-Host "Backend-Setup fertig."
