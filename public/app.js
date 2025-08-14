// Configuration
const ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImFmMmZmZmY2ZjgzZjRlOTFiYWFiNmY3NmUxNTU2ODc0IiwiaCI6Im11cm11cjY0In0=";
const ORS_BASE = "https://api.openrouteservice.org";

// Backend API base
const API_BASE = "http://localhost:8000";

// Map setup
const map = L.map('map').setView([47.3769, 8.5417], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap Mitwirkende'
}).addTo(map);
let routeLayer = null;

const startInput = document.getElementById('start');
const zielInput = document.getElementById('ziel');
const startSug = document.getElementById('start-suggestions');
const zielSug = document.getElementById('ziel-suggestions');
const form = document.getElementById('route-form');
const topList = document.getElementById('top-list');
const savedList = document.getElementById('saved-list');

// Helpers
function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function showSuggestions(listElem, items, onPick) {
    if (!items || items.length === 0) {
        listElem.style.display = 'none';
        listElem.innerHTML = '';
        return;
    }
    listElem.innerHTML = '';
    items.forEach(it => {
        const li = document.createElement('li');
        li.textContent = it.properties.label;
        li.addEventListener('click', () => {
            onPick(it);
            listElem.style.display = 'none';
            listElem.innerHTML = '';
        });
        listElem.appendChild(li);
    });
    listElem.style.display = 'block';
}

async function orsAutocomplete(query) {
    if (!ORS_API_KEY) return [];
    const url = new URL(ORS_BASE + "/geocode/autocomplete");
    url.searchParams.set("api_key", ORS_API_KEY);
    url.searchParams.set("text", query);
    url.searchParams.set("size", "5");
    const r = await fetch(url);
    if (!r.ok) {
        console.error("ORS autocomplete error", r.status, await r.text().catch(() => ""));
        return [];
    }
    const data = await r.json().catch(() => null);
    if (!data || !Array.isArray(data.features)) {
        console.warn("Autocomplete Antwort ohne Features", data);
        return [];
    }
    return data.features;
}

async function orsGeocode(query) {
    if (!ORS_API_KEY) return [];
    const url = new URL(ORS_BASE + "/geocode/search");
    url.searchParams.set("api_key", ORS_API_KEY);
    url.searchParams.set("text", query);
    url.searchParams.set("size", "1");
    const r = await fetch(url);
    if (!r.ok) {
        console.error("ORS geocode error", r.status, await r.text().catch(() => ""));
        return [];
    }
    const data = await r.json().catch(() => null);
    if (!data || !Array.isArray(data.features)) {
        console.warn("Geocode Antwort ohne Features", data);
        return [];
    }
    return data.features;
}

// Draw route handling GeoJSON, JSON und kodierte Polyline
async function drawRoute(startCoord, endCoord) {
    // GeoJSON per Query verlangen
    const url = ORS_BASE + "/v2/directions/driving-car?format=geojson";

    const r = await fetch(url, {
        method: "POST",
        headers: {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/geo+json, application/json"
        },
        body: JSON.stringify({
            coordinates: [
                [startCoord[0], startCoord[1]],
                [endCoord[0], endCoord[1]]
            ]
        })
    });

    if (!r.ok) {
        const txt = await r.text().catch(() => "");
        console.error("ORS directions error", r.status, txt);
        alert("Routenberechnung fehlgeschlagen: " + r.status);
        return null;
    }

    let data;
    try { data = await r.json(); }
    catch (e) {
        console.error("ORS directions JSON parse error", e);
        alert("Routenberechnung fehlgeschlagen: ungueltige Antwort");
        return null;
    }

    // A) GeoJSON FeatureCollection
    if (data && Array.isArray(data.features) && data.features.length > 0) {
        const feat = data.features[0];
        if (!feat.geometry || !Array.isArray(feat.geometry.coordinates)) {
            console.error("Unerwartetes GeoJSON Format", data);
            alert("Routenberechnung fehlgeschlagen: unerwartetes Format");
            return null;
        }
        const coords = feat.geometry.coordinates.map(c => [c[1], c[0]]);
        if (routeLayer) routeLayer.remove();
        routeLayer = L.polyline(coords, { weight: 6 }).addTo(map);
        map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });
        return feat;
    }

    // B) JSON mit routes[0]
    if (data && Array.isArray(data.routes) && data.routes.length > 0) {
        const r0 = data.routes[0];

        // B1) GeoJSON Koordinaten vorhanden
        if (r0.geometry && Array.isArray(r0.geometry.coordinates)) {
            const coords = r0.geometry.coordinates.map(c => [c[1], c[0]]);
            if (routeLayer) routeLayer.remove();
            routeLayer = L.polyline(coords, { weight: 6 }).addTo(map);
            map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });
            return { geometry: r0.geometry, properties: { summary: r0.summary || {} } };
        }

        // B2) kodierter Polyline String
        if (r0.geometry && typeof r0.geometry === "string") {
            let coords = decodePolyline(r0.geometry, 5);
            if (!coords || coords.length === 0 || !coords.every(p => Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180)) {
                coords = decodePolyline(r0.geometry, 6);
            }
            if (!coords || coords.length === 0) {
                console.error("Polyline konnte nicht dekodiert werden", r0.geometry);
                alert("Routenberechnung fehlgeschlagen: Geometrie unlesbar");
                return null;
            }
            const latlng = coords.map(c => [c[0], c[1]]);
            if (routeLayer) routeLayer.remove();
            routeLayer = L.polyline(latlng, { weight: 6 }).addTo(map);
            map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });
            return { geometry: { type: "LineString", coordinates: coords.map(c => [c[1], c[0]]) }, properties: { summary: r0.summary || {} } };
        }
    }

    console.warn("Keine Route gefunden. Antwort:", data);
    alert("Keine Route gefunden. Bitte andere Adressen versuchen");
    return null;
}

// Decoder fuer Google Encoded Polyline
function decodePolyline(str, precisionDigits) {
    const precision = Math.pow(10, precisionDigits || 5);
    let index = 0, lat = 0, lng = 0, coordinates = [];

    while (index < str.length) {
        let result = 0, shift = 0, b;
        do {
            b = str.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        const dlat = (result & 1) ? ~(result >> 1) : (result >> 1);
        lat += dlat;

        result = 0; shift = 0;
        do {
            b = str.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        const dlng = (result & 1) ? ~(result >> 1) : (result >> 1);
        lng += dlng;

        coordinates.push([lat / precision, lng / precision]);
    }
    return coordinates;
}

function addTopSearch(key) {
    const stats = JSON.parse(localStorage.getItem("topSearches") || "{}");
    stats[key] = (stats[key] || 0) + 1;
    localStorage.setItem("topSearches", JSON.stringify(stats));
    renderTopSearches();
}

function renderTopSearches() {
    const stats = JSON.parse(localStorage.getItem("topSearches") || "{}");
    const arr = Object.entries(stats).sort((a,b) => b[1]-a[1]).slice(0,10);
    topList.innerHTML = "";
    arr.forEach(([label, count]) => {
        const li = document.createElement("li");
        li.textContent = label + " (" + count + ")";
        topList.appendChild(li);
    });
}

async function saveRouteToBackend(routeInfo) {
    const r = await fetch(API_BASE + "/api/routes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(routeInfo)
    });
    return r.ok ? r.json() : null;
}

async function refreshSavedRoutes() {
    const r = await fetch(API_BASE + "/api/routes");
    if (!r.ok) return;
    const items = await r.json();
    savedList.innerHTML = "";
    for (const it of items) {
        const li = document.createElement("li");
        li.innerHTML = '<span>' + it.start_text + ' → ' + it.end_text + '</span>';
        const showBtn = document.createElement("button");
        showBtn.className = "primary";
        showBtn.textContent = "Anzeigen";
        showBtn.addEventListener("click", async () => {
            if (it.geometry && it.geometry.coordinates) {
                const coords = it.geometry.coordinates.map(c => [c[1], c[0]]);
                if (routeLayer) routeLayer.remove();
                routeLayer = L.polyline(coords, { weight: 6 }).addTo(map);
                map.fitBounds(routeLayer.getBounds(), { padding: [30,30] });
            }
        });
        const delBtn = document.createElement("button");
        delBtn.textContent = "Löschen";
        delBtn.addEventListener("click", async () => {
            await fetch(API_BASE + "/api/routes/" + it.id, { method: "DELETE" });
            refreshSavedRoutes();
        });
        li.appendChild(showBtn);
        li.appendChild(delBtn);
        savedList.appendChild(li);
    }
}

// Autocomplete bindings
startInput.addEventListener('input', debounce(async () => {
    const q = startInput.value.trim();
    if (q.length < 3) { showSuggestions(startSug, [], ()=>{}); return; }
    const items = await orsAutocomplete(q);
    showSuggestions(startSug, items, f => {
        startInput.value = f.properties.label;
        startInput.dataset.lon = f.geometry.coordinates[0];
        startInput.dataset.lat = f.geometry.coordinates[1];
    });
}, 250));

zielInput.addEventListener('input', debounce(async () => {
    const q = zielInput.value.trim();
    if (q.length < 3) { showSuggestions(zielSug, [], ()=>{}); return; }
    const items = await orsAutocomplete(q);
    showSuggestions(zielSug, items, f => {
        zielInput.value = f.properties.label;
        zielInput.dataset.lon = f.geometry.coordinates[0];
        zielInput.dataset.lat = f.geometry.coordinates[1];
    });
}, 250));

// Form submit
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const startText = startInput.value.trim();
    const zielText = zielInput.value.trim();

    if (!startText || !zielText) {
        alert("Bitte Start und Ziel eingeben");
        return;
    }

    const sList = await orsGeocode(startText);
    const zList = await orsGeocode(zielText);

    if (!sList[0] || !zList[0]) {
        console.warn("Geocode leer", { sList, zList });
        alert("Adresse nicht gefunden. Bitte präziser eingeben, z. B. mit Ort und Land");
        return;
    }

    const sLon = sList[0].geometry.coordinates[0];
    const sLat = sList[0].geometry.coordinates[1];
    const zLon = zList[0].geometry.coordinates[0];
    const zLat = zList[0].geometry.coordinates[1];

    const feat = await drawRoute([sLon, sLat], [zLon, zLat]);
    if (!feat) return;

    const dist = feat.properties?.summary?.distance ?? 0;
    const dur = feat.properties?.summary?.duration ?? 0;
    const geometry = feat.geometry;

    addTopSearch(startText + " → " + zielText);

    const saved = await saveRouteToBackend({
        start_text: startText,
        end_text: zielText,
        start_coords: { lon: sLon, lat: sLat },
        end_coords: { lon: zLon, lat: zLat },
        distance: dist,
        duration: dur,
        geometry: geometry
    });
    if (saved) refreshSavedRoutes();
});

// Init
renderTopSearches();
refreshSavedRoutes();
