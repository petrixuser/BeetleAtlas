(function () {
  // Normalisiert Eingabewerte fuer konsistente Verarbeitung.
  function normalizeCountryName(value) {
    return String(value || "").trim().replace(/\s+/g, " ");
  }

  // Leitet den passenden Zielwert aus den Eingaben ab.
  function resolveCountryDisplay(entry, maps) {
    var countryNameToIso = (maps && maps.COUNTRY_NAME_TO_ISO) || {};
    var isoToCountryName = (maps && maps.ISO_TO_COUNTRY_NAME) || {};

    var rawCode = String((entry && entry.code) || "").trim().toUpperCase();
    var rawName = normalizeCountryName((entry && entry.name) || "");
    var iso = rawCode.length === 2 ? rawCode : (countryNameToIso[rawName.toUpperCase()] || "");
    var fallbackName = iso ? (isoToCountryName[iso] || "") : "";
    var normalizedName = normalizeCountryName(
      rawName && rawName.length > 2 ? rawName : (fallbackName || (rawCode.length > 2 ? rawCode : rawName))
    );
    return {
      labelName: normalizedName || rawCode,
      iso: iso,
    };
  }

  // Ordnet eine numerische Hoehe einem der vordefinierten Hoehenbaender zu.
  function getElevationGroup(elevation) {
    if (elevation < 100) return "0_100";
    if (elevation < 500) return "100_500";
    if (elevation < 1000) return "500_1000";
    if (elevation < 2000) return "1000_2000";
    if (elevation < 3000) return "2000_3000";
    if (elevation < 4500) return "3000_4500";
    return "4500_plus";
  }

  // Erzeugt ein SVG-Element mit den angegebenen Attributen.
  function svgElement(name, attributes) {
    var element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes || {}).forEach(function (entry) {
      element.setAttribute(entry[0], entry[1]);
    });
    return element;
  }

  // Berechnet die Mercator-Y-Koordinate für eine gegebene Breite.
  function mercatorY(lat) {
    var radians = (Math.max(-85, Math.min(85, lat)) * Math.PI) / 180;
    return Math.log(Math.tan(Math.PI / 4 + radians / 2));
  }

  // Projektionsfunktion für Koordinaten basierend auf den Geo-Grenzen.
  function project(coord, geoBounds) {
    var lon = coord[0];
    var lat = coord[1];
    var padding = 40;
    var width = 1000 - padding * 2;
    var height = 980 - padding * 2;
    var x = padding + ((lon - geoBounds.minLon) / (geoBounds.maxLon - geoBounds.minLon)) * width;
    var maxY = mercatorY(geoBounds.maxLat);
    var minY = mercatorY(geoBounds.minLat);
    var y = padding + ((maxY - mercatorY(lat)) / (maxY - minY)) * height;
    return [x, y];
  }

  // Erstellt einen Pfad aus einem Ring basierend auf den Geo-Grenzen.
  function pathFromRing(ring, geoBounds) {
    return ring
      .map(function (coordinate, index) {
        var p = project(coordinate, geoBounds);
        var x = p[0];
        var y = p[1];
        return (index === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
      })
      .join(" ") + " Z";
  }

  // Erstellt einen Pfad aus einer Geometrie basierend auf den Geo-Grenzen.
  function pathFromGeometry(geometry, geoBounds) {
    if (geometry.type === "Polygon") {
      return geometry.coordinates.map(function (ring) { return pathFromRing(ring, geoBounds); }).join(" ");
    }

    if (geometry.type === "MultiPolygon") {
      return geometry.coordinates
        .map(function (polygon) {
          return polygon.map(function (ring) { return pathFromRing(ring, geoBounds); }).join(" ");
        })
        .join(" ");
    }

    return "";
  }

  // Sammelt die Koordinaten aus einer Geometrie.
  function collectCoordinates(geometry, output) {
    var out = output || [];
    if (geometry.type === "Polygon") {
      geometry.coordinates.flat().forEach(function (coordinate) { out.push(coordinate); });
    }

    if (geometry.type === "MultiPolygon") {
      geometry.coordinates.flat(2).forEach(function (coordinate) { out.push(coordinate); });
    }

    return out;
  }

  // Berechnet die Grenzen der gegebenen Features.
  function calculateBounds(features) {
    var coordinates = features.flatMap(function (feature) {
      return collectCoordinates(feature.geometry);
    });
    var lons = coordinates.map(function (c) { return c[0]; });
    var lats = coordinates.map(function (c) { return c[1]; });

    return {
      minLon: Math.min.apply(Math, lons), maxLon: Math.max.apply(Math, lons),
      minLat: Math.min.apply(Math, lats), maxLat: Math.max.apply(Math, lats),
    };
  }

  // Formatiert Temperaturwerte konsistent fuer die Listenansicht.
  function formatTemperature(value) {
    if (value === null || value === undefined || value === "") return "--";
    var num = Number(value);
    return Number.isFinite(num) ? num.toFixed(1) + " C" : "--";
  }

  // Generiert die URL für die Detailseite eines Käfers.
  function detailPageUrl(beetleId) {
    return "detail.html?id=" + encodeURIComponent(String(beetleId == null ? "" : beetleId));
  }

  // Gibt das Label für das Boden-pH-Band zurück.
  function soilPhBandLabel(value, labels) {
    if (!value || value === "unknown") return null;
    return (labels && labels[value]) || value;
  }

  // Gibt das Label für den Bodentyp zurück.
  function soilTypeLabel(value, labels) {
    if (!value || value === "unknown") return null;
    return (labels && labels[value]) || value;
  }

  // Formatiert Boden-pH inklusive Band- und Bodentyp-Informationen.
  function formatSoilPh(beetle, labels) {
    var shared = window.BeetleFormatters;
    if (shared && typeof shared.formatSoilPhFromRecord === "function") {
      return shared.formatSoilPhFromRecord(beetle, labels);
    }
    var phValue = beetle && beetle.meta && beetle.meta.location && beetle.meta.location.soilPh;
    var phBand = soilPhBandLabel(beetle && beetle.meta && beetle.meta.location && beetle.meta.location.soilPhBand, labels);
    var soilType = soilTypeLabel(beetle && beetle.soil, labels);
    var numeric = Number(phValue);
    if (Number.isFinite(numeric)) {
      var phText = phBand ? numeric.toFixed(1) + " (" + phBand + ")" : numeric.toFixed(1);
      return soilType ? phText + " · Boden: " + soilType : phText;
    }
    if (phBand) return soilType ? phBand + " · Boden: " + soilType : phBand;
    if (soilType) return "unbekannt · Boden: " + soilType;
    return "unbekannt";
  }

  // Extrahiert das Beobachtungsjahr eines Käfers.
  function extractObservedYear(beetle) {
    var eventDateValue =
      (beetle && beetle.observedAt) ||(beetle && beetle.meta && beetle.meta.observation && beetle.meta.observation.eventDate) || "";
    return String(eventDateValue).slice(0, 4);
  }

  // Prüft, ob ein Käfer ein Bild hat.
  function beetleHasImage(beetle) {
    return (
      Boolean(beetle && beetle.imageUrl) ||
      Boolean(beetle && beetle.meta && beetle.meta.observation && beetle.meta.observation.imageAvailable) ||
      (beetle && beetle.meta && beetle.meta.media && beetle.meta.media.coverage
        ? beetle.meta.media.coverage !== "no_images": false)
    );
  }

  // Einheitliche Client-Filterlogik fuer Demo-/Offline-Modus der Listenansicht.
  function beetleMatchesClientFilters(beetle, filters) {
    var search = (filters && filters.search) || "";
    var country = (filters && filters.country) || "all";
    var countryName = (filters && filters.countryName) || "";
    var climateSet = (filters && filters.climateSet) || new Set();
    var vegetationSet = (filters && filters.vegetationSet) || new Set();
    var elevationSet = (filters && filters.elevationSet) || new Set();
    var soilPhBand = (filters && filters.soilPhBand) || "all";
    var temperatureBand = (filters && filters.temperatureBand) || "all";
    var precipitationBand = (filters && filters.precipitationBand) || "all";
    var dataQuality = (filters && filters.dataQuality) || "all";
    var observedYear = (filters && filters.observedYear) || "";
    var imageMode = (filters && filters.imageMode) || "all";
    var getElevationGroupFn = (filters && filters.getElevationGroup) || getElevationGroup;

    var matchesSearch =
      String((beetle && beetle.name) || "").toLowerCase().includes(search) ||
      String((beetle && beetle.family) || "").toLowerCase().includes(search) ||
      String((beetle && beetle.location) || "").toLowerCase().includes(search);
    var matchesCountry = country === "all" || String((beetle && beetle.location) || "").toLowerCase().includes(countryName);
    var matchesClimate = climateSet.size === 0 || climateSet.has(beetle && beetle.climate);
    var matchesVegetation = vegetationSet.size === 0 || vegetationSet.has(beetle && beetle.vegetation);
    var matchesElevation = elevationSet.size === 0 || elevationSet.has(getElevationGroupFn(beetle && beetle.elevation));
    var matchesSoilPhBand = soilPhBand === "all" || 
      ((beetle && beetle.meta && beetle.meta.location && beetle.meta.location.soilPhBand) || "unknown") === soilPhBand;
    var matchesTempBand = temperatureBand === "all" ||
      ((beetle && beetle.ee && beetle.ee.bands && beetle.ee.bands.temperature) || "unknown") === temperatureBand;
    var matchesPrecipBand = precipitationBand === "all" ||
      ((beetle && beetle.ee && beetle.ee.bands && beetle.ee.bands.precipitation) || "unknown") === precipitationBand;
    var matchesDataQuality = dataQuality === "all" ||
      ((beetle && beetle.meta && beetle.meta.observation && beetle.meta.observation.eventDateQuality) || "unknown") === dataQuality;

    var beetleYear = extractObservedYear(beetle);
    var matchesYear = observedYear === "" || beetleYear === observedYear;
    var hasImage = beetleHasImage(beetle);
    var matchesImage = imageMode === "all" || (imageMode === "with_images" ? hasImage : !hasImage);

    return (
      matchesSearch && matchesCountry && matchesClimate && matchesVegetation &&
      matchesElevation && matchesSoilPhBand && matchesTempBand && matchesPrecipBand &&
      matchesDataQuality && matchesYear && matchesImage
    );
  }

  // Maskiert Inhalte fuer eine sichere Ausgabe.
  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>\"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // Erstellt eine Zeile für die Länderanteile.
  function countryShareRow(label, share) {
    var pct = share != null ? Math.round(share * 100) : null;
    var width = pct != null ? Math.max(4, Math.min(100, pct)) : 0;
    return "\n    <li class=\"ci-share\">\n      <span class=\"ci-share-label\">" + escapeHtml(label) + "</span>\n      <span class=\"ci-share-bar\"><span style=\"width:" + width + "%\"></span></span>\n      <span class=\"ci-share-pct\">" + (pct != null ? pct + " %" : "-") + "</span>\n    </li>";
  }

  window.AppPageUtils = {
    normalizeCountryName: normalizeCountryName, resolveCountryDisplay: resolveCountryDisplay,
    getElevationGroup: getElevationGroup, svgElement: svgElement, project: project, 
    pathFromGeometry: pathFromGeometry, calculateBounds: calculateBounds, formatTemperature: formatTemperature,
    detailPageUrl: detailPageUrl, formatSoilPh: formatSoilPh, beetleMatchesClientFilters: beetleMatchesClientFilters,
    escapeHtml: escapeHtml, countryShareRow: countryShareRow,
  };
})();
