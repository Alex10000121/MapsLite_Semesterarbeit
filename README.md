# MapsLite – Web-Applikation (FastAPI + ZODB + Leaflet + OpenRouteService)

Diese Anwendung berechnet Routen zwischen zwei Adressen (OpenRouteService), zeigt sie auf einer Karte (Leaflet) und speichert persönliche Routen serverseitig in **ZODB** (objektorientierte Datenbank, keine SQL). Häufige Suchanfragen werden **lokal im Browser** gezählt und angezeigt.

## Features

- Single Page Application (Vanilla JS, Leaflet)
- Autocomplete & Geocoding (ORS)
- Routing (ORS v2 `/v2/directions/driving-car`) – **ohne** `geometry_format` (ORS liefert encoded polyline)
- Polyline-Decode im Frontend
- Top 10 Suchanfragen (localStorage)
- REST API (FastAPI RML2): `GET/POST /api/routes`, `GET/DELETE /api/routes/{route_identifier}`
- ZODB als Datenbank (keine SQL → resistent gegen SQL-Injection)
- Akzeptanztest (Playwright)
- Unit-Tests (pytest)
- CORS konfigurierbar

---

## Voraussetzungen

- Node.js 18+
- Python 3.11+ (getestet mit 3.13)
- (Windows) ggf. **Visual Studio Build Tools** mit „Desktop development with C++“, falls ZODB-Abhängigkeiten C-Extensions bauen müssen.

---

## Einrichtung

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env   # wenn noch nicht vorhanden
