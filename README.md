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
- API-Key für [OpenRouteService](https://openrouteservice.org)

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
# ORS_API_KEY in .env ergänzen (siehe unten)
```

### 2) Frontend

```bash
npm install
```

---

## Anwendung starten

### Backend

```bash
./Skripts/start_backend.sh
```

Der Startskript aktiviert die virtuelle Umgebung und startet den Entwicklungsserver per `uvicorn` auf Port `8000`. Alternativ kann der Befehl manuell ausgeführt werden:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
npm run serve
```

Der statische HTTP-Server (`http-server`) läuft standardmäßig auf Port `5500`. Nach dem Start sind Frontend und Backend unter <http://localhost:5500> bzw. <http://localhost:8000> erreichbar.

---

## Umgebungsvariablen

Die Anwendung liest Konfigurationswerte aus der Datei `backend/.env` ein. Eine Beispielkonfiguration befindet sich in `backend/.env.example` und kann per `cp` kopiert und angepasst werden. Relevante Variablen:

| Variable            | Beschreibung                                                    | Standardwert                         |
| ------------------- | ---------------------------------------------------------------- | ----------------------------------- |
| `DATABASE_FILE`     | Pfad zur ZODB-Datei                                              | `./data/appdata.fs`                 |
| `CORS_ALLOW_ORIGINS`| Kommagetrennte Liste erlaubter Frontend-URLs (CORS)              | `http://127.0.0.1:5500,http://localhost:5500` |
| `ORS_API_KEY`       | API-Key für [OpenRouteService](https://openrouteservice.org)     | _muss gesetzt werden_               |

Der API-Key für OpenRouteService ist erforderlich, damit das Backend Geocoding und Routing-Anfragen stellvertretend für das Frontend weiterleiten kann.


## Tests

### Backend-Unit-Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

### End-to-End-Tests (Playwright)

```bash
# Bei der ersten Ausführung Browser installieren
npx playwright install

# Tests ausführen
npm run test:e2e

# optional mit sichtbarem Browser
npm run test:e2e:headed

# Test-Report anzeigen
npm run test:e2e:report
```
