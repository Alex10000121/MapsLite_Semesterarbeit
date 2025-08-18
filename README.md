# LiteMaps ZODB – Routenplaner (SPA + FastAPI + ZODB)

Eine einfache Web‑App, die zwei Orte entgegen nimmt, die Route via **OpenRouteService (ORS)** berechnet, auf einer Karte anzeigt, häufige Suchanfragen lokal speichert und **persönliche Routen** serverseitig über eine **REST‑API** mit **ZODB** persistiert.  
Frontend als Single Page App (VanillaJS + Leaflet), Backend als FastAPI‑Service, Tests für Backend (pytest) und E2E (Playwright).

---

## Inhalt
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration (ORS API Key)](#konfiguration-ors-api-key)
- [Starten](#starten)
- [Bedienung](#bedienung)
- [REST-API (Swagger)](#rest-api-swagger)
- [Tests](#tests)
    - [Backend (pytest)](#backend-pytest)
    - [Frontend (Playwright)](#frontend-playwright)
- [Sicherheit (SQL Injection u.ä.)](#sicherheit-sql-injection-ua)
- [Architektur](#architektur)
- [Troubleshooting](#troubleshooting)

---

## Voraussetzungen
- **macOS / Linux / Windows**
- **Python 3.13** (Homebrew: `brew install python`)
- **Node.js + npm**
- Internetzugang (für ORS)

---

## Installation

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip

# Abhängigkeiten inkl. httpx (für Tests):
python -m pip install -r requirements.txt

# Optional (empfohlen): Dev-Tools inkl. pytest
python -m pip install -r requirements-dev.txt
```

## Starten

# Backend

cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# Frontend

cd frontend
npm run serve