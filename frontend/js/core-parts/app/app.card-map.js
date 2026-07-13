(function () {
  "use strict";

  // ============================================================
  //  Kompakte, GESPERRTE Fundort-Karte fuer die ausgeklappte
  //  Ergebniskarte auf der Hauptseite.
  //    - kein Ziehen / kein Scroll-Zoom (gestureHandling: "none")
  //    - drei thematische Ansichten wie die grossen Karten:
  //        Normal, Hoehe (Topographie), Klima (Koeppen), Vegetation
  //    - in der Hoehen-Ansicht ist der Zoom fest auf die max. Zoomstufe
  //      der Hoehenkarte gesetzt und nicht veraenderbar.
  //  Faellt ohne Google-Maps-Key auf einen einfachen Karten-Embed zurueck.
  // ============================================================

  var LATAM_BOUNDS = (window.MapCommon && window.MapCommon.LATAM_BOUNDS)
    || { west: -160, south: -58, east: -32, north: 34 };
  var ELEVATION_VIEW_MAX_ZOOM = 10; // identisch zur Detailkarte
  var BASE_ZOOM = 8;

  // Modulweiter Cache fuer die GeoJSON-Datensaetze (nur einmal laden).
  var climateGeoPromise = null;
  var vegetationGeoPromise = null;

  function loadGoogleMaps() {
    if (window.MapCommon && typeof window.MapCommon.loadGoogleMapsScript === "function") {
      return window.MapCommon.loadGoogleMapsScript({
        key: window.GMAPS_KEY, callbackName: "initCardMap",
      });
    }
    return Promise.resolve(Boolean(window.google && window.google.maps));
  }

  function getClimateGeo() {
    if (!climateGeoPromise) {
      climateGeoPromise = fetch("/assets/koppen-latam.geojson").then(function (r) { return r.json(); });
    }
    return climateGeoPromise;
  }

  function getVegetationGeo() {
    if (!vegetationGeoPromise) {
      vegetationGeoPromise = fetch("/assets/ecoregions-latam.geojson").then(function (r) { return r.json(); });
    }
    return vegetationGeoPromise;
  }

  // Topographie-Overlay (gleiche Quelle wie die Detailkarte).
  function makeElevationTileType() {
    return new window.google.maps.ImageMapType({
      getTileUrl: function (coord, zoom) {
        return "https://tile.opentopomap.org/" + zoom + "/" + coord.x + "/" + coord.y + ".png";
      },
      tileSize: new window.google.maps.Size(256, 256),
      opacity: 0.85, name: "Topographie", maxZoom: 17,
    });
  }

  // Faerbt eine GeoJSON-Ebene anhand der feature-Eigenschaft "color".
  function styleThemeLayer(dataLayer) {
    dataLayer.setStyle(function (feat) {
      return {
        fillColor: feat.getProperty("color"), fillOpacity: 0.72,
        strokeWeight: 0, clickable: false,
      };
    });
  }

  // Baut die eigentliche Google-Karte inklusive Umschaltung.
  function buildMap(state) {
    var g = window.google.maps;
    var center = { lat: state.lat, lng: state.lng };

    var map = new g.Map(state.frame, {
      center: center,
      zoom: BASE_ZOOM,
      mapTypeId: g.MapTypeId.ROADMAP,
      disableDefaultUI: true,
      zoomControl: false,
      scrollwheel: false,
      draggable: false,
      gestureHandling: "none",
      keyboardShortcuts: false,
      clickableIcons: false,
      restriction: {
        latLngBounds: {
          north: LATAM_BOUNDS.north, south: LATAM_BOUNDS.south,
          west: LATAM_BOUNDS.west, east: LATAM_BOUNDS.east,
        },
        strictBounds: false,
      },
    });
    state.map = map;

    new g.Marker({
      position: center, map: map, title: state.name,
      icon: {
        path: g.SymbolPath.CIRCLE, scale: 7, fillColor: "#ff2b2b",
        fillOpacity: 0.9, strokeColor: "#ffd1d1", strokeWeight: 1.5,
      },
    });

    g.event.addListenerOnce(map, "idle", function () {
      state.frame.classList.add("is-ready");
    });
    setTimeout(function () {
      g.event.trigger(map, "resize");
      map.setCenter(center);
    }, 60);

    // Entfernt alle thematischen Ebenen und setzt Basiszustand.
    function clearThemes() {
      if (map.overlayMapTypes.getLength() > 0) map.overlayMapTypes.clear();
      map.setOptions({ maxZoom: null, minZoom: null });
      if (state.climateLayer) state.climateLayer.setMap(null);
      if (state.vegetationLayer) state.vegetationLayer.setMap(null);
    }

    function setView(view) {
      clearThemes();

      if (view === "elevation") {
        map.overlayMapTypes.push(makeElevationTileType());
        // Zoom fest auf die max. Zoomstufe der Hoehenkarte, nicht veraenderbar.
        map.setOptions({ maxZoom: ELEVATION_VIEW_MAX_ZOOM, minZoom: ELEVATION_VIEW_MAX_ZOOM });
        map.setZoom(ELEVATION_VIEW_MAX_ZOOM);
        map.setCenter(center);
      } else if (view === "climate") {
        getClimateGeo().then(function (geo) {
          if (!state.climateLayer) {
            state.climateLayer = new g.Data();
            state.climateLayer.addGeoJson(geo);
            styleThemeLayer(state.climateLayer);
          }
          if (state.currentView === "climate") state.climateLayer.setMap(map);
        });
      } else if (view === "vegetation") {
        getVegetationGeo().then(function (geo) {
          if (!state.vegetationLayer) {
            state.vegetationLayer = new g.Data();
            state.vegetationLayer.addGeoJson(geo);
            styleThemeLayer(state.vegetationLayer);
          }
          if (state.currentView === "vegetation") state.vegetationLayer.setMap(map);
        });
      } else {
        map.setZoom(BASE_ZOOM);
        map.setCenter(center);
      }

      state.currentView = view;
      updateToolbar(state, view);
      updateLegend(state, view);
    }

    // Toolbar-Klicks verdrahten.
    if (state.toolbar) {
      state.toolbar.addEventListener("click", function (event) {
        var btn = event.target && event.target.closest ? event.target.closest(".mini-map-btn") : null;
        if (!btn || !btn.dataset.view) return;
        setView(btn.dataset.view);
      });
    }

    setView("normal");
  }

  // Markiert den aktiven Toolbar-Button.
  function updateToolbar(state, view) {
    if (!state.toolbar) return;
    state.toolbar.querySelectorAll(".mini-map-btn").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.view === view);
    });
  }

  // Zeigt unter der Karte den konkreten Wert DIESES Kaefers als farbige
  // Ein-Zeilen-Legende (passend zum aktiven Modus). Normal -> keine Legende.
  function updateLegend(state, view) {
    if (!state.legend) return;
    var lookups = window.BEETLE_LEGEND_COLORS;
    var swatch = null;
    if (lookups) {
      if (view === "elevation") {
        swatch = lookups.elevationSwatch(state.elevation);
      } else if (view === "climate") {
        if (state.koppen) {
          swatch = { color: lookups.koppenColor(state.koppen), label: lookups.koppenLabel(state.koppen) };
        } else {
          swatch = lookups.climateSwatch(state.climate);
        }
      } else if (view === "vegetation") {
        if (state.vegzone) {
          swatch = { color: lookups.vegetationZoneColor(state.vegzone), label: state.vegzone };
        } else {
          swatch = lookups.vegetationSwatch(state.vegetation);
        }
      }
    }
    if (!swatch) {
      state.legend.innerHTML = "";
      return;
    }
    state.legend.innerHTML =
      '<span class="mini-legend-swatch" style="background:' + swatch.color + '"></span>' +
      '<span class="mini-legend-label">' + swatch.label + "</span>";
  }

  // Fallback ohne Google-Maps-Key: einfacher Karten-Embed, Toolbar ausblenden.
  function renderFallback(state) {
    if (state.toolbar) state.toolbar.style.display = "none";
    state.frame.innerHTML =
      '<iframe class="mini-map-embed" title="Fundort: ' + state.name +
      '" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=' +
      state.lat + ',' + state.lng + '&z=7&hl=de&output=embed"></iframe>';
  }

  // Initialisiert die Karte fuer einen Container (.detail-mini-map).
  function init(container) {
    if (!container || container.dataset.cardMapInit === "1") return;
    var lat = Number(container.dataset.lat);
    var lng = Number(container.dataset.lng);
    var frame = container.querySelector(".mini-map-frame");
    if (!frame || !Number.isFinite(lat) || !Number.isFinite(lng)) return;
    container.dataset.cardMapInit = "1";

    var state = {
      lat: lat, lng: lng,
      name: container.dataset.name || "Fundort",
      elevation: container.dataset.elevation,
      climate: container.dataset.climate,
      vegetation: container.dataset.vegetation,
      koppen: container.dataset.koppen,
      vegzone: container.dataset.vegzone,
      frame: frame,
      toolbar: container.querySelector(".mini-map-toolbar"),
      legend: container.querySelector(".mini-map-legend"),
      map: null, climateLayer: null, vegetationLayer: null, currentView: "normal",
    };

    loadGoogleMaps().then(function (ok) {
      if (!ok || !window.google || !window.google.maps) {
        renderFallback(state);
        return;
      }
      buildMap(state);
    });
  }

  window.AppCardMap = { init: init };
})();
