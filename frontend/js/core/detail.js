// Kern-Modul der Detailseite: laedt Kaeferdaten und Medien aus dem Backend
// (mit lokalem Fallback), formatiert Umweltwerte und rendert Faktenblöcke,
// Metrikbalken, Sticky-Header und die Standortkarte.
(function () {
  "use strict";

  // Liefert ein Detail-Element ueber seine DOM-ID.
  function $(id) {
    return document.getElementById(id);
  }

  var loadingEl = $("detailLoading");
  var errorEl = $("detailError");
  var errorTextEl = $("detailErrorText");
  var contentEl = $("detailContent");
  var envRangesCache = null;
  var APP_CATALOG = window.AppCatalog || {};

  // ===== Konstanten und Delegation =====

  var DEFAULT_METRIC_RANGES = {
    elevation: { min: 0, max: 4500 },
    temperature: { min: -5, max: 40 },
    worldclimBio01: { min: -5, max: 40 },
    precipitation: { min: 0, max: 3000 },
    worldclimBio12: { min: 0, max: 3000 },
    soilMoisture: { min: 0, max: 0.6 },
    ndvi: { min: -0.2, max: 1.0 },
    relativeHumidity: { min: 0, max: 100 },
    surfacePressureHpa: { min: 850, max: 1050 },
    nighttimeLights: { min: 0, max: 120 },
    slope: { min: 0, max: 45 },
    distanceToWaterM: { min: 0, max: 5000 },
    humanModification: { min: 0, max: 1 },
  };

  // Kapselt Aufrufe ins Kartenmodul, damit die Seite ohne Karten-Skript nicht crasht.
  function callDetailMapPage(method, fallback, arg) {
    var mapPage = window.DetailMapPage;
    if (!mapPage || typeof mapPage[method] !== "function") return fallback;
    return mapPage[method](arg);
  }

  // Kapselt Aufrufe ins Detail-UI-Modul fuer DOM-zentrierte Renderlogik.
  function callDetailUi(method, fallback, arg) {
    var ui = window.DetailUI;
    if (!ui || typeof ui[method] !== "function") return fallback;
    return ui[method](arg);
  }

  // Blendet ein Element sichtbar ein.
  function show(el) {
    if (el) el.classList.remove("is-hidden");
  }

  // Blendet ein Element aus.
  function hide(el) {
    if (el) el.classList.add("is-hidden");
  }

  // Zeigt einen Fehlzustand an und blendet Lade-/Inhaltsbereich aus.
  function showError(message) {
    hide(loadingEl);
    hide(contentEl);
    if (errorTextEl) errorTextEl.textContent = message;
    show(errorEl);
  }

  // ===== Generische Wert-Hilfsfunktionen =====

  // Liefert die API-Basis-URL (leer, wenn kein Backend konfiguriert ist).
  function apiBase() {
    return window.API_BASE_URL || "";
  }

  // Prueft, ob die Detailseite mit Backend-API arbeiten kann.
  function apiEnabled() {
    return Boolean(apiBase());
  }

  // Formatiert den Wert fuer die Anzeige.
  function formatValue(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (Array.isArray(value)) return value.join(", ");
    if (typeof value === "boolean") return value ? "ja" : "nein";
    if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(3);
    return String(value);
  }

  // Formatiert den Wert fuer die Anzeige.
  function formatOneDecimal(value) {
    var num = Number(value);
    return Number.isFinite(num) ? num.toFixed(1) : null;
  }

  // Formatiert den Wert fuer die Anzeige.
  function formatThreeDecimals(value) {
    var num = Number(value);
    return Number.isFinite(num) ? num.toFixed(3) : null;
  }

  // Zentrale Uebersetzung technischer Klassen/Codes kommt aus dem Shared-Catalog.
  var CODE_VALUE_DE = APP_CATALOG.CODE_VALUE_DE || {};

  // Uebersetzt einen numerischen Landbedeckungs-Code in eine deutsche Bezeichnung.
  var landcoverClassLabelFn = typeof APP_CATALOG.landcoverClassLabel === "function"
    ? APP_CATALOG.landcoverClassLabel
    : function () { return null; };

  // ===== Fachliche Formatierung =====

  // Uebersetzt einen technischen Code in eine lesbare deutsche Bezeichnung.
  function formatCodeValue(value) {
    if (value === null || value === undefined || value === "") return null;
    var key = String(value).trim();
    if (!key) return null;
    var lookup = key.toLowerCase();
    if (Object.prototype.hasOwnProperty.call(CODE_VALUE_DE, lookup)) {
      return CODE_VALUE_DE[lookup];
    }
    var text = key.replace(/_/g, " ").trim();
    if (!text) return null;
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  // Baut die Landbedeckungs-Anzeige: bevorzugt die deutsche Gruppenbezeichnung,
  function landcoverText(landcoverGroup, landcoverClass) {
    var groupText = formatCodeValue(landcoverGroup);
    if (groupText && groupText !== "Unbekannt") return groupText;
    var classText = landcoverClassLabelFn(landcoverClass);
    if (classText) return classText;
    return groupText || null;
  }

  // Kombiniert numerischen Wert und Klassenband in ein gemeinsames Label.
  function withBand(valueText, bandText) {
    if (!valueText) return null;
    if (!bandText) return valueText;
    return valueText + " (" + bandText + ")";
  }

  var SOIL_PH_BAND_LABELS = APP_CATALOG.SOIL_PH_BAND_LABELS || {
    strongly_acidic: "stark sauer",
    acidic: "sauer",
    neutral: "neutral",
    alkaline: "alkalisch",
    strongly_alkaline: "stark alkalisch",
  };

  // Uebersetzt den Boden-pH-Bandcode in einen lesbaren Text.
  function soilPhBandLabel(value) {
    var shared = window.BeetleFormatters;
    if (shared && typeof shared.soilBandLabel === "function") {
      return shared.soilBandLabel(value, SOIL_PH_BAND_LABELS);
    }
    if (!value || value === "unknown") return null;
    return SOIL_PH_BAND_LABELS[value] || value;
  }

  // Uebersetzt den Bodentypcode in einen lesbaren Text.
  function soilTypeLabel(value) {
    var shared = window.BeetleFormatters;
    if (shared && typeof shared.soilTypeLabel === "function") {
      return shared.soilTypeLabel(value, SOIL_PH_BAND_LABELS);
    }
    if (!value || value === "unknown") return null;
    return SOIL_PH_BAND_LABELS[value] || value;
  }

  // Entspricht fachlich der Boden-pH-Darstellung aus der Listenansicht, inkl. Bodentyp-Anhang.
  function formatSoilPhWithType(detail) {
    var shared = window.BeetleFormatters;
    if (shared && typeof shared.formatSoilPhFromRecord === "function") {
      return shared.formatSoilPhFromRecord(detail, SOIL_PH_BAND_LABELS);
    }
    var phValue = detail && detail.meta && detail.meta.location && detail.meta.location.soilPh;
    var phBandRaw = detail && detail.meta && detail.meta.location && detail.meta.location.soilPhBand;
    var phBand = soilPhBandLabel(phBandRaw);
    var soilType = soilTypeLabel(detail && detail.soil);
    var numeric = Number(phValue);

    if (Number.isFinite(numeric)) {
      var phText = phBand ? numeric.toFixed(1) + " (" + phBand + ")" : numeric.toFixed(1);
      if (soilType && phBand && soilType !== phBand) {
        return phText + " · Boden: " + soilType;
      }
      return phText;
    }
    if (phBand) {
      if (soilType && soilType !== phBand) return phBand + " · Boden: " + soilType;
      return phBand;
    }
    if (soilType) return "unbekannt · Boden: " + soilType;
    return "unbekannt";
  }

  // Baut kuratierte Metadaten-Zeilen fuer den Faktenbereich.
  function curatedMetaRows(detail) {
    var meta = detail && detail.meta ? detail.meta : {};
    var observation = meta.observation || {};
    var taxonomy = meta.taxonomy || {};

    return [
      ["GBIF-ID", observation.gbifId],
      ["Datensatz", observation.datasetName],
      ["Institution", observation.institutionCode],
      ["Nachweisart", formatCodeValue(observation.basisOfRecordClass)],
      ["Taxon-ID", taxonomy.taxonId],
      ["Gattung", taxonomy.genus],
      ["Art-Epithet", taxonomy.specificEpithet],
      ["Taxon-Aufloesung", formatCodeValue(taxonomy.resolution)],
    ];
  }

  // Baut kuratierte Qualitaets-/Abdeckungs-Zeilen fuer den Faktenbereich.
  function curatedQualityRows(detail) {
    var meta = detail && detail.meta ? detail.meta : {};
    var observation = meta.observation || {};
    var location = meta.location || {};
    var media = meta.media || {};

    return [
      ["Event-Date Qualität", formatCodeValue(observation.eventDateQuality)],
      [
        "Koordinaten-Unschaerfe",
        withBand(
          location.coordinateUncertainty != null ? location.coordinateUncertainty + " m" : null,
          formatCodeValue(location.coordinateUncertaintyBand)
        ),
      ],
      ["Bild vorhanden", observation.imageAvailable],
      ["Medien-Abdeckung", formatCodeValue(media.coverage)],
    ];
  }

  // ===== Sticky-Header =====

  // Rendert den mitscrollenden Kopfbereich der Detailseite.
  function renderStickyHeader(detail) {
    callDetailUi("renderStickyHeader", undefined, {
      detail: detail,
      formatCodeValue: formatCodeValue,
      formatOneDecimal: formatOneDecimal,
      soilPhBandLabel: soilPhBandLabel,
      elevationText: elevationText,
    });
  }

  // Aktiviert den Sticky-Header passend zum Scrollzustand.
  function setupStickyVisibility() {
    callDetailUi("setupStickyVisibility");
  }

  // Rendert die zugehoerigen Inhalte fuer die UI.
  function renderClimateChips(detail) {
    callDetailUi("renderClimateChips", undefined, {
      detail: detail,
      formatCodeValue: formatCodeValue,
      formatOneDecimal: formatOneDecimal,
      soilPhBandLabel: soilPhBandLabel,
      landcoverText: landcoverText,
    });
  }

  // ===== Schnelle Umweltmetriken =====

  // Begrenzt einen Wert auf den Prozentbereich 0-100.
  function clampPct(value) {
    var n = Number(value);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(100, n));
  }

  // Konvertiert Werte robust in endliche Zahlen oder null.
  function toFiniteNumber(value) {
    var n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  // Leitet den passenden Zielwert aus den Eingaben ab.
  function resolveElevationValue(detail) {
    var direct = toFiniteNumber(detail && detail.elevation);
    if (direct !== null) return direct;

    var locationElevation = toFiniteNumber(detail && detail.meta && detail.meta.location && detail.meta.location.elevation);
    if (locationElevation !== null) return locationElevation;

    return toFiniteNumber(detail && detail.ee && detail.ee.raw && detail.ee.raw.elevation);
  }

  // Formatiert die Hoehe kompakt in Metern.
  function elevationText(detail) {
    var value = resolveElevationValue(detail);
    return value === null ? null : Math.round(value) + " m";
  }

  // Liefert den angeforderten Wert aus dem aktuellen Zustand.
  function getRangeBounds(ranges, key) {
    var fromApi = ranges && ranges[key] ? ranges[key] : null;
    var fallback = DEFAULT_METRIC_RANGES[key] || { min: 0, max: 1 };
    var minValue = toFiniteNumber(fromApi && fromApi.min);
    var maxValue = toFiniteNumber(fromApi && fromApi.max);
    if (minValue === null || maxValue === null || maxValue <= minValue) {
      return { min: fallback.min, max: fallback.max };
    }
    return { min: minValue, max: maxValue };
  }

  // Liefert den angeforderten Wert aus dem aktuellen Zustand.
  function getCombinedRangeBounds(ranges, keys, fallback) {
    var collected = [];
    (keys || []).forEach(function (key) {
      var bounds = getRangeBounds(ranges, key);
      if (bounds && Number.isFinite(bounds.min) && Number.isFinite(bounds.max) && bounds.max > bounds.min) {
        collected.push(bounds);
      }
    });

    if (!collected.length) {
      return fallback || { min: 0, max: 1 };
    }

    var minValue = collected[0].min;
    var maxValue = collected[0].max;
    collected.forEach(function (bounds) {
      if (bounds.min < minValue) minValue = bounds.min;
      if (bounds.max > maxValue) maxValue = bounds.max;
    });
    return { min: minValue, max: maxValue };
  }

  // Rechnet einen Messwert in Prozent relativ zu einem Wertebereich um.
  function percentFromRange(value, minValue, maxValue) {
    var numericValue = toFiniteNumber(value);
    if (numericValue === null) return 0;
    var numericMin = toFiniteNumber(minValue);
    var numericMax = toFiniteNumber(maxValue);
    if (numericMax === null) return 0;
    if (numericMin === null || numericMax <= numericMin) {
      return numericMax <= 0 ? 0 : clampPct((numericValue / numericMax) * 100);
    }
    return clampPct(((numericValue - numericMin) / (numericMax - numericMin)) * 100);
  }

  // Baut alle benoetigten Wertebereiche fuer die Umweltmetriken.
  function buildMetricBounds(ranges) {
    return {
      elevationBounds: getCombinedRangeBounds(ranges, ["elevation", "elevationM", "elevation_m"], { min: 0, max: 4500 }),
      temperatureBounds: getRangeBounds(ranges, "temperature"),
      worldclimTempBounds: getRangeBounds(ranges, "worldclimBio01"),
      precipitationBounds: getRangeBounds(ranges, "precipitation"),
      worldclimPrecipBounds: getRangeBounds(ranges, "worldclimBio12"),
      soilMoistureBounds: getRangeBounds(ranges, "soilMoisture"),
      ndviBounds: getRangeBounds(ranges, "ndvi"),
      humidityBounds: getRangeBounds(ranges, "relativeHumidity"),
      pressureBounds: getRangeBounds(ranges, "surfacePressureHpa"),
      nighttimeLightsBounds: getRangeBounds(ranges, "nighttimeLights"),
      slopeBounds: getRangeBounds(ranges, "slope"),
      distanceToWaterBounds: getRangeBounds(ranges, "distanceToWaterM"),
      humanModificationBounds: getRangeBounds(ranges, "humanModification"),
    };
  }

  // Leitet Temperatur- und Niederschlagswerte fuer Metrikbalken ab.
  function deriveMetricDisplayValues(detail, raw, location) {
    return {
      tempValue: raw.temperature != null
        ? Number(raw.temperature)
        : detail && detail.temperature != null
          ? Number(detail.temperature)
          : null,
      precipValue: raw.precipitation != null
        ? Number(raw.precipitation)
        : location.worldclimBio12 != null
          ? Number(location.worldclimBio12)
          : null,
    };
  }

  // Baut Kernzeilen (Hoehe, Temperatur, Niederschlag) fuer die Metrikbalken.
  function buildMetricCoreRows(detail, location, bounds, values) {
    return [
      {
        label: "Hoehe",
        tone: "slope",
        valueText: elevationText(detail) || "—",
        pct: percentFromRange(resolveElevationValue(detail), bounds.elevationBounds.min, bounds.elevationBounds.max),
      },
      {
        label: "Temperatur",
        tone: "temp",
        valueText: values.tempValue != null ? formatOneDecimal(values.tempValue) + " °C" : "—",
        pct: percentFromRange(values.tempValue, bounds.temperatureBounds.min, bounds.temperatureBounds.max),
      },
      {
        label: "Temperatur (Langzeitklima)",
        tone: "temp",
        valueText: location.worldclimBio01 != null ? formatOneDecimal(location.worldclimBio01) + " °C" : "—",
        pct: percentFromRange(location.worldclimBio01, bounds.worldclimTempBounds.min, bounds.worldclimTempBounds.max),
      },
      {
        label: "Niederschlag",
        tone: "precip",
        valueText: values.precipValue != null ? Math.round(values.precipValue) + " mm" : "—",
        pct: percentFromRange(values.precipValue, bounds.precipitationBounds.min, bounds.precipitationBounds.max),
      },
      {
        label: "Niederschlag (Langzeitklima)",
        tone: "precip",
        valueText: location.worldclimBio12 != null ? Math.round(Number(location.worldclimBio12)) + " mm/Jahr" : "—",
        pct: percentFromRange(location.worldclimBio12, bounds.worldclimPrecipBounds.min, bounds.worldclimPrecipBounds.max),
      },
    ];
  }

  // Baut Feuchte-/Vegetationszeilen fuer die Metrikbalken.
  function buildMetricMoistureRows(raw, bounds) {
    return [
      {
        label: "Bodenfeuchte",
        tone: "moisture",
        valueText: raw.soilMoisture != null ? formatThreeDecimals(raw.soilMoisture) : "—",
        pct: percentFromRange(raw.soilMoisture, bounds.soilMoistureBounds.min, bounds.soilMoistureBounds.max),
      },
      {
        label: "NDVI",
        tone: "ndvi",
        valueText: raw.ndvi != null ? formatThreeDecimals(raw.ndvi) : "—",
        pct: percentFromRange(raw.ndvi, bounds.ndviBounds.min, bounds.ndviBounds.max),
      },
      {
        label: "Luftfeuchte",
        tone: "humidity",
        valueText: raw.relativeHumidity != null ? formatOneDecimal(raw.relativeHumidity) + " %" : "—",
        pct: percentFromRange(raw.relativeHumidity, bounds.humidityBounds.min, bounds.humidityBounds.max),
      },
    ];
  }

  // Baut Atmosphaeren-/Umfeldzeilen fuer die Metrikbalken.
  function buildMetricEnvironmentRows(raw, bounds) {
    return [
      {
        label: "Luftdruck",
        tone: "pressure",
        valueText: raw.surfacePressureHpa != null ? formatOneDecimal(raw.surfacePressureHpa) + " hPa" : "—",
        pct: percentFromRange(raw.surfacePressureHpa, bounds.pressureBounds.min, bounds.pressureBounds.max),
      },
      {
        label: "Nachtlicht",
        tone: "light",
        valueText: raw.nighttimeLights != null ? formatOneDecimal(raw.nighttimeLights) + " nW" : "—",
        pct: percentFromRange(raw.nighttimeLights, bounds.nighttimeLightsBounds.min, bounds.nighttimeLightsBounds.max),
      },
      {
        label: "Hangneigung",
        tone: "slope",
        valueText: raw.slope != null ? formatOneDecimal(raw.slope) + " °" : "—",
        pct: percentFromRange(raw.slope, bounds.slopeBounds.min, bounds.slopeBounds.max),
      },
      {
        label: "Distanz zu Wasser",
        tone: "water",
        valueText: raw.distanceToWaterM != null ? Math.round(Number(raw.distanceToWaterM)) + " m" : "—",
        pct: percentFromRange(raw.distanceToWaterM, bounds.distanceToWaterBounds.min, bounds.distanceToWaterBounds.max),
      },
      {
        label: "Menschlicher Einfluss",
        tone: "impact",
        valueText: raw.humanModification != null ? formatThreeDecimals(raw.humanModification) : "—",
        pct: percentFromRange(raw.humanModification, bounds.humanModificationBounds.min, bounds.humanModificationBounds.max),
      },
    ];
  }

  // Baut die Balkenzeilen fuer die schnelle Umweltuebersicht.
  function buildMetricRows(detail, raw, location, bounds, values) {
    return []
      .concat(buildMetricCoreRows(detail, location, bounds, values))
      .concat(buildMetricMoistureRows(raw, bounds))
      .concat(buildMetricEnvironmentRows(raw, bounds));
  }

  // Rendert die zugehoerigen Inhalte fuer die UI.
  function renderMetricBars(detail) {
    var raw = detail && detail.ee && detail.ee.raw ? detail.ee.raw : {};
    var location = detail && detail.meta && detail.meta.location ? detail.meta.location : {};
    var ranges = envRangesCache || DEFAULT_METRIC_RANGES;
    var bounds = buildMetricBounds(ranges);
    var values = deriveMetricDisplayValues(detail, raw, location);
    var rows = buildMetricRows(detail, raw, location, bounds, values);
    callDetailUi("renderMetricBars", undefined, { rows: rows, clampPct: clampPct });
  }

  // Leitet kombinierte Niederschlagsangaben fuer den EE-Faktenblock ab.
  function buildCuratedPrecipTexts(location, raw) {
    return {
      worldclimPrecipText: location.worldclimBio12 != null
        ? Math.round(Number(location.worldclimBio12)) + " mm/Jahr"
        : null,
      monthlyPrecipText: raw.precipitation != null ? Math.round(Number(raw.precipitation)) + " mm" : null,
    };
  }

  // Leitet Temperaturangaben inkl. Fallback fuer den EE-Faktenblock ab.
  function buildCuratedTempTexts(detail, raw) {
    return {
      eeTempText: raw.temperature != null ? formatOneDecimal(raw.temperature) + " °C" : null,
      fallbackTempText:
        raw.temperature == null && detail && detail.temperature != null
          ? formatOneDecimal(detail.temperature) + " °C"
          : null,
    };
  }

  // Baut kuratierte Earth-Engine/Umwelt-Zeilen fuer den Faktenbereich.
  function curatedEeRows(detail) {
    var meta = detail && detail.meta ? detail.meta : {};
    var location = meta.location || {};
    var ee = detail && detail.ee ? detail.ee : {};
    var bands = ee.bands || {};
    var raw = ee.raw || {};

    var precipTexts = buildCuratedPrecipTexts(location, raw);
    var tempTexts = buildCuratedTempTexts(detail, raw);

    return [
      ["Wissenschaftlicher Name", detail && detail.name ? detail.name : null],
      ["Land", location.country],
      ["Region", location.region],
      ["Stadt", location.city],
      ["Hoehe", elevationText(detail)],
      ["Vegetation", formatCodeValue(detail && detail.vegetation)],
      ["Koordinaten-Unschaerfe", location.coordinateUncertainty != null ? location.coordinateUncertainty + " m" : null],
      ["Organischer Bodenkohlenstoff", location.soilOrganicCarbon != null ? formatThreeDecimals(location.soilOrganicCarbon) + " %" : null,],
      ["WorldClim Jahresmitteltemperatur", location.worldclimBio01 != null ? formatOneDecimal(location.worldclimBio01) + " °C" : null,],
      ["WorldClim Jahresniederschlag", precipTexts.worldclimPrecipText],
      ["Temperatur", tempTexts.eeTempText || tempTexts.fallbackTempText],
      ["Niederschlag", precipTexts.monthlyPrecipText],
      ["Bodenfeuchte", raw.soilMoisture != null ? formatThreeDecimals(raw.soilMoisture) + " m³/m³" : null,],
      ["NDVI", raw.ndvi != null ? formatThreeDecimals(raw.ndvi) : null],
      ["Relative Luftfeuchte", raw.relativeHumidity != null ? formatOneDecimal(raw.relativeHumidity) + " %" : null,],
      ["Luftdruck", raw.surfacePressureHpa != null ? formatOneDecimal(raw.surfacePressureHpa) + " hPa" : null,],
      ["Nachtlicht", raw.nighttimeLights != null ? formatOneDecimal(raw.nighttimeLights) + " nW/cm²/sr" : null,],
      ["Hangneigung", raw.slope != null ? formatOneDecimal(raw.slope) + " °" : null],
      ["Distanz zu Wasser", raw.distanceToWaterM != null ? Math.round(Number(raw.distanceToWaterM)) + " m" : null,],
      ["Menschlicher Einfluss", raw.humanModification != null ? formatThreeDecimals(raw.humanModification) : null,],
      ["Landbedeckung", landcoverText(bands.landcoverGroup, raw.landcoverClass)],
    ];
  }
  // ===== Datenladen =====

  // Rendert eine Schluessel-Wert-Liste in das angegebene <dl>-Element.
  function setKv(dl, rows) {
    callDetailUi("renderKeyValue", undefined, { dl: dl, rows: rows, formatValue: formatValue });
  }


  // Rendert die zugehoerigen Inhalte fuer die UI.
  function renderMedia(mediaItems) {
    callDetailUi("renderMedia", undefined, { mediaItems: mediaItems });
  }

  // ===== Haupt-Rendering =====

  // Leitet Temperatur-/Niederschlagswerte fuer den oberen Faktenbereich ab.
  function buildTopSummary(detail) {
    var raw = detail && detail.ee && detail.ee.raw ? detail.ee.raw : {};
    var location = detail && detail.meta && detail.meta.location ? detail.meta.location : {};

    var topTempText =
      raw.temperature != null
        ? formatOneDecimal(raw.temperature) + " °C"
        : detail.temperature != null
          ? formatOneDecimal(detail.temperature) + " °C"
          : null;

    var topPrecipText =
      raw.precipitation != null
        ? Math.round(Number(raw.precipitation)) + " mm"
        : location.worldclimBio12 != null
          ? Math.round(Number(location.worldclimBio12)) + " mm/Jahr"
          : null;

    return {
      topTempText: topTempText,
      topPrecipText: topPrecipText,
    };
  }

  // Setzt Titel, Untertitel und Hero-Bild der Detailseite.
  function renderDetailHeader(detail) {
    $("detailTitle").textContent = detail.name || "Unbekannter Kaefer";
    $("detailSubtitle").textContent = [detail.family, detail.location].filter(Boolean).join(" · ") || "—";
    callDetailUi("renderHero", undefined, { detail: detail });
  }

  // Rendert den kompakten Kernfakten-Block oben auf der Seite.
  function renderCoreFacts(detail, summary) {
    setKv($("detailCoreFacts"), [
      ["ID", detail.id],
      ["Beobachtet am", detail.observedAt],
      ["Koordinaten", Array.isArray(detail.coordinates) ? detail.coordinates.join(", ") : null],
      ["Klimazone", formatCodeValue(detail.climate)],
      ["Vegetation", formatCodeValue(detail.vegetation)],
      ["Hoehe", elevationText(detail)],
      ["Temperatur", summary.topTempText],
      ["Niederschlag", summary.topPrecipText],
      ["Boden-pH", formatSoilPhWithType(detail)],
    ]);
  }

  // Rendert Meta-, Qualitaets- und EE-Faktenlisten.
  function renderDetailFactSections(detail) {
    setKv($("detailMetaFacts"), curatedMetaRows(detail));
    setKv($("detailQualityFacts"), curatedQualityRows(detail));
    setKv($("detailEeFacts"), curatedEeRows(detail));
  }

  // Rendert Sticky-Header, Chips und Metrikbalken.
  function renderDetailEnhancements(detail) {
    renderStickyHeader(detail);
    setupStickyVisibility();
    renderClimateChips(detail);
    renderMetricBars(detail);
  }

  // Schaltet nach erfolgreichem Rendern in den Inhaltszustand.
  function showDetailContentState() {
    hide(loadingEl);
    hide(errorEl);
    show(contentEl);
  }

  // Rendert die komplette Detailseite (Header, Fakten, Metriken, Karte, Medien).
  async function render(detail, mediaItems) {
    var summary = buildTopSummary(detail);

    renderDetailHeader(detail);
    renderCoreFacts(detail, summary);
    renderDetailFactSections(detail);
    renderDetailEnhancements(detail);

    await Promise.resolve(callDetailMapPage("renderLocationMap", undefined, detail));

    renderMedia(mediaItems);
    showDetailContentState();
  }

  // Bindet optionale Detailkarten-Features (Toggle + Legenden).
  function initDetailMapUi() {
    callDetailMapPage("initDetailMapToggle");
    callDetailMapPage("initDetailLegendFilters");
  }

  // Liest die Kaefer-ID aus der URL und validiert sie.
  function resolveBeetleIdFromUrl() {
    var params = new URLSearchParams(window.location.search);
    return params.get("id");
  }

  // Laedt Detaildaten bevorzugt aus der API, mit lokalem Fallback.
  async function resolveDetailData(beetleId) {
    if (apiEnabled()) {
      try {
        return await window.DetailData.loadFromApi(beetleId);
      } catch (apiError) {
        var fallbackData = window.DetailData.loadFromLocal(beetleId);
        if (!fallbackData) throw apiError;
        return fallbackData;
      }
    }

    var localData = window.DetailData.loadFromLocal(beetleId);
    if (!localData) {
      throw new Error("Ohne Backend konnte diese ID nicht in den lokalen Daten gefunden werden.");
    }
    return localData;
  }

  // Aktualisiert Umweltbereiche im Hintergrund und rendert Metriken danach neu.
  function refreshRangesInBackground(detail) {
    window.DetailData.loadEnvironmentRanges().then(function (ranges) {
      if (!ranges) return;
      envRangesCache = ranges;
      renderMetricBars(detail);
    });
  }

  // Wandelt unbekannte Fehler in eine stabile Benutzerfehlermeldung.
  function resolveErrorMessage(error) {
    return error && error.message ? error.message : "Die Detaildaten konnten nicht geladen werden.";
  }

  // Initialisiert die benoetigten Ablaufe und Startwerte.
  async function init() {
    // Reihenfolge: UI binden -> Datenquelle aufloesen -> rendern -> optionale Range-Nachladung.
    initDetailMapUi();
    var beetleId = resolveBeetleIdFromUrl();

    if (!beetleId) {
      showError("Es wurde keine Kaefer-ID uebergeben.");
      return;
    }

    try {
      var data = await resolveDetailData(beetleId);

      var allMedia = window.DetailData.uniqueMediaUrls(data.detail, data.media || []);
      await render(data.detail, allMedia);
      refreshRangesInBackground(data.detail);
    } catch (error) {
      showError(resolveErrorMessage(error));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

