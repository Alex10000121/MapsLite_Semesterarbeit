# LiteMaps mit ZODB

Ziel: SPA Frontend mit OpenRouteService sowie FastAPI Backend mit ZODB zum Speichern persönlicher Routen.

## Schnellstart

1. Backend
   - Python 3.11 empfohlen
   - `cd backend`
   - `python -m venv .venv && . .venv/bin/activate` auf macOS Linux. Unter Windows `.\.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --port 8000`

2. Frontend
   - Node 18 plus
   - `cd ..`
   - `npm install`
   - `npm run serve`
   - Öffne http://localhost:5500/public/index.html
   - Trage deinen OpenRouteService Key in `public/app.js` bei `ORS_API_KEY` ein

3. Tests
   - API Unit Tests: im Ordner `backend` `pytest -q`
   - E2E Tests: im Projektroot `npx playwright install` dann `npm run test:e2e`

## REST API

- Swagger UI: http://localhost:8000/docs
- Endpunkte:
  - `GET /health`
  - `GET /api/routes`
  - `POST /api/routes`
  - `GET /api/routes/{id}`
  - `DELETE /api/routes/{id}`

## Sicherheit

- Keine SQL Engine vorhanden, daher ist klassische SQL Injection nicht anwendbar.
- Eingaben werden validiert, CORS ist aktiviert.
- API Key darf nicht im Repository landen. Nutze `.env` oder Umgebungsvariablen.

## Bewertungskriterien Abdeckung

- Frontend: Routenberechnung und Anzeige, Autocomplete, Top 10 lokale Suchanfragen.
- REST API: ZODB als Datenbank, CRUD, Swagger durch FastAPI, Richardson Level 2.
- Tests: Pytest Unit Tests, Playwright Akzeptanztest.
- Deployment: nutze CI deiner Wahl für automatische Tests und Deployment.
