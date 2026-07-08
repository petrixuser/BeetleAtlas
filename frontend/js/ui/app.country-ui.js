(function () {
  "use strict";

  // Maskiert den Inhalt fuer eine sichere Ausgabe.
  function escapeHtml(value) {
    var fn = window.AppPageUtils && window.AppPageUtils.escapeHtml;
    if (typeof fn === "function") return fn(value);
    return String(value == null ? "" : value);
  }

  // Baut einen Prozent-/Anteilseintrag fuer Klima- und Vegetationslisten (mit Farbe).
  function countryShareRow(label, share, color) {
    var fn = window.AppPageUtils && window.AppPageUtils.countryShareRow;
    if (typeof fn === "function") return fn(label, share, color);
    return "";
  }

  // Formatiert Zahlen robust fuer Statistikzeilen und Kennzahlen.
  function formatCountryNumber(value) {
    return value == null ? "-" : Number(value).toLocaleString("de-DE");
  }

  // Liefert Label-Funktionen mit stabilen Fallbacks.
  function statsLabels(ctx) {
    return {
      climateLabel: (ctx && ctx.climateLabel) || function (v) { return v || "Unbekannt"; },
      vegetationLabel: (ctx && ctx.vegetationLabel) || function (v) { return v || "Unbekannt"; },
    };
  }

  // Liest den Stats-Snapshot fuer ein Land aus der globalen Datenstruktur.
  function countryStats(countryName) {
    return window.COUNTRY_STATS && window.COUNTRY_STATS[countryName];
  }

  // Rendert die Liste der haeufigsten Kaefer als HTML.
  function beetleListHtml(stats) {
    return (stats.topBeetles || [])
      .map(function (beetle, index) {
        return "\n      <li>\n        <span class=\"ci-rank\">" + (index + 1) + "</span>\n        <span class=\"ci-beetle\">\n          <em>" + escapeHtml((beetle && beetle.name) || "-") + "</em>\n          " + ((beetle && beetle.family) ? "<span class=\"ci-beetle-fam\">" + escapeHtml(beetle.family) + "</span>" : "") + "\n        </span>\n        <span class=\"ci-count\">" + formatCountryNumber(beetle && beetle.count) + "</span>\n      </li>";
      })
      .join("");
  }

  // Liefert die Farb-Lookups (gleiche Farben wie Karte/Detail).
  function legendColors() {
    return window.BEETLE_LEGEND_COLORS || {
      climateMajorColor: function () { return null; },
      koppenColor: function () { return null; },
      koppenLabel: function (c) { return c; },
      vegetationZoneColor: function () { return null; },
    };
  }

  // Rendert anteilige Klima-Zeilen (Hauptgruppen) als farbige Listeintraege.
  function climateRowsHtml(stats, climateLabel) {
    var colors = legendColors();
    return (stats.climates || [])
      .map(function (item) {
        return countryShareRow(climateLabel(item && item.climate), item && item.share, colors.climateMajorColor(item && item.climate));
      })
      .join("");
  }

  // Rendert die haeufigsten Koeppen-Subtypen (feine Kartenzonen) als farbige Zeilen.
  function koppenRowsHtml(stats) {
    var colors = legendColors();
    return (stats.topKoppen || [])
      .map(function (item) {
        var code = item && item.koppen;
        return countryShareRow(colors.koppenLabel(code), item && item.share, colors.koppenColor(code));
      })
      .join("");
  }

  // Rendert anteilige Vegetations-Zeilen: bevorzugt die feinen Kartenzonen.
  function vegetationRowsHtml(stats, vegetationLabel) {
    var colors = legendColors();
    var zones = stats.topVegetationZones || [];
    if (zones.length) {
      return zones
        .map(function (item) {
          var zone = item && item.zone;
          return countryShareRow(zone || "Unbekannt", item && item.share, colors.vegetationZoneColor(zone));
        })
        .join("");
    }
    return (stats.vegetations || [])
      .map(function (item) {
        return countryShareRow(vegetationLabel(item && item.vegetation), item && item.share);
      })
      .join("");
  }

  // Rendert den Klima-&-Umwelt-Abschnitt: Metrik-Vergleichsbalken (Hoehe,
  // Temperatur, Niederschlag, ... jeweils mit min/O/max), dann die
  // Klimazonen-Verteilung (A-E) und die feinen Koeppen-Zonen.
  function climateSummaryHtml(stats, climateRows, koppenRows) {
    var envBars = metricBarsHtml(stats, [
      "elevation", "temperature", "precipitation", "soilMoisture", "ndvi", "humidity",
      "pressure", "light", "slope", "waterDistance", "humanModification", "soilPh",
    ]);
    var envBlock = envBars ? "<ul class=\"ci-mlist\">" + envBars + "</ul>" : "";
    var distBlock = climateRows
      ? "\n      <p class=\"ci-subh\">Klimazonen-Verteilung</p>\n      <ul class=\"ci-shares\">" + climateRows + "</ul>"
      : "";
    var koppenBlock = koppenRows
      ? "\n      <p class=\"ci-subh\">Koeppen-Zonen</p>\n      <ul class=\"ci-shares\">" + koppenRows + "</ul>"
      : "";
    return "\n      <h3 class=\"ci-h\">Klima &amp; Umwelt</h3>\n      <p class=\"ci-hint\">Balken: O-Wert im Vergleich zu allen Laendern - je hoeher, desto laenger und dunkler. Darunter min/max im Land.</p>\n      "
      + envBlock + distBlock + koppenBlock;
  }

  // Rendert den Vegetations-Abschnitt oder Fallback-Text.
  function vegetationSummaryHtml(vegRows) {
    return "\n      <h3 class=\"ci-h\">Vegetation</h3>\n      " + (vegRows ? "<ul class=\"ci-shares\">" + vegRows + "</ul>" : "<p class=\"ci-kv\">-</p>");
  }
  var METRIC_DEFS = [
    { key: "elevation", label: "Höhe", unit: " m", digits: 0, clampMin: 0, tone: { start: "#dcc9a3", end: "#7a5a2e" } },
    { key: "temperature", label: "Temperatur", unit: " °C", digits: 1, tone: { start: "#f3b087", end: "#bf4b1a" } },
    { key: "precipitation", label: "Niederschlag", unit: " mm", digits: 0, tone: { start: "#9bc6ea", end: "#2667a3" } },
    { key: "soilMoisture", label: "Bodenfeuchte", unit: "", digits: 3, tone: { start: "#8fd6cb", end: "#22786b" } },
    { key: "ndvi", label: "NDVI (Vegetation)", unit: "", digits: 3, tone: { start: "#98cc98", end: "#387b38" } },
    { key: "humidity", label: "Luftfeuchte", unit: " %", digits: 1, tone: { start: "#8eb8dc", end: "#1f5f98" } },
    { key: "pressure", label: "Luftdruck", unit: " hPa", digits: 0, tone: { start: "#c9d2dc", end: "#4a5a6b" } },
    { key: "light", label: "Nachtlicht (Helligkeit)", unit: "", digits: 2, tone: { start: "#f2e2a6", end: "#b8860b" } },
    { key: "slope", label: "Hangneigung", unit: " °", digits: 1, tone: { start: "#cdd6a3", end: "#5f6b2e" } },
    { key: "waterDistance", label: "Distanz zu Wasser", unit: " m", digits: 0, tone: { start: "#a9dce8", end: "#216b82" } },
    { key: "humanModification", label: "Menschl. Einfluss", unit: "", digits: 3, tone: { start: "#e8b4c4", end: "#9e2a5a" } },
    { key: "soilPh", label: "Boden-pH", unit: "", digits: 1, tone: { start: "#cdb4e8", end: "#5a2a9e" } },
  ];

  var METRIC_BY_KEY = {};
  METRIC_DEFS.forEach(function (m) { METRIC_BY_KEY[m.key] = m; });

  // Liefert {min, avg, max} einer Metrik; faellt auf flache avg*-Felder zurueck
  // (aeltere Snapshots ohne metrics-Objekt).
  function metricValue(stats, key) {
    var mv = stats.metrics && stats.metrics[key];
    if (mv && typeof mv === "object") return mv;
    var flatKey = "avg" + key.charAt(0).toUpperCase() + key.slice(1);
    var flat = stats[flatKey];
    return { min: null, avg: (typeof flat === "number" ? flat : null), max: null };
  }

  var _rangeCache = null;

  // Ermittelt Min/Max des O-Werts jeder Metrik ueber ALLE Laender (fuer die
  // relative Balkenlaenge).
  function crossCountryRanges() {
    if (_rangeCache) return _rangeCache;
    var stats = window.COUNTRY_STATS || {};
    var ranges = {};
    METRIC_DEFS.forEach(function (m) { ranges[m.key] = { min: Infinity, max: -Infinity }; });
    Object.keys(stats).forEach(function (name) {
      var s = stats[name];
      METRIC_DEFS.forEach(function (m) {
        var v = metricValue(s, m.key).avg;
        if (typeof v === "number" && isFinite(v)) {
          if (v < ranges[m.key].min) ranges[m.key].min = v;
          if (v > ranges[m.key].max) ranges[m.key].max = v;
        }
      });
    });
    _rangeCache = ranges;
    return ranges;
  }

  // Parst einen Hex-Farbwert in RGB-Kanaele.
  function parseHexColor(hex) {
    var clean = String(hex || "").replace("#", "").trim();
    if (clean.length !== 6) return null;
    var r = parseInt(clean.slice(0, 2), 16);
    var g = parseInt(clean.slice(2, 4), 16);
    var b = parseInt(clean.slice(4, 6), 16);
    if (!isFinite(r) || !isFinite(g) || !isFinite(b)) return null;
    return { r: r, g: g, b: b };
  }

  // Interpoliert Start-/End-Farbe -> dunkler Endton bei hohem Wert.
  function mixToneColor(startHex, endHex, ratio) {
    var start = parseHexColor(startHex);
    var end = parseHexColor(endHex);
    if (!start || !end) return endHex || startHex || "#2f6b47";
    var t = Math.max(0, Math.min(1, Number(ratio) || 0));
    var r = Math.round(start.r + (end.r - start.r) * t);
    var g = Math.round(start.g + (end.g - start.g) * t);
    var b = Math.round(start.b + (end.b - start.b) * t);
    return "rgb(" + r + ", " + g + ", " + b + ")";
  }

  // Formatiert einen Metrikwert (Nachkommastellen + Einheit).
  function formatMetricValue(value, m) {
    if (typeof value !== "number" || !isFinite(value)) return "-";
    var num = m.digits ? value.toFixed(m.digits) : String(Math.round(value));
    return num + m.unit;
  }

  // Baut eine einzelne Metrik-Balkenzeile: Kopf (Label + O-Wert), Balken mit
  // dynamischem Verlauf, darunter min/max des Landes.
  function metricBarRow(m, stats, ranges) {
    var mv = metricValue(stats, m.key);
    var v = mv.avg;
    if (typeof v !== "number" || !isFinite(v)) return "";
    var r = ranges[m.key] || { min: v, max: v };
    var span = r.max - r.min;
    var frac = span > 0 ? (v - r.min) / span : 0.5;
    frac = Math.max(0, Math.min(1, frac));
    var width = Math.max(6, Math.round(frac * 100));
    var endColor = mixToneColor(m.tone.start, m.tone.end, frac);
    var grad = "linear-gradient(90deg, " + m.tone.start + " 0%, " + endColor + " 100%)";
    return "\n      <li class=\"ci-mrow\">"
      + "\n        <div class=\"ci-mrow-head\"><span class=\"ci-mrow-name\">" + escapeHtml(m.label) + "</span>"
      + "<span class=\"ci-mrow-avg\">O " + escapeHtml(formatMetricValue(v, m)) + "</span></div>"
      + "\n        <span class=\"ci-mrow-bar\"><span style=\"width:" + width + "%;background:" + grad + "\"></span></span>"
      + "\n        <div class=\"ci-mrow-mm\"><span>min " + escapeHtml(formatMetricValue(mv.min, m)) + "</span>"
      + "<span>max " + escapeHtml(formatMetricValue(mv.max, m)) + "</span></div>"
      + "\n      </li>";
  }

  // Rendert mehrere Metrik-Balken (nach Schluessel) als Listeneintraege.
  function metricBarsHtml(stats, keys) {
    var ranges = crossCountryRanges();
    return keys.map(function (k) {
      var m = METRIC_BY_KEY[k];
      return m ? metricBarRow(m, stats, ranges) : "";
    }).join("");
  }

  // Rendert die Kennzahlen fuer Arten- und Fundanzahl.
  function countryMetricsHtml(stats) {
    return "\n      <div class=\"ci-metrics\">\n        <div class=\"ci-metric\"><span class=\"ci-metric-num\">" + formatCountryNumber(stats.speciesCount) + "</span><span class=\"ci-metric-lbl\">Arten</span></div>\n        <div class=\"ci-metric\"><span class=\"ci-metric-num\">" + formatCountryNumber(stats.observationCount) + "</span><span class=\"ci-metric-lbl\">Funde</span></div>\n      </div>";
  }

  // Baut das komplette Sidebar-Panel aus den Teilsektionen zusammen.
  function countryPanelHtml(stats, labels) {
    var beetles = beetleListHtml(stats);
    var climateRows = climateRowsHtml(stats, labels.climateLabel);
    var koppenRows = koppenRowsHtml(stats);
    var vegRows = vegetationRowsHtml(stats, labels.vegetationLabel);

    return "\n    <div class=\"ci\">\n      " 
    + countryMetricsHtml(stats) + "\n\n      " 
    + (beetles ? "<h3 class=\"ci-h\">Haeufigste Kaefer</h3><ol class=\"ci-beetles\">" 
    + beetles + "</ol>" : "") + "\n\n      " 
    + climateSummaryHtml(stats, climateRows, koppenRows)  + "\n\n      " 
    + vegetationSummaryHtml(vegRows) + "\n    </div>";
  }

  // Baut die Sidebar-Inhalte fuer ein Land aus dem Snapshot COUNTRY_STATS.
  function renderCountryInfo(countryName, ctx) {
    var labels = statsLabels(ctx);
    var stats = countryStats(countryName);
    if (!stats) {
      return "<p>Fuer dieses Land sind noch keine aufbereiteten Daten verfuegbar.</p>";
    }

    return countryPanelHtml(stats, labels);
  }

  // Fuellt die Sidebar und blendet sie ein.
  function openCountrySidebar(countryName, ctx) {
    var titleEl = ctx && ctx.titleEl;
    var contentEl = ctx && ctx.contentEl;
    var sidebarEl = ctx && ctx.sidebarEl;
    if (!titleEl || !contentEl || !sidebarEl) return;

    titleEl.textContent = countryName;
    contentEl.innerHTML = renderCountryInfo(countryName, {
      climateLabel: ctx && ctx.climateLabel,
      vegetationLabel: ctx && ctx.vegetationLabel,
    });
    sidebarEl.classList.add("is-open");
    document.body.classList.add("country-sidebar-open");
    sidebarEl.setAttribute("aria-hidden", "false");
  }

  // Schaltet die Sidebar aus der Ansicht.
  function closeCountrySidebar(ctx) {
    var sidebarEl = ctx && ctx.sidebarEl;
    if (!sidebarEl) return;
    sidebarEl.classList.remove("is-open");
    document.body.classList.remove("country-sidebar-open");
    sidebarEl.setAttribute("aria-hidden", "true");
  }

  window.AppCountryUI = {
    renderCountryInfo: renderCountryInfo, openCountrySidebar: openCountrySidebar, closeCountrySidebar: closeCountrySidebar,
  };
})();
