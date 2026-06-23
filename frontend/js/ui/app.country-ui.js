(function () {
  "use strict";

  // Maskiert den Inhalt fuer eine sichere Ausgabe.
  function escapeHtml(value) {
    var fn = window.AppPageUtils && window.AppPageUtils.escapeHtml;
    if (typeof fn === "function") return fn(value);
    return String(value == null ? "" : value);
  }

  // Baut einen Prozent-/Anteilseintrag fuer Klima- und Vegetationslisten.
  function countryShareRow(label, share) {
    var fn = window.AppPageUtils && window.AppPageUtils.countryShareRow;
    if (typeof fn === "function") return fn(label, share);
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

  // Rendert anteilige Klima-Zeilen als Listeintraege.
  function climateRowsHtml(stats, climateLabel) {
    return (stats.climates || [])
      .map(function (item) {
        return countryShareRow(climateLabel(item && item.climate), item && item.share);
      })
      .join("");
  }

  // Rendert anteilige Vegetations-Zeilen als Listeintraege.
  function vegetationRowsHtml(stats, vegetationLabel) {
    return (stats.vegetations || [])
      .map(function (item) {
        return countryShareRow(vegetationLabel(item && item.vegetation), item && item.share);
      })
      .join("");
  }

  // Rendert den Hoehen-Abschnitt (min/avg/max).
  function elevationSummaryHtml(stats) {
    var elevationRange = stats.elevationRange || [null, null];
    var minE = elevationRange[0];
    var maxE = elevationRange[1];
    return "<p class=\"ci-kv\">min " + formatCountryNumber(minE) + " m - O " + formatCountryNumber(stats.avgElevation) + " m - max " + formatCountryNumber(maxE) + " m</p>";
  }

  // Rendert den Klima-Abschnitt inklusive Durchschnittswerte.
  function climateSummaryHtml(stats, climateRows) {
    var tempLine = stats.avgTemperature != null ? String(stats.avgTemperature) + " C" : "-";
    var precipLine = stats.avgPrecipitation != null ? formatCountryNumber(stats.avgPrecipitation) + " mm" : "-";
    return "\n      <h3 class=\"ci-h\">Klima</h3>\n      <p class=\"ci-kv\">O Temperatur: " + tempLine + "</p>\n      <p class=\"ci-kv\">O Niederschlag: " + precipLine + "</p>\n      " + (climateRows ? "<ul class=\"ci-shares\">" + climateRows + "</ul>" : "");
  }

  // Rendert den Vegetations-Abschnitt oder Fallback-Text.
  function vegetationSummaryHtml(vegRows) {
    return "\n      <h3 class=\"ci-h\">Vegetation</h3>\n      " + (vegRows ? "<ul class=\"ci-shares\">" + vegRows + "</ul>" : "<p class=\"ci-kv\">-</p>");
  }

  // Rendert die Kennzahlen fuer Arten- und Fundanzahl.
  function countryMetricsHtml(stats) {
    return "\n      <div class=\"ci-metrics\">\n        <div class=\"ci-metric\"><span class=\"ci-metric-num\">" + formatCountryNumber(stats.speciesCount) + "</span><span class=\"ci-metric-lbl\">Arten</span></div>\n        <div class=\"ci-metric\"><span class=\"ci-metric-num\">" + formatCountryNumber(stats.observationCount) + "</span><span class=\"ci-metric-lbl\">Funde</span></div>\n      </div>";
  }

  // Baut das komplette Sidebar-Panel aus den Teilsektionen zusammen.
  function countryPanelHtml(stats, labels) {
    var beetles = beetleListHtml(stats);
    var climateRows = climateRowsHtml(stats, labels.climateLabel);
    var vegRows = vegetationRowsHtml(stats, labels.vegetationLabel);

    return "\n    <div class=\"ci\">\n      " 
    + countryMetricsHtml(stats) + "\n\n      " 
    + (beetles ? "<h3 class=\"ci-h\">Haeufigste Kaefer</h3><ol class=\"ci-beetles\">" 
    + beetles + "</ol>" : "") + "\n\n      <h3 class=\"ci-h\">Hoehe</h3>\n      " 
    + elevationSummaryHtml(stats) + "\n\n      " 
    + climateSummaryHtml(stats, climateRows)  + "\n\n      " 
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
