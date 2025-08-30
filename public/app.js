// ==============================
// Frontend-Konfiguration
// ==============================
const API_BASE = "http://127.0.0.1:8000"; // FastAPI-Backend

// ==============================
// Leaflet-Karte
// ==============================
const map = L.map('map').setView([47.3769, 8.5417], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap Mitwirkende'
}).addTo(map);
let currentRouteLayer = null;

// ==============================
// UI-Elemente
// ==============================
const startInput = document.getElementById('start');
const zielInput = document.getElementById('ziel');
const startSug = document.getElementById('start-suggestions');
const zielSug = document.getElementById('ziel-suggestions');
const form = document.getElementById('route-form');
const topList = document.getElementById('top-list');
const savedList = document.getElementById('saved-list');

// ==============================
// Helpers
// ==============================
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
    const label = it?.properties?.label || it?.properties?.name || '(ohne Label)';
    const li = document.createElement('li');
    li.textContent = label;
    li.addEventListener('click', () => {
      onPick(it);
      listElem.style.display = 'none';
      listElem.innerHTML = '';
    });
    listElem.appendChild(li);
  });
  listElem.style.display = 'block';
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
    li.textContent = `${label} (${count})`;
    topList.appendChild(li);
  });
}

// ==============================
// Backend-Proxy: ORS (kein Key im Frontend)
// ==============================
async function apiAutocomplete(query) {
  if (!query) return [];
  const url = new URL(API_BASE + "/api/ors/autocomplete");
  url.searchParams.set("text", query);
  url.searchParams.set("size", "5");
  const r = await fetch(url);
  if (!r.ok) return [];
  const data = await r.json();
  return data.features || [];
}

async function apiGeocodeOne(query) {
  if (!query) return null;
  const url = new URL(API_BASE + "/api/ors/geocode");
  url.searchParams.set("text", query);
  url.searchParams.set("size", "1");
  const r = await fetch(url);
  if (!r.ok) return null;
  const data = await r.json();
  return data.features && data.features[0] ? data.features[0] : null;
}

async function apiDirections(startLon, startLat, endLon, endLat, profile = "driving-car") {
  const r = await fetch(API_BASE + "/api/ors/directions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start: [startLon, startLat],
      end: [endLon, endLat],
      profile
    })
  });
  if (!r.ok) {
    const txt = await r.text();
    console.error("Directions failed:", r.status, txt);
    throw new Error("Routenberechnung fehlgeschlagen");
  }
  return r.json();
}

// ==============================
// Polyline-Decoding (encoded -> [lat, lon])
// ==============================
function decodePolyline(encoded, precision = 1e-5) {
  let index = 0, lat = 0, lng = 0, coordinates = [];
  while (index < encoded.length) {
    let b, shift = 0, result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    const deltaLat = (result & 1) ? ~(result >> 1) : (result >> 1);
    lat += deltaLat;

    shift = 0; result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    const deltaLng = (result & 1) ? ~(result >> 1) : (result >> 1);
    lng += deltaLng;

    coordinates.push([lat * precision, lng * precision]); // [lat, lon]
  }
  return coordinates;
}

async function drawEncodedRoute(encodedGeometry) {
  const latlon = decodePolyline(encodedGeometry); // [ [lat, lon], ... ]
  if (!latlon.length) return;
  const leafletCoords = latlon.map(p => [p[0], p[1]]);
  if (currentRouteLayer) currentRouteLayer.remove();
  currentRouteLayer = L.polyline(leafletCoords, { weight: 6 }).addTo(map);
  map.fitBounds(currentRouteLayer.getBounds(), { padding: [30,30] });
}

// ==============================
// Backend-CRUD (ZODB)
// ==============================
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
    li.innerHTML = `<span>${it.start_text} → ${it.end_text}</span>`;
    const showBtn = document.createElement("button");
    showBtn.className = "primary";
    showBtn.textContent = "Anzeigen";
    showBtn.addEventListener("click", async () => {
      if (it.geometry_encoded) {
        await drawEncodedRoute(it.geometry_encoded);
      }
    });
    const delBtn = document.createElement("button");
    delBtn.textContent = "Löschen";
    delBtn.addEventListener("click", async () => {
      await fetch(API_BASE + "/api/routes/" + it.identifier, { method: "DELETE" });
      refreshSavedRoutes();
    });
    li.appendChild(showBtn);
    li.appendChild(delBtn);
    savedList.appendChild(li);
  }
}

// ==============================
// Autocomplete-Bindings
// ==============================
startInput.addEventListener('input', debounce(async () => {
  const q = startInput.value.trim();
  if (q.length < 3) { showSuggestions(startSug, [], ()=>{}); return; }
  const items = await apiAutocomplete(q);
  showSuggestions(startSug, items, f => {
    startInput.value = f.properties.label;
    startInput.dataset.lon = f.geometry.coordinates[0];
    startInput.dataset.lat = f.geometry.coordinates[1];
  });
}, 250));

zielInput.addEventListener('input', debounce(async () => {
  const q = zielInput.value.trim();
  if (q.length < 3) { showSuggestions(zielSug, [], ()=>{}); return; }
  const items = await apiAutocomplete(q);
  showSuggestions(zielSug, items, f => {
    zielInput.value = f.properties.label;
    zielInput.dataset.lon = f.geometry.coordinates[0];
    zielInput.dataset.lat = f.geometry.coordinates[1];
  });
}, 250));

// ==============================
// Formular: Route berechnen + speichern
// ==============================
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const startText = startInput.value.trim();
  const zielText = zielInput.value.trim();

  // Koordinaten lesen
  let sLon = parseFloat(startInput.dataset.lon);
  let sLat = parseFloat(startInput.dataset.lat);
  let zLon = parseFloat(zielInput.dataset.lon);
  let zLat = parseFloat(zielInput.dataset.lat);

  // Fallback: Geocode, falls keine Suggestion gewählt
  if (Number.isNaN(sLon) || Number.isNaN(sLat)) {
    const f = await apiGeocodeOne(startText);
    if (f) { sLon = f.geometry.coordinates[0]; sLat = f.geometry.coordinates[1]; }
  }
  if (Number.isNaN(zLon) || Number.isNaN(zLat)) {
    const f = await apiGeocodeOne(zielText);
    if (f) { zLon = f.geometry.coordinates[0]; zLat = f.geometry.coordinates[1]; }
  }

  if ([sLon,sLat,zLon,zLat].some(Number.isNaN)) {
    alert("Bitte gültige Adressen auswählen");
    return;
  }

  // Directions via Backend (Proxy)
  let ors;
  try {
    ors = await apiDirections(sLon, sLat, zLon, zLat);
  } catch (err) {
    alert(err.message || "Routenberechnung fehlgeschlagen");
    return;
  }

  const route = ors.routes && ors.routes[0] ? ors.routes[0] : null;
  if (!route) {
    alert("Keine Route gefunden. Bitte andere Adressen versuchen.");
    return;
  }

  // Zeichnen
  if (route.geometry) {
    await drawEncodedRoute(route.geometry); // encoded string
  }

  // Top-10 lokal hochzählen
  addTopSearch(`${startText} → ${zielText}`);

  // In Backend speichern
  const dist = route.summary?.distance ?? null;
  const dur = route.summary?.duration ?? null;

  const payload = {
    start_text: startText,
    end_text: zielText,
    start_coordinates: { longitude: sLon, latitude: sLat },
    end_coordinates: { longitude: zLon, latitude: zLat },
    distance_meters: dist,
    duration_seconds: dur,
    geometry_encoded: route.geometry || null,
    profile: "driving-car"
  };

  const saved = await saveRouteToBackend(payload);
  if (saved) refreshSavedRoutes();
});

// ==============================
// Init
// ==============================
renderTopSearches();
refreshSavedRoutes();
