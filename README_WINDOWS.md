# MapsLite – Windows-Setup & Startanleitung

## Voraussetzungen
- Node.js 18+
- Python 3.11+
- (Optional) Visual Studio Build Tools mit "Desktop development with C++" für Pakete mit C-Extensions
- API-Key für [OpenRouteService](https://openrouteservice.org)

---

## 1) Backend einrichten (PowerShell)
```powershell
cd backend
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env  # falls noch nicht vorhanden
# ORS_API_KEY in .env eintragen
```

## 2) Frontend einrichten
```powershell
npm.cmd install
```

---

## Anwendung starten

### Backend
```powershell
.\Skripts\start_backend.ps1
# oder manuell
cd backend
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```powershell
npm.cmd run serve
```

Der statische Server läuft auf Port 5500, das Backend auf Port 8000.

---

## Umgebungsvariablen
Konfigurationswerte werden aus `backend/.env` geladen. Wichtige Variablen:
- `DATABASE_FILE` – Pfad zur ZODB-Datei
- `CORS_ALLOW_ORIGINS` – erlaubte Frontend-URLs
- `ORS_API_KEY` – API-Key für OpenRouteService (obligatorisch)

---

## Hinweise
- PowerShell-Skripte erfordern ggf. temporär: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- Die Windows-Skripte aktivieren die virtuelle Umgebung automatisch.
- Falls `npm` wegen einer gesperrten `npm.ps1` nicht startet, können die Befehle mit `npm.cmd` ausgeführt werden.
