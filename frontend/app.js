// Demo-Daten kommen aus frontend/data/demo-beetles.js (window.DEMO_BEETLES).
// loadBeetles() wechselt automatisch auf Backend, wenn window.API_BASE_URL gesetzt ist.
let beetles = [];

async function loadBeetles() {
  try {
    if (window.API_BASE_URL) {
      const res = await fetch(`${window.API_BASE_URL}/api/beetles`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      beetles = await res.json();
    } else {
      // Mock-Modus: Demo-Daten aus demo-beetles.js
      beetles = window.DEMO_BEETLES ?? [];
    }
  } catch (error) {
    console.error("Kaeferdaten konnten nicht geladen werden:", error);
    beetles = window.DEMO_BEETLES ?? [];
  }
}

const labelPositions = {
  Argentina: [-38, -64],
  Belize: [17.2, -88.7],
  Bolivia: [-17, -64],
  Brazil: [-10, -53],
  Chile: [-30, -71],
  Colombia: [4.5, -73],
  "Costa Rica": [9.8, -84.1],
  Cuba: [21.8, -79],
  "Dominican Republic": [19, -70.2],
  Ecuador: [-1.6, -78.4],
  "El Salvador": [13.8, -88.9],
  "French Guiana": [4.1, -53.1],
  Guatemala: [15.5, -90.3],
  Guyana: [5, -58.9],
  Haiti: [19, -72.4],
  Honduras: [14.8, -86.6],
  Jamaica: [18.1, -77.3],
  Mexico: [23, -102],
  Nicaragua: [12.8, -85],
  Panama: [8.6, -80.1],
  Paraguay: [-23.4, -58.4],
  Peru: [-9.5, -75],
  "Puerto Rico": [18.2, -66.5],
  Suriname: [4.1, -55.9],
  Uruguay: [-32.8, -56],
  Venezuela: [7, -66]
};

const tinyLabels = new Set([
  "Belize",
  "Costa Rica",
  "Dominican Republic",
  "El Salvador",
  "French Guiana",
  "Guyana",
  "Haiti",
  "Jamaica",
  "Panama",
  "Puerto Rico",
  "Suriname",
  "Uruguay"
]);

let selectedId = null;
let geoBounds;
let zoom = 1;
let panX = 0;
let panY = 0;
let dragStart = null;

const searchInput = document.querySelector("#searchInput");
const climateFilter = document.querySelector("#climateFilter");
const vegetationFilter = document.querySelector("#vegetationFilter");
const elevationFilter = document.querySelector("#elevationFilter");
const resetButton = document.querySelector("#resetButton");
const resultHeading = document.querySelector("#resultHeading");
const resultList = document.querySelector("#resultList");
const detailContent = document.querySelector("#detailContent");
const atlasSvg = document.querySelector("#atlasSvg");
const mapViewport = document.querySelector("#mapViewport");
const baseLayer = document.querySelector("#baseLayer");
const countryLineLayer = document.querySelector("#countryLineLayer");
const labelLayer = document.querySelector("#labelLayer");
const beetleLayer = document.querySelector("#beetleLayer");
const pointPopup = document.querySelector("#pointPopup");
const countrySidebar = document.querySelector("#countrySidebar");
const countrySidebarTitle = document.querySelector("#countrySidebarTitle");
const countrySidebarContent = document.querySelector("#countrySidebarContent");
const closeSidebarButton = document.querySelector("#closeSidebarButton");
const zoomInButton = document.querySelector("#zoomInButton");
const zoomOutButton = document.querySelector("#zoomOutButton");
const resetMapButton = document.querySelector("#resetMapButton");

function getElevationGroup(elevation) {
  if (elevation < 500) return "low";
  if (elevation < 1500) return "mid";
  if (elevation < 3000) return "high";
  return "veryHigh";
}

function getFilteredBeetles() {
  const search = searchInput.value.trim().toLowerCase();
  const climate = climateFilter.value;
  const vegetation = vegetationFilter.value;
  const elevation = elevationFilter.value;

  return beetles.filter((beetle) => {
    const matchesSearch =
      beetle.name.toLowerCase().includes(search) ||
      beetle.family.toLowerCase().includes(search) ||
      beetle.location.toLowerCase().includes(search);
    const matchesClimate = climate === "all" || beetle.climate === climate;
    const matchesVegetation = vegetation === "all" || beetle.vegetation === vegetation;
    const matchesElevation = elevation === "all" || getElevationGroup(beetle.elevation) === elevation;

    return matchesSearch && matchesClimate && matchesVegetation && matchesElevation;
  });
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function mercatorY(lat) {
  const radians = (Math.max(-85, Math.min(85, lat)) * Math.PI) / 180;
  return Math.log(Math.tan(Math.PI / 4 + radians / 2));
}

function project([lon, lat]) {
  const padding = 40;
  const width = 1000 - padding * 2;
  const height = 980 - padding * 2;
  const x = padding + ((lon - geoBounds.minLon) / (geoBounds.maxLon - geoBounds.minLon)) * width;
  const maxY = mercatorY(geoBounds.maxLat);
  const minY = mercatorY(geoBounds.minLat);
  const y = padding + ((maxY - mercatorY(lat)) / (maxY - minY)) * height;
  return [x, y];
}

function pathFromRing(ring) {
  return ring
    .map((coordinate, index) => {
      const [x, y] = project(coordinate);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ") + " Z";
}

function pathFromGeometry(geometry) {
  if (geometry.type === "Polygon") {
    return geometry.coordinates.map(pathFromRing).join(" ");
  }

  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates
      .map((polygon) => polygon.map(pathFromRing).join(" "))
      .join(" ");
  }

  return "";
}

function collectCoordinates(geometry, output = []) {
  if (geometry.type === "Polygon") {
    geometry.coordinates.flat().forEach((coordinate) => output.push(coordinate));
  }

  if (geometry.type === "MultiPolygon") {
    geometry.coordinates.flat(2).forEach((coordinate) => output.push(coordinate));
  }

  return output;
}

function calculateBounds(features) {
  const coordinates = features.flatMap((feature) => collectCoordinates(feature.geometry));
  const lons = coordinates.map(([lon]) => lon);
  const lats = coordinates.map(([, lat]) => lat);

  return {
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats)
  };
}

function renderAtlasMap(featureCollection) {
  geoBounds = calculateBounds(featureCollection.features);
  baseLayer.innerHTML = "";
  countryLineLayer.innerHTML = "";
  labelLayer.innerHTML = "";
  beetleLayer.innerHTML = "";

  featureCollection.features.forEach((feature) => {
    const pathData = pathFromGeometry(feature.geometry);
    const name = feature.properties.name;

    baseLayer.appendChild(svgElement("path", {
      class: "country",
      d: pathData
    }));

    countryLineLayer.appendChild(svgElement("path", {
      class: "country-line",
      d: pathData
    }));

    const labelCoordinate = labelPositions[name];
    if (!labelCoordinate) return;

    const [x, y] = project([labelCoordinate[1], labelCoordinate[0]]);
    const label = svgElement("text", {
      class: tinyLabels.has(name) ? "country-label tiny-label" : "country-label",
      x,
      y,
      "data-country": name,
      tabindex: 0
    });
    label.textContent = name;
    labelLayer.appendChild(label);
  });
}

function renderBeetlePoints() {
  if (!geoBounds) return;

  beetleLayer.innerHTML = "";

  getFilteredBeetles().forEach((beetle) => {
    const [x, y] = project(beetle.coordinates);
    const point = svgElement("circle", {
      class: "beetle-point",
      cx: x,
      cy: y,
      r: 2.5,
      "data-id": beetle.id
    });
    beetleLayer.appendChild(point);
  });
}

function updateMapTransform() {
  mapViewport.setAttribute("transform", `translate(${panX} ${panY}) scale(${zoom})`);
}

function setZoom(nextZoom, centerX = 500, centerY = 490) {
  const oldZoom = zoom;
  zoom = Math.min(5, Math.max(1, nextZoom));
  panX = centerX - ((centerX - panX) / oldZoom) * zoom;
  panY = centerY - ((centerY - panY) / oldZoom) * zoom;
  updateMapTransform();
}

function resetMapView() {
  zoom = 1;
  panX = 0;
  panY = 0;
  updateMapTransform();
}

function render() {
  const filteredBeetles = getFilteredBeetles();

  if (!filteredBeetles.some((beetle) => beetle.id === selectedId)) {
    selectedId = filteredBeetles[0]?.id ?? null;
  }

  resultHeading.textContent = `${filteredBeetles.length} gefundene Arten`;

  if (filteredBeetles.length === 0) {
    resultList.innerHTML = `
      <div class="empty-state">Keine passenden Arten gefunden.</div>
    `;
    detailContent.innerHTML = `
      <div class="empty-state">Keine Detaildaten vorhanden.</div>
    `;
    renderMapPoints();
    return;
  }

  resultList.innerHTML = filteredBeetles
    .map(
      (beetle) => `
        <button class="species-card ${beetle.id === selectedId ? "is-active" : ""}" data-id="${beetle.id}" type="button">
          <h3>${beetle.name}</h3>
          <p>${beetle.family} - ${beetle.location}</p>
          <div class="meta-row">
            <span class="tag">${beetle.climate}</span>
            <span class="tag">${beetle.vegetation}</span>
            <span class="tag">${beetle.elevation} m</span>
          </div>
        </button>
      `
    )
    .join("");

  renderDetails(beetles.find((beetle) => beetle.id === selectedId));
  renderMapPoints();
}

function renderMapPoints() {
  if (googleMapInstance) {
    renderGoogleMapMarkers();
  } else {
    renderBeetlePoints();
  }
}

function renderDetails(beetle) {
  detailContent.innerHTML = `
    <h2>${beetle.name}</h2>
    <p>${beetle.family}</p>
    <ul class="detail-list">
      <li><strong>Fundort</strong>${beetle.location}</li>
      <li><strong>Klimazone</strong>${beetle.climate}</li>
      <li><strong>Vegetation</strong>${beetle.vegetation}</li>
      <li><strong>Hoehenlage</strong>${beetle.elevation} m</li>
      <li><strong>Temperatur</strong>${beetle.temperature} C</li>
      <li><strong>Boden</strong>${beetle.soil}</li>
    </ul>
  `;
}

function openCountrySidebar(countryName) {
  countrySidebarTitle.textContent = countryName;
  countrySidebarContent.innerHTML = `
    <p>Noch keine Informationen eingetragen.</p>
  `;
  countrySidebar.classList.add("is-open");
  countrySidebar.setAttribute("aria-hidden", "false");
}

function closeCountrySidebar() {
  countrySidebar.classList.remove("is-open");
  countrySidebar.setAttribute("aria-hidden", "true");
}

function openPointPopup(beetle, event) {
  pointPopup.innerHTML = `
    <h3>${beetle.name}</h3>
    <p>Hoehe: noch nicht eingetragen</p>
    <p>Vegetation: noch nicht eingetragen</p>
    <p>Klimazone: noch nicht eingetragen</p>
  `;

  const canvas = event.currentTarget.closest(".map-canvas");
  const canvasRect = canvas.getBoundingClientRect();
  const left = Math.min(event.clientX - canvasRect.left + 12, canvasRect.width - 210);
  const top = Math.min(event.clientY - canvasRect.top + 12, canvasRect.height - 150);

  pointPopup.style.left = `${Math.max(12, left)}px`;
  pointPopup.style.top = `${Math.max(12, top)}px`;
  pointPopup.classList.remove("is-hidden");
}

function closePointPopup() {
  pointPopup.classList.add("is-hidden");
}

resultList.addEventListener("click", (event) => {
  const card = event.target.closest(".species-card");
  if (!card) return;

  selectedId = Number(card.dataset.id);
  render();
});

labelLayer.addEventListener("click", (event) => {
  const label = event.target.closest(".country-label");
  if (!label) return;

  closePointPopup();
  openCountrySidebar(label.dataset.country);
});

labelLayer.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;

  const label = event.target.closest(".country-label");
  if (!label) return;

  event.preventDefault();
  closePointPopup();
  openCountrySidebar(label.dataset.country);
});

beetleLayer.addEventListener("click", (event) => {
  const point = event.target.closest(".beetle-point");
  if (!point) return;

  const beetle = beetles.find((item) => item.id === Number(point.dataset.id));
  if (!beetle) return;

  closeCountrySidebar();
  openPointPopup(beetle, event);
});

closeSidebarButton.addEventListener("click", closeCountrySidebar);

[searchInput, climateFilter, vegetationFilter, elevationFilter].forEach((element) => {
  element.addEventListener("input", render);
});

zoomInButton.addEventListener("click", () => setZoom(zoom * 1.25));
zoomOutButton.addEventListener("click", () => setZoom(zoom / 1.25));
resetMapButton.addEventListener("click", resetMapView);

atlasSvg.addEventListener("wheel", (event) => {
  event.preventDefault();
  const rect = atlasSvg.getBoundingClientRect();
  const centerX = ((event.clientX - rect.left) / rect.width) * 1000;
  const centerY = ((event.clientY - rect.top) / rect.height) * 980;
  setZoom(event.deltaY < 0 ? zoom * 1.12 : zoom / 1.12, centerX, centerY);
});

atlasSvg.addEventListener("pointerdown", (event) => {
  if (event.target.closest(".country-label") || event.target.closest(".beetle-point")) return;

  closePointPopup();
  atlasSvg.setPointerCapture(event.pointerId);
  atlasSvg.classList.add("is-dragging");
  dragStart = { x: event.clientX, y: event.clientY, panX, panY };
});

atlasSvg.addEventListener("pointermove", (event) => {
  if (!dragStart) return;
  panX = dragStart.panX + event.clientX - dragStart.x;
  panY = dragStart.panY + event.clientY - dragStart.y;
  updateMapTransform();
});

atlasSvg.addEventListener("pointerup", () => {
  dragStart = null;
  atlasSvg.classList.remove("is-dragging");
});

atlasSvg.addEventListener("pointerleave", () => {
  dragStart = null;
  atlasSvg.classList.remove("is-dragging");
});

resetButton.addEventListener("click", () => {
  searchInput.value = "";
  climateFilter.value = "all";
  vegetationFilter.value = "all";
  elevationFilter.value = "all";
  selectedId = beetles[0]?.id ?? null;
  render();
});

// ─── Kartenansichten ──────────────────────────────────────────────────────────

let currentView = "normal";

// Layer-Instanzen (einmalig erstellt, dann nur ein-/ausgeblendet)
let elevationTileType = null;
let climateDataLayer = null;
let vegetationDataLayer = null;

function hideAllThemeLayers() {
  if (googleMapInstance.overlayMapTypes.getLength() > 0) {
    googleMapInstance.overlayMapTypes.clear();
  }
  climateDataLayer?.setMap(null);
  vegetationDataLayer?.setMap(null);
  document.querySelectorAll(".map-legend").forEach((el) => el.classList.add("is-hidden"));
}

async function setMapView(view) {
  document.querySelectorAll(".toggle-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === view);
  });

  if (!googleMapInstance) { currentView = view; return; }

  hideAllThemeLayers();
  currentView = view;

  if (view === "elevation") {
    if (!elevationTileType) {
      elevationTileType = new google.maps.ImageMapType({
        getTileUrl: (coord, zoom) =>
          `https://tile.opentopomap.org/${zoom}/${coord.x}/${coord.y}.png`,
        tileSize: new google.maps.Size(256, 256),
        opacity: 0.85,
        name: "Topographie",
        maxZoom: 17,
      });
    }
    googleMapInstance.overlayMapTypes.push(elevationTileType);
    document.getElementById("elevationLegend")?.classList.remove("is-hidden");
    return;
  }

  if (view === "climate") {
    if (!climateDataLayer) {
      const data = await fetch("assets/koppen-latam.geojson").then((r) => r.json());
      climateDataLayer = new google.maps.Data();
      climateDataLayer.addGeoJson(data);
      climateDataLayer.setStyle((feat) => ({
        fillColor: feat.getProperty("color"),
        fillOpacity: 0.72,
        strokeWeight: 0,
        clickable: false,
      }));
    }
    climateDataLayer.setMap(googleMapInstance);
    document.getElementById("climateLegend")?.classList.remove("is-hidden");
    return;
  }

  if (view === "vegetation") {
    if (!vegetationDataLayer) {
      const data = await fetch("assets/ecoregions-latam.geojson").then((r) => r.json());
      vegetationDataLayer = new google.maps.Data();
      vegetationDataLayer.addGeoJson(data);
      vegetationDataLayer.setStyle((feat) => ({
        fillColor: feat.getProperty("color"),
        fillOpacity: 0.72,
        strokeWeight: 0,
        clickable: false,
      }));
    }
    vegetationDataLayer.setMap(googleMapInstance);
    document.getElementById("vegetationLegend")?.classList.remove("is-hidden");
    return;
  }
}

// ─── Google Maps ──────────────────────────────────────────────────────────────

let googleMapInstance = null;
let activeMarkers = [];
let activeInfoWindow = null;

const mapLoadingState = document.querySelector("#mapLoadingState");
const mapErrorState = document.querySelector("#mapErrorState");
const googleMapEl = document.querySelector("#googleMap");

function showMapError() {
  mapLoadingState.classList.add("is-hidden");
  mapErrorState.classList.remove("is-hidden");
}

// Globaler Callback fuer Google Maps
window.initMap = function () {
  mapLoadingState.classList.add("is-hidden");

  googleMapInstance = new google.maps.Map(googleMapEl, {
    center: { lat: -15, lng: -60 },
    zoom: 4,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    restriction: {
      latLngBounds: { north: 35, south: -60, west: -120, east: -30 },
      strictBounds: false
    }
  });

  activeInfoWindow = new google.maps.InfoWindow();

  // Ländergrenzen als klickbarer GeoJSON-Layer
  initGeoJsonLayer();

  renderGoogleMapMarkers();
};

// Wird von Google Maps aufgerufen, wenn der Key ungueltig ist
window.gm_authFailure = function () {
  showMapError();
};

function initGeoJsonLayer() {
  if (!googleMapInstance || !window.LATIN_AMERICA_COUNTRIES) return;

  googleMapInstance.data.addGeoJson(window.LATIN_AMERICA_COUNTRIES);

  googleMapInstance.data.setStyle({
    fillColor: "#f7f4e8",
    fillOpacity: 0.25,
    strokeColor: "#35463f",
    strokeWeight: 0.9
  });

  // Hover-Effekt
  googleMapInstance.data.addListener("mouseover", (event) => {
    googleMapInstance.data.overrideStyle(event.feature, {
      fillOpacity: 0.5,
      strokeColor: "#2f6b47",
      strokeWeight: 1.5
    });
  });

  googleMapInstance.data.addListener("mouseout", (event) => {
    googleMapInstance.data.revertStyle(event.feature);
  });

  // Klick auf Land öffnet Sidebar
  googleMapInstance.data.addListener("click", (event) => {
    const name = event.feature.getProperty("name");
    if (!name) return;
    activeInfoWindow.close();
    openCountrySidebar(name);
  });
}

function renderGoogleMapMarkers() {
  if (!googleMapInstance) return;

  // Alte Marker entfernen
  activeMarkers.forEach((marker) => marker.setMap(null));
  activeMarkers = [];

  getFilteredBeetles().forEach((beetle) => {
    const marker = new google.maps.Marker({
      position: { lat: beetle.coordinates[1], lng: beetle.coordinates[0] },
      map: googleMapInstance,
      title: beetle.name,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 7,
        fillColor: "#ff2b2b",
        fillOpacity: 0.9,
        strokeColor: "#ffd1d1",
        strokeWeight: 1.5
      }
    });

    marker.addListener("click", () => {
      closeCountrySidebar();
      activeInfoWindow.setContent(`
        <div style="font-family:Arial,sans-serif;font-size:0.88rem;min-width:160px">
          <strong style="font-size:1rem">${beetle.name}</strong><br>
          <span style="color:#66736b">${beetle.family}</span>
          <hr style="margin:0.5rem 0;border:none;border-top:1px solid #d9ded8">
          <div><strong>Fundort:</strong> ${beetle.location}</div>
          <div><strong>Höhe:</strong> ${beetle.elevation} m</div>
          <div><strong>Klima:</strong> ${beetle.climate}</div>
          <div><strong>Vegetation:</strong> ${beetle.vegetation}</div>
        </div>
      `);
      activeInfoWindow.open(googleMapInstance, marker);
    });

    activeMarkers.push(marker);
  });
}

// Google Maps Script dynamisch laden
function loadGoogleMapsScript() {
  if (!window.GMAPS_KEY || window.GMAPS_KEY === "DEIN_API_KEY_HIER") {
    showMapError();
    return;
  }

  const script = document.createElement("script");
  script.src = `https://maps.googleapis.com/maps/api/js?key=${window.GMAPS_KEY}&callback=initMap&loading=async`;
  script.async = true;
  script.defer = true;
  script.onerror = showMapError;
  document.head.appendChild(script);
}

loadGoogleMapsScript();

// Toggle-Buttons
document.querySelectorAll(".toggle-btn").forEach((btn) => {
  btn.addEventListener("click", () => setMapView(btn.dataset.view));
});

// ─── Initialisierung ──────────────────────────────────────────────────────────

(async () => {
  await loadBeetles();

  // SVG-Fallback (nur aktiv wenn Google Maps nicht laedt)
  if (window.LATIN_AMERICA_COUNTRIES) {
    renderAtlasMap(window.LATIN_AMERICA_COUNTRIES);
    renderBeetlePoints();
    updateMapTransform();
  }

  render();
})();
