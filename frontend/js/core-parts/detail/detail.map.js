(function () {
  "use strict";

  // Liefert ein DOM-Element per ID.
  function $(id) {
    return document.getElementById(id);
  }

  var LATAM_BOUNDS = (window.MapCommon && window.MapCommon.LATAM_BOUNDS)
    || { west: -160, south: -58, east: -32, north: 34 };
  var detailGoogleMap = null;
  var detailGoogleMarker = null;
  var googleMapsLoadPromise = null;
  var detailCurrentView = "normal";
  var detailElevationTileType = null;
  var detailClimateDataLayer = null;
  var detailVegetationDataLayer = null;
  var detailActiveClimateLegendColor = null;
  var detailActiveVegetationLegendColor = null;
  var ELEVATION_VIEW_MAX_ZOOM = 10;

  // ===== Legend helpers =====

  function normalizeLegendColor(value) {
    var fn = window.MapCommon && window.MapCommon.normalizeLegendColor;
    if (typeof fn === "function") return fn(value);
    return String(value || "").trim().toLowerCase();
  }

  // Liest die Farbe eines Legendeneintrags robust aus Inline- oder computed-Style.
  function detailLegendItemColor(li) {
    var swatch = li && li.querySelector ? li.querySelector(".legend-swatch") : null;
    if (!swatch) return "";
    var inlineStyle = swatch.getAttribute("style") || "";
    var match = inlineStyle.match(/background\s*:\s*([^;]+)/i);
    if (match && match[1]) return normalizeLegendColor(match[1]);
    return normalizeLegendColor(swatch.style.backgroundColor || "");
  }

  // Markiert den aktiven Legendeneintrag fuer eine einzelne aktive Farbe.
  function setDetailLegendActiveState(legendId, activeColor) {
    var root = $(legendId);
    if (!root) return;
    root.querySelectorAll("li").forEach(function (li) {
      var isActive = Boolean(activeColor) && detailLegendItemColor(li) === activeColor;
      li.classList.toggle("is-active", isActive);
    });
  }

  // Filtert die Klima-Polygone nach aktivem Legendeneintrag.
  function applyDetailClimateLegendFilter() {
    if (!detailClimateDataLayer) return;
    detailClimateDataLayer.setStyle(function (feat) {
      var featureColor = normalizeLegendColor(feat.getProperty("color"));
      var visible = !detailActiveClimateLegendColor || featureColor === detailActiveClimateLegendColor;
      return {
        fillColor: feat.getProperty("color"), fillOpacity: visible ? 0.72 : 0,
        strokeWeight: 0, visible: visible, clickable: false,
      };
    });
    setDetailLegendActiveState("detailClimateLegend", detailActiveClimateLegendColor);
  }

  // Filtert die Vegetations-Polygone nach aktivem Legendeneintrag.
  function applyDetailVegetationLegendFilter() {
    if (!detailVegetationDataLayer) return;
    detailVegetationDataLayer.setStyle(function (feat) {
      var featureColor = normalizeLegendColor(feat.getProperty("color"));
      var visible = !detailActiveVegetationLegendColor || featureColor === detailActiveVegetationLegendColor;
      return {
        fillColor: feat.getProperty("color"), fillOpacity: visible ? 0.72 : 0,
        strokeWeight: 0, visible: visible, clickable: false,
      };
    });
    setDetailLegendActiveState("detailVegetationLegend", detailActiveVegetationLegendColor);
  }

  // Platzhalter: Detail-Legenden sind derzeit nur informativ und nicht klickbar.
  function initDetailLegendFilters() {
    // Detail legends are informational only (no click filtering).
  }

  // ===== Google maps script and layer switching =====

  function loadGoogleMapsScriptForDetail() {
    var common = window.MapCommon;
    if (common && typeof common.loadGoogleMapsScript === "function") {
      return common.loadGoogleMapsScript({
        key: window.GMAPS_KEY, callbackName: "initDetailMap",
      });
    }

    if (window.google && window.google.maps) return Promise.resolve(true);
    if (!window.GMAPS_KEY || window.GMAPS_KEY === "DEIN_API_KEY_HIER") return Promise.resolve(false);
    if (googleMapsLoadPromise) return googleMapsLoadPromise;

    googleMapsLoadPromise = new Promise(function (resolve) {
      window.initDetailMap = function () {
        resolve(true);
      };

      var script = document.createElement("script");
      script.src = "https://maps.googleapis.com/maps/api/js?key=" + window.GMAPS_KEY + "&callback=initDetailMap&loading=async";
      script.async = true;
      script.defer = true;
      script.onerror = function () {
        resolve(false);
      };
      document.head.appendChild(script);
    });

    return googleMapsLoadPromise;
  }

  // Blendet alle thematischen Detail-Legenden aus.
  function hideDetailMapLegends() {
    var ids = ["detailElevationLegend", "detailClimateLegend", "detailVegetationLegend"];
    ids.forEach(function (id) {
      var el = $(id);
      if (el) el.classList.add("is-hidden");
    });
  }

  // Synchronisiert den aktiven Zustand der Detail-View-Toggle-Buttons.
  function updateDetailMapToggleUI() {
    var buttons = document.querySelectorAll("#detailMapViewToggle .toggle-btn");
    buttons.forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.view === detailCurrentView);
    });
  }

  // Entfernt aktive Overlay-Layer und setzt die Detail-Karte auf Basisansicht.
  function hideAllDetailThemeLayers() {
    if (!detailGoogleMap) return;
    if (detailGoogleMap.overlayMapTypes.getLength() > 0) {
      detailGoogleMap.overlayMapTypes.clear();
    }
    detailGoogleMap.setOptions({ maxZoom: null });
    if (detailClimateDataLayer) detailClimateDataLayer.setMap(null);
    if (detailVegetationDataLayer) detailVegetationDataLayer.setMap(null);
    hideDetailMapLegends();
  }

  // Blendet genau die Legende der aktiven Kartenansicht ein.
  function showDetailMapLegend(legendId) {
    var legend = $(legendId);
    if (legend) legend.classList.remove("is-hidden");
  }

  // Stellt den Hoehen-Overlay-Tilelayer bereit.
  function ensureDetailElevationTileType() {
    if (detailElevationTileType) return detailElevationTileType;
    detailElevationTileType = new window.google.maps.ImageMapType({
      getTileUrl: function (coord, zoom) {
        return "https://tile.opentopomap.org/" + zoom + "/" + coord.x + "/" + coord.y + ".png";
      },
      tileSize: new window.google.maps.Size(256, 256),
      opacity: 0.85,
      name: "Topographie",
      maxZoom: 17,
    });
    return detailElevationTileType;
  }

  // Laedt den Klima-Datensatz einmalig und initialisiert den Layer.
  async function ensureDetailClimateDataLayer() {
    if (detailClimateDataLayer) return detailClimateDataLayer;
    var climate = await fetch("/assets/koppen-latam.geojson").then(function (r) { return r.json(); });
    detailClimateDataLayer = new window.google.maps.Data();
    detailClimateDataLayer.addGeoJson(climate);
    applyDetailClimateLegendFilter();
    return detailClimateDataLayer;
  }

  // Laedt den Vegetations-Datensatz einmalig und initialisiert den Layer.
  async function ensureDetailVegetationDataLayer() {
    if (detailVegetationDataLayer) return detailVegetationDataLayer;
    var vegetation = await fetch("/assets/ecoregions-latam.geojson").then(function (r) { return r.json(); });
    detailVegetationDataLayer = new window.google.maps.Data();
    detailVegetationDataLayer.addGeoJson(vegetation);
    applyDetailVegetationLegendFilter();
    return detailVegetationDataLayer;
  }

  // Aktiviert die Hoehenansicht auf der Detailkarte.
  function activateDetailElevationView() {
    detailGoogleMap.overlayMapTypes.push(ensureDetailElevationTileType());
    detailGoogleMap.setOptions({ maxZoom: ELEVATION_VIEW_MAX_ZOOM });
    if (detailGoogleMap.getZoom() > ELEVATION_VIEW_MAX_ZOOM) {
      detailGoogleMap.setZoom(ELEVATION_VIEW_MAX_ZOOM);
    }
    showDetailMapLegend("detailElevationLegend");
  }

  // Aktiviert die Klimaansicht auf der Detailkarte.
  async function activateDetailClimateView() {
    var layer = await ensureDetailClimateDataLayer();
    applyDetailClimateLegendFilter();
    layer.setMap(detailGoogleMap);
    showDetailMapLegend("detailClimateLegend");
  }

  // Aktiviert die Vegetationsansicht auf der Detailkarte.
  async function activateDetailVegetationView() {
    var layer = await ensureDetailVegetationDataLayer();
    applyDetailVegetationLegendFilter();
    layer.setMap(detailGoogleMap);
    showDetailMapLegend("detailVegetationLegend");
  }

  // Schaltet die Detail-Karte zwischen Normal-, Hoehen-, Klima- und Vegetationsansicht um.
  async function setDetailMapView(view) {
    detailCurrentView = view;
    updateDetailMapToggleUI();
    if (!detailGoogleMap || !window.google || !window.google.maps) return;

    hideAllDetailThemeLayers();

    if (view === "elevation") {
      activateDetailElevationView();
      return;
    }

    if (view === "climate") {
      await activateDetailClimateView();
      return;
    }

    if (view === "vegetation") {
      await activateDetailVegetationView();
    }
  }

  // Registriert Klick-Handler fuer die Detail-Ansichtsumschaltung.
  function initDetailMapToggle() {
    var toggle = $("detailMapViewToggle");
    if (!toggle) return;
    toggle.addEventListener("click", function (event) {
      var btn = event.target && event.target.closest ? event.target.closest(".toggle-btn") : null;
      if (!btn || !btn.dataset.view) return;
      setDetailMapView(btn.dataset.view);
    });
    updateDetailMapToggleUI();
  }

  // ===== Coordinate and map rendering =====

  function parseCoordinates(coords) {
    if (!Array.isArray(coords) || coords.length < 2) return null;
    var lon = Number(coords[0]);
    var lat = Number(coords[1]);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    return { lat: lat, lon: lon };
  }

  // Setzt den Fallback-Zustand bei ungueltigen Koordinaten.
  function showMissingCoordinatesState(mapWrap, mapLink, mapHint) {
    mapWrap.classList.add("is-hidden");
    mapLink.classList.add("is-hidden");
    mapHint.textContent = "Fuer diesen Datensatz sind keine gueltigen Koordinaten verfuegbar.";
  }

  // Setzt den Fallback-Zustand, wenn Google Maps nicht verfuegbar ist.
  function showUnavailableMapState(mapWrap, mapHint) {
    mapWrap.classList.add("is-hidden");
    mapHint.textContent = "Karte konnte nicht geladen werden (Google Maps nicht verfuegbar).";
  }

  // Aktualisiert den externen Kartenlink mit den aktuellen Koordinaten.
  function updateExternalMapLink(mapLink, coord) {
    mapLink.href = "https://www.google.com/maps?q=" + coord.lat + "," + coord.lon;
    mapLink.classList.remove("is-hidden");
  }

  // Erstellt die Google Map oder zentriert eine bestehende Instanz neu.
  function ensureDetailGoogleMap(mapFrame, center) {
    if (!detailGoogleMap) {
      detailGoogleMap = new window.google.maps.Map(mapFrame, {
        center: center, zoom: 13, mapTypeId: window.google.maps.MapTypeId.ROADMAP,
        restriction: {
          latLngBounds: {
            north: LATAM_BOUNDS.north, south: LATAM_BOUNDS.south,
            west: LATAM_BOUNDS.west, east: LATAM_BOUNDS.east,
          },
          strictBounds: false,
        },
      });
      return;
    }
    detailGoogleMap.setCenter(center);
    detailGoogleMap.setZoom(13);
  }

  // Setzt den roten Fundortmarker auf die aktuelle Kartenposition.
  function renderDetailMarker(center, detail) {
    if (detailGoogleMarker) detailGoogleMarker.setMap(null);
    detailGoogleMarker = new window.google.maps.Marker({
      position: center, map: detailGoogleMap,
      title: detail && detail.name ? detail.name : "Fundort",
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE, scale: 7, fillColor: "#ff2b2b",
        fillOpacity: 0.9, strokeColor: "#ffd1d1", strokeWeight: 1.5,
      },
    });
  }

  // Zeigt den Koordinatenhinweis fuer die aktuelle Detailposition an.
  function setCoordinateHint(mapHint, coord) {
    mapHint.textContent = "Koordinaten: " + coord.lat.toFixed(6) + ", " + coord.lon.toFixed(6);
  }

  // Rendert die Fundortkarte auf der Detailseite inklusive Marker und Fallback-Verhalten.
  async function renderLocationMap(detail) {
    var mapWrap = $("detailMapWrap");
    var mapFrame = $("detailMapFrame");
    var mapHint = $("detailMapHint");
    var mapLink = $("detailMapLink");
    if (!mapWrap || !mapFrame || !mapHint || !mapLink) return;

    var coord = parseCoordinates(detail && detail.coordinates);
    if (!coord) {
      showMissingCoordinatesState(mapWrap, mapLink, mapHint);
      return;
    }

    updateExternalMapLink(mapLink, coord);

    var mapsReady = await loadGoogleMapsScriptForDetail();
    if (!mapsReady || !window.google || !window.google.maps) {
      showUnavailableMapState(mapWrap, mapHint);
      return;
    }

    var center = { lat: coord.lat, lng: coord.lon };

    ensureDetailGoogleMap(mapFrame, center);
    renderDetailMarker(center, detail);

    await setDetailMapView(detailCurrentView);

    setCoordinateHint(mapHint, coord);
    mapWrap.classList.remove("is-hidden");
  }

  window.DetailMapPage = {
    initDetailLegendFilters: initDetailLegendFilters, initDetailMapToggle: initDetailMapToggle,
    renderLocationMap: renderLocationMap, setDetailMapView: setDetailMapView,
  };
})();
