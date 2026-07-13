// Karten-Bootstrap: laedt Google Maps dynamisch, initialisiert Karte, GeoJSON-
// Laenderlayer und Marker, mit SVG-Fallback falls Google Maps nicht verfuegbar ist.
const mapLoadingState = document.querySelector("#mapLoadingState");
const mapErrorState = document.querySelector("#mapErrorState");
const googleMapEl = document.querySelector("#googleMap");
const svgFallbackEl = document.querySelector("#svgFallback");
const MAP_BOOTSTRAP_BOUNDS = (window.MapCommon && window.MapCommon.LATAM_BOUNDS)
  || { west: -160, south: -58, east: -32, north: 34 };
let mapBootstrapWatchdogId = null;

// ===== Bootstrap-Hilfsfunktionen =====

// Schaltet auf den SVG-Fallback um, wenn Google Maps nicht verfuegbar ist.
function showMapFallback(reason) {
  if (mapBootstrapWatchdogId) {
    clearTimeout(mapBootstrapWatchdogId);
    mapBootstrapWatchdogId = null;
  }
  mapLoadingState.classList.add("is-hidden");
  mapErrorState.classList.add("is-hidden");
  if (googleMapEl) googleMapEl.style.display = "none";
  if (svgFallbackEl) svgFallbackEl.style.display = "block";
  if (atlasSvg) atlasSvg.style.display = "block";
  if (reason) console.warn(reason);
}

// Zeigt einen expliziten Fehlerzustand fuer die Karteninitialisierung.
function showMapError() {
  mapLoadingState.classList.add("is-hidden");
  mapErrorState.classList.remove("is-hidden");
}

// Schaltet die DOM-Ansicht auf die aktive Google-Map um.
function showGoogleMapUi() {
  if (mapBootstrapWatchdogId) {
    clearTimeout(mapBootstrapWatchdogId);
    mapBootstrapWatchdogId = null;
  }
  mapLoadingState.classList.add("is-hidden");
  if (googleMapEl) googleMapEl.style.display = "block";
  if (svgFallbackEl) svgFallbackEl.style.display = "none";
}

// Falls der Google-Loader haengt, erzwingen wir den SVG-Fallback nach kurzer Zeit.
function startMapBootstrapWatchdog() {
  if (mapBootstrapWatchdogId) clearTimeout(mapBootstrapWatchdogId);
  mapBootstrapWatchdogId = setTimeout(function () {
    if (mapLoadingState && !mapLoadingState.classList.contains("is-hidden")) {
      showMapFallback("Map bootstrap timeout. Switching to SVG fallback map.");
    }
  }, 12000);
}

// Erzeugt die Google-Map mit LATAM-Bounds und Basisansicht.
function createGoogleMapInstance() {
  googleMapInstance = new google.maps.Map(googleMapEl, {
    center: { lat: -15, lng: -60 },
    zoom: 4,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    restriction: {
      latLngBounds: {
        north: MAP_BOOTSTRAP_BOUNDS.north,
        south: MAP_BOOTSTRAP_BOUNDS.south,
        west: MAP_BOOTSTRAP_BOUNDS.west,
        east: MAP_BOOTSTRAP_BOUNDS.east,
      },
      strictBounds: false
    }
  });
}

// Bindet das Nachladen von Kartenpunkten an den Idle-Event.
function bindMapIdleReload() {
  if (!window.API_BASE_URL) return;
  googleMapInstance.addListener("idle", scheduleMapPoints);
}

// Rendert Marker und stellt eine eventuell aktive Themenansicht wieder her.
function renderInitialMapView() {
  renderMapPoints();
  if (currentView !== "normal") {
    setMapView(currentView);
  }
}

// Globaler Callback fuer Google Maps.
window.initMap = function () {
  showGoogleMapUi();
  createGoogleMapInstance();
  activeInfoWindow = new google.maps.InfoWindow();

  initGeoJsonLayer();
  bindMapIdleReload();
  renderInitialMapView();
};

// ===== Google-Map-Datenlayer und Marker =====

// Wird von Google Maps aufgerufen, wenn der Key ungueltig ist
window.gm_authFailure = function () {
  showMapFallback("Google Maps authentication failed. Using SVG fallback map.");
};

// Bindet die Laender-GeoJSON-Layer inkl. Hover/Klick-Verhalten an Google Maps.
function initGeoJsonLayer() {
  if (!googleMapInstance || !window.LATIN_AMERICA_COUNTRIES) return;

  googleMapInstance.data.addGeoJson(window.LATIN_AMERICA_COUNTRIES);
  if (typeof updateCountryHighlight === "function") {
    updateCountryHighlight();
  }

  bindCountryHoverHandlers();
  bindCountryClickHandler();
}

// Bindet Hover-Effekte fuer den Country-Layer.
function bindCountryHoverHandlers() {
  googleMapInstance.data.addListener("mouseover", (event) => {
    googleMapInstance.data.overrideStyle(event.feature, {
      fillColor:   "#2f6b47",
      fillOpacity: 0.15,
      strokeOpacity: 0,
      strokeWeight: 0
    });
  });

  googleMapInstance.data.addListener("mouseout", (event) => {
    googleMapInstance.data.revertStyle(event.feature);
  });
}

// Oeffnet bei Klick auf ein Land die Country-Sidebar.
function bindCountryClickHandler() {
  googleMapInstance.data.addListener("click", (event) => {
    const name = event.feature.getProperty("name");
    if (!name) return;
    activeInfoWindow.close();
    if (typeof selectCountryFromMap === "function") {
      selectCountryFromMap(name);
    }
    openCountrySidebar(name);
  });
}

// Entfernt alle aktuell sichtbaren Marker von der Google-Map.
function clearGoogleMapMarkers() {
  activeMarkers.forEach((marker) => marker.setMap(null));
  activeMarkers = [];
}

// Erzeugt rohe Markerpunkte aus den gefilterten Kaeferdaten.
function getRawGoogleMapMarkers() {
  return getFilteredBeetles().map((beetle) => ({
    beetle,
    lat: beetle.coordinates[1],
    lng: beetle.coordinates[0],
  }));
}

// Wendet den raeumlichen Subtyp-Filter auf Markerpunkte an, falls aktiv.
function getRenderableGoogleMapMarkers(rawMarkers) {
  return shouldApplySubtypeSpatialFilter()
    ? filterPointsByActiveThemePolygons(rawMarkers)
    : rawMarkers;
}

// Erzeugt einen einzelnen Google-Map-Marker fuer einen Kaeferpunkt.
function createGoogleBeetleMarker(markerPoint) {
  const beetle = markerPoint.beetle;
  const lat = markerPoint.lat;
  const lng = markerPoint.lng;

  const marker = new google.maps.Marker({
    position: { lat, lng },
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

  // Featured/Demo-Marker tragen schon alle Daten -> kein Nachladen noetig.
  marker.addListener("click", () => {
    openBeetleInfoWindow(marker, beetle, false);
  });

  return marker;
}

// Rendert Marker aus den aktuell gefilterten Treffern auf der Google-Karte.
function renderGoogleMapMarkers() {
  if (!googleMapInstance) return;

  clearGoogleMapMarkers();
  const rawMarkers = getRawGoogleMapMarkers();
  const markersToRender = getRenderableGoogleMapMarkers(rawMarkers);
  lastRenderedMapPointCount = markersToRender.length;
  updateResultHeading(getFilteredBeetles().length);

  markersToRender.forEach((markerPoint) => {
    activeMarkers.push(createGoogleBeetleMarker(markerPoint));
  });
}

// Google Maps Script dynamisch laden
async function loadGoogleMapsScript() {
  const loader = window.MapCommon && window.MapCommon.loadGoogleMapsScript;
  if (typeof loader !== "function") {
    showMapFallback("MapCommon loader missing. Using SVG fallback map.");
    return;
  }

  const loaded = await loader({
    key: window.GMAPS_KEY,
    callbackName: "initMap",
  });
  if (!loaded) {
    showMapFallback("Google Maps key missing or script failed. Using SVG fallback map.");
  }
}

// ===== Seiten-Bootstrap =====

// Bindet die View-Toggle-Buttons auf die Kartenansicht.
function bindMapViewToggleButtons() {
  document.querySelectorAll(".map-view-toggle .toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => setMapView(btn.dataset.view));
  });
}

// Initialisiert die Hauptseite nach dem ersten Datenladen.
async function bootstrapMainPage() {
  showLoadingState();

  await loadBeetles();
  restorePinnedBeetleIfNeeded();

  // SVG-Fallback (nur aktiv wenn Google Maps nicht laedt)
  if (window.LATIN_AMERICA_COUNTRIES) {
    renderAtlasMap(window.LATIN_AMERICA_COUNTRIES);
    renderBeetlePoints();
    updateMapTransform();
  }

  render();
  saveMainState();
}

loadGoogleMapsScript();
startMapBootstrapWatchdog();
initLegendFilters();
bindMapViewToggleButtons();
bootstrapMainPage();
