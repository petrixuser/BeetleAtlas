(function () {
  "use strict";

  // Zeigt eine neutrale Ladeanzeige in Ueberschrift und Ergebnisliste.
  function showLoadingState(ctx) {
    var resultHeading = ctx && ctx.resultHeading;
    var resultList = ctx && ctx.resultList;
      var loadingText = (ctx && ctx.loadingText) || "Kaeferdaten werden geladen …";
    if (resultHeading) resultHeading.textContent = loadingText;
    if (resultList) {
      resultList.innerHTML = '\n        <div class="empty-state">' + loadingText + '</div>\n      ';
    }
  }

  // Rendert die Trefferliste der Artenkarten und liefert zurueck, ob Treffer vorhanden sind.
  function renderResultList(ctx) {
    var resultList = ctx && ctx.resultList;
    var displayBeetles = (ctx && ctx.displayBeetles) || [];
    var expandedIds = (ctx && ctx.expandedIds) || new Set();
    var climateLabel = ctx && ctx.climateLabel;
    var vegetationLabel = ctx && ctx.vegetationLabel;
    var beetleDetailHtml = ctx && ctx.beetleDetailHtml;
    var showLoading = Boolean(ctx && ctx.showLoadingState);

    if (!resultList) return false;
    if (typeof climateLabel !== "function") return false;
    if (typeof vegetationLabel !== "function") return false;
    if (typeof beetleDetailHtml !== "function") return false;

    if (!displayBeetles.length) {
      resultList.innerHTML = showLoading
          ? '\n          <div class="empty-state">Kaeferdaten werden geladen …</div>\n        '
        : '\n          <div class="empty-state">Keine passenden Arten gefunden.</div>\n        ';
      return false;
    }

    resultList.innerHTML = displayBeetles
      .map(function (beetle) {
        var expanded = expandedIds.has(String(beetle.id));
        var commonName = beetle.commonName
          ? ' <span class="common-name">' + beetle.commonName + '</span>'
          : "";
        var sub = [beetle.family, beetle.location].filter(Boolean).join(" - ");
        return '\n          <article class="species-card ' + (expanded ? "is-expanded" : "") + '" data-id="' + beetle.id + '">\n            <button class="species-card-head" type="button" aria-expanded="' + expanded + '">\n              <h3>' + beetle.name + commonName + '</h3>\n              <p>' + (sub || "—") + '</p>\n              <div class="meta-row">\n                <span class="tag">' + climateLabel(beetle.climate) + '</span>\n                <span class="tag">' + vegetationLabel(beetle.vegetation) + '</span>\n                <span class="tag">' + (beetle.elevation != null ? beetle.elevation : 0) + ' m</span>\n              </div>\n              <span class="expand-hint" aria-hidden="true"></span>\n            </button>\n            <div class="species-card-detail">' + beetleDetailHtml(beetle) + '</div>\n          </article>\n        ';
      })
      .join("");

    return true;
  }

  // Oeffnet den Punkt-Popup an der Mausposition innerhalb der Kartenflaeche.
  function openPointPopup(ctx) {
    var pointPopup = ctx && ctx.pointPopup;
    var beetle = (ctx && ctx.beetle) || {};
    var event = ctx && ctx.event;
    if (!pointPopup || !event || !event.currentTarget) return;

    pointPopup.innerHTML = '\n      <h3>' + beetle.name + '</h3>\n      <p>Hoehe: noch nicht eingetragen</p>\n      <p>Vegetation: noch nicht eingetragen</p>\n      <p>Klimazone: noch nicht eingetragen</p>\n    ';

    var canvas = event.currentTarget.closest(".map-canvas");
    if (!canvas) return;

    var canvasRect = canvas.getBoundingClientRect();
    var left = Math.min(event.clientX - canvasRect.left + 12, canvasRect.width - 210);
    var top = Math.min(event.clientY - canvasRect.top + 12, canvasRect.height - 150);

    pointPopup.style.left = Math.max(12, left) + "px";
    pointPopup.style.top = Math.max(12, top) + "px";
    pointPopup.classList.remove("is-hidden");
  }

  // Schließt den Punkt-Popup wieder.
  function closePointPopup(ctx) {
    var pointPopup = ctx && ctx.pointPopup;
    if (pointPopup) pointPopup.classList.add("is-hidden");
  }

  // Markiert den aktiven Kartenansichts-Button in der Toggle-Leiste.
  function setViewButtonsActive(ctx) {
    var view = ctx && ctx.view;
    document.querySelectorAll(".toggle-btn").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.view === view);
    });
  }

  // Ermittelt das sichtbare Label des aktiven Subtyp-Filters aus der Legende.
  function activeSubtypeLabel(currentView) {
    var legendId = currentView === "climate"
      ? "climateLegend"
      : (currentView === "vegetation" ? "vegetationLegend" : null);
    if (!legendId) return "Subtyp";
    var root = document.getElementById(legendId);
    if (!root) return "Subtyp";
    var activeItems = Array.from(root.querySelectorAll("li.is-active:not([data-legend-all])"));
    if (activeItems.length === 1) return activeItems[0].textContent.trim();
    if (activeItems.length > 1) return String(activeItems.length) + " Subtypen";
    return "Subtyp";
  }

  // Baut den kontextabhängigen Zusatztext für die Ergebnis-Ueberschrift.
  function activeFilterContextLabel(ctx) {
    var climates = (ctx && ctx.climates) || [];
    var vegetations = (ctx && ctx.vegetations) || [];
    var climateLabel = ctx && ctx.climateLabel;
    var vegetationLabel = ctx && ctx.vegetationLabel;
    var currentView = ctx && ctx.currentView;
    var hasSubtypeSpatialFilter = Boolean(ctx && ctx.hasSubtypeSpatialFilter);

    var parts = [];
    if (climates.length && typeof climateLabel === "function") {
      var climateText = climates.map(function (code) { return climateLabel(code); }).join(", ");
      parts.push("Klima: " + climateText);
    }
    
    if (vegetations.length && typeof vegetationLabel === "function") {
      var vegetationText = vegetations.map(function (code) { return vegetationLabel(code); }).join(", ");
      parts.push("Vegetation: " + vegetationText);
    }

    if (hasSubtypeSpatialFilter) {
      var group = currentView === "climate" ? "Klima-Untergruppe" : "Vegetations-Untergruppe";
      parts.push(group + ": " + activeSubtypeLabel(currentView));
    }
    return parts.join(" | ");
  }

  // Aktualisiert die Ergebnis-Ueberschrift anhand Trefferzahl, Backend-Zustand und Filterkontext.
  function updateResultHeading(ctx) {
    var resultHeading = ctx && ctx.resultHeading;
    if (!resultHeading) return;

    var shown = Number((ctx && ctx.shown) || 0);
    var featuredMode = Boolean(ctx && ctx.featuredMode);
    var apiEnabled = Boolean(ctx && ctx.apiEnabled);
    var subtypeListLoading = Boolean(ctx && ctx.subtypeListLoading);
    var hasSubtypeSpatialFilter = Boolean(ctx && ctx.hasSubtypeSpatialFilter);
    var lastRenderedMapPointTotal = Number(ctx && ctx.lastRenderedMapPointTotal);
    var totalBeetles = Number((ctx && ctx.totalBeetles) || 0);

    if (featuredMode) {
      resultHeading.textContent = "Bekannte Käfer Lateinamerikas";
      return;
    }

    if (apiEnabled && hasSubtypeSpatialFilter && subtypeListLoading) {
        resultHeading.textContent = "Kaeferdaten werden geladen …";
      return;
    }

    var shouldUseMapTotal =
      apiEnabled &&
      Number.isFinite(lastRenderedMapPointTotal) &&
      lastRenderedMapPointTotal >= shown;

    if (shouldUseMapTotal) {
      resultHeading.textContent = String(shown) + " von " + String(lastRenderedMapPointTotal) + " Treffern";
    } 

    else if (apiEnabled && totalBeetles > shown) {
      resultHeading.textContent = String(shown) + " von " + String(totalBeetles) + " Treffern";
    } 
    
    else {
      resultHeading.textContent = String(shown) + " gefundene Arten";
    }

    var context = activeFilterContextLabel(ctx);
    if (context) resultHeading.textContent = resultHeading.textContent + " | " + context;
  }

  // Befuellt das Laender-Dropdown aus den vorbereiteten Länderdaten sortiert nach Anzeigename.
  function populateCountryFilter(ctx) {
    var countryFilter = ctx && ctx.countryFilter;
    var countryStats = ctx && ctx.countryStats;
    var resolveCountryDisplay = ctx && ctx.resolveCountryDisplay;
    if (!countryFilter || !countryStats || typeof resolveCountryDisplay !== "function") return;

    Object.values(countryStats)
      .map(function (c) { return { code: c.code, name: c.name }; })
      .sort(function (a, b) {
        return resolveCountryDisplay(a).labelName.localeCompare(resolveCountryDisplay(b).labelName, "de");
      })
      .forEach(function (c) {
        var opt = document.createElement("option");
        opt.value = c.code;
        var display = resolveCountryDisplay(c);
        opt.dataset.countryName = display.labelName;
        opt.textContent = display.iso ? display.labelName + " (" + display.iso + ")" : display.labelName;
        countryFilter.appendChild(opt);
      });
  }

  window.AppMainUI = {
    showLoadingState: showLoadingState, renderResultList: renderResultList,
    openPointPopup: openPointPopup, closePointPopup: closePointPopup,
    setViewButtonsActive: setViewButtonsActive, updateResultHeading: updateResultHeading,
    populateCountryFilter: populateCountryFilter,
  };
})();
