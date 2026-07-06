(function () {
  "use strict";

  // Markiert die aktiven Eintraege einer Farblegende und aktualisiert "Alle anzeigen".
  function setLegendActiveState(ctx, legendId, activeColors) {
    var root = document.getElementById(legendId);
    if (!root) return;
    root.querySelectorAll("li").forEach(function (li) {
      var isAll = li.hasAttribute("data-legend-all");
      var color = ctx.legendItemColor(li);
      var isActive = isAll
        ? !activeColors || activeColors.size === 0
        : Boolean(activeColors && activeColors.size > 0) && activeColors.has(color);
      li.classList.toggle("is-active", isActive);
    });
  }

  // Markiert die aktiven Hoehenstufen in der Hoehenlegende.
  function setElevationLegendActiveState(ctx) {
    var root = document.getElementById("elevationLegend");
    if (!root) return;
    root.querySelectorAll("li").forEach(function (li) {
      var key = li.getAttribute("data-elevation") || "";
      var isAll = li.hasAttribute("data-legend-all");
      var isActive = isAll ? ctx.selectedElevationKeys.size === 0 : ctx.selectedElevationKeys.has(key);
      li.classList.toggle("is-active", isActive);
    });
  }

  // Prueft, ob die Bedingung erfuellt ist.
  function isBroadClimateCode(code) {
    var value = String(code || "").trim();
    if (!value) return false;
    if (/^[A-E]$/i.test(value)) return true;
    return ["unknown", "cold", "mild", "warm", "hot"].includes(value.toLowerCase());
  }

  // Uebernimmt selektierte Codes in die aktiven Legendenfarben.
  function syncLegendColorsFromSelection(rootId, selectedCodes, activeColorSet, getSelector, readColor, shouldSkipCode) {
    activeColorSet.clear();
    var root = document.getElementById(rootId);
    if (!root) return;

    selectedCodes.forEach(function (code) {
      if (shouldSkipCode && shouldSkipCode(code)) return;
      var li = root.querySelector(getSelector(code));
      if (!li) return;
      var color = readColor(li);
      if (color) activeColorSet.add(color);
    });
  }

  // Synchronisiert den Klima-Filterzustand in die aktive Klima-Legende.
  function syncClimateLegendColorsFromSelection(ctx) {
    syncLegendColorsFromSelection(
      "climateLegend",
      ctx.getSelectedClimateCodes(),
      ctx.activeClimateLegendColors,
      function (code) { return "li[data-filter-climate=\"" + code + "\"]"; },
      ctx.legendItemColor,
      isBroadClimateCode
    );
  }

  // Synchronisiert den Vegetations-Filterzustand in die aktive Vegetationslegende.
  function syncVegetationLegendColorsFromSelection(ctx) {
    syncLegendColorsFromSelection(
      "vegetationLegend",
      ctx.getSelectedVegetationCodes(),
      ctx.activeVegetationLegendColors,
      function (code) { return "li[data-filter-vegetation=\"" + code + "\"]"; },
      ctx.legendItemColor
    );
  }

  // Baut den Style fuer Thema-Layer anhand aktiver Legendenfarben.
  function buildThemeFeatureStyle(ctx, feat, activeColors) {
    var featureColor = ctx.normalizeLegendColor(feat.getProperty("color"));
    var visible = activeColors.size === 0 || activeColors.has(featureColor);
    return {
      fillColor: feat.getProperty("color"),
      fillOpacity: visible ? 0.72 : 0,
      strokeWeight: 0,
      visible: visible,
      clickable: false,
    };
  }

  // Wendet den Klima-Legendenfilter auf den Klima-GeoJSON-Layer an.
  function applyClimateLegendFilter(ctx) {
    if (!ctx.climateDataLayer) return;
    ctx.climateDataLayer.setStyle(function (feat) {
      return buildThemeFeatureStyle(ctx, feat, ctx.activeClimateLegendColors);
    });
    setLegendActiveState(ctx, "climateLegend", ctx.activeClimateLegendColors);
  }

  // Wendet den Vegetations-Legendenfilter auf den Vegetations-GeoJSON-Layer an.
  function applyVegetationLegendFilter(ctx) {
    if (!ctx.vegetationDataLayer) return;
    ctx.vegetationDataLayer.setStyle(function (feat) {
      return buildThemeFeatureStyle(ctx, feat, ctx.activeVegetationLegendColors);
    });
    setLegendActiveState(ctx, "vegetationLegend", ctx.activeVegetationLegendColors);
  }

  // Loescht die Auswahl fuer eine Subtyp-Legende und setzt UI + Zustand zurueck.
  function clearSubtypeLegendSelection(config) {
    config.activeColors.clear();
    config.filterEl.value = "all";
    config.setSelectedCodes([]);
  }

  // Setzt Einzel- oder Mehrfachauswahl fuer einen Subtyp-Legendeneintrag.
  function updateSubtypeLegendSelection(config, color, code, isMultiSelect) {
    if (isMultiSelect) {
      if (config.activeColors.has(color)) {
        config.activeColors.delete(color);
        if (code) config.selectedCodes.delete(code);
      } else {
        config.activeColors.add(color);
        if (code) config.selectedCodes.add(code);
      }
      return;
    }

    config.activeColors.clear();
    config.selectedCodes.clear();
    if (color) config.activeColors.add(color);
    if (code) config.selectedCodes.add(code);
  }

  // Synchronisiert den sichtbaren Filterwert (Select) mit der aktuellen Subtyp-Auswahl.
  function syncSubtypeFilterValue(config) {
    if (config.activeColors.size === 0) {
      config.filterEl.value = "all";
      config.setSelectedCodes([]);
      return;
    }
    config.filterEl.value = config.selectedCodes.size === 1 ? config.getSelectedCodes()[0] : "all";
  }

  // Behandelt Klicks auf Subtyp-Legenden (Klima/Vegetation) einheitlich.
  function handleSubtypeLegendClick(ctx, event, config) {
    var li = ctx.legendItemFromEvent(event);
    if (!li) return;

    if (li.hasAttribute("data-legend-all")) {
      clearSubtypeLegendSelection(config);
      config.applyLegendFilter(ctx);
      ctx.applyFilters();
      return;
    }

    var color = ctx.legendItemColor(li);
    var code = li.getAttribute(config.codeAttribute);
    var isMultiSelect = Boolean(event.shiftKey || event.ctrlKey || event.metaKey);

    updateSubtypeLegendSelection(config, color, code, isMultiSelect);
    syncSubtypeFilterValue(config);
    config.applyLegendFilter(ctx);
    ctx.applyFilters();
  }

  // Verarbeitet Klicks in der Klima-Legende.
  function handleClimateLegendClick(ctx, event) {
    handleSubtypeLegendClick(ctx, event, {
      activeColors: ctx.activeClimateLegendColors, selectedCodes: ctx.selectedClimateCodes,
      setSelectedCodes: ctx.setSelectedClimateCodes, getSelectedCodes: ctx.getSelectedClimateCodes,
      filterEl: ctx.climateFilter, codeAttribute: "data-filter-climate",
      applyLegendFilter: applyClimateLegendFilter,
    });
  }

  // Verarbeitet Klicks in der Vegetations-Legende.
  function handleVegetationLegendClick(ctx, event) {
    handleSubtypeLegendClick(ctx, event, {
      activeColors: ctx.activeVegetationLegendColors, selectedCodes: ctx.selectedVegetationCodes,
      setSelectedCodes: ctx.setSelectedVegetationCodes, getSelectedCodes: ctx.getSelectedVegetationCodes,
      filterEl: ctx.vegetationFilter, codeAttribute: "data-filter-vegetation",
      applyLegendFilter: applyVegetationLegendFilter,
    });
  }

  // Verarbeitet Klicks in der Hoehen-Legende.
  function handleElevationLegendClick(ctx, event) {
    var li = ctx.legendItemFromEvent(event);
    if (!li) return;

    if (li.hasAttribute("data-legend-all")) {
      ctx.setSelectedElevations([]);
      setElevationLegendActiveState(ctx);
      ctx.applyFilters();
      return;
    }

    var key = li.getAttribute("data-elevation");
    if (!key) return;

    if (event.shiftKey) {
      if (ctx.selectedElevationKeys.has(key)) ctx.selectedElevationKeys.delete(key);
      else ctx.selectedElevationKeys.add(key);
      ctx.elevationFilter.value = ctx.selectedElevationKeys.size === 1 ? ctx.getSelectedElevationKeys()[0] : "all";
    } else {
      ctx.setSelectedElevations([key]);
    }

    setElevationLegendActiveState(ctx);
    ctx.applyFilters();
  }

  // Bindet einen Klick-Handler auf eine Legendengruppe.
  function bindLegendClick(legendId, handler, getCtx) {
    var legend = document.getElementById(legendId);
    if (!legend) return;
    legend.addEventListener("click", function (event) {
      handler(getCtx(), event);
    });
  }

  // Initialisiert alle Klick-Handler fuer die drei Kartenlegenden.
  function initLegendFilters(getCtx) {
    bindLegendClick("climateLegend", handleClimateLegendClick, getCtx);
    bindLegendClick("vegetationLegend", handleVegetationLegendClick, getCtx);
    bindLegendClick("elevationLegend", handleElevationLegendClick, getCtx);
  }

  // Entfernt alle aktiven Themenlayer und blendet die Legenden aus.
  function hideAllThemeLayers(ctx) {
    if (!ctx.googleMapInstance) return;
    if (ctx.googleMapInstance.overlayMapTypes.getLength() > 0) {
      ctx.googleMapInstance.overlayMapTypes.clear();
    }
    ctx.googleMapInstance.setOptions({ maxZoom: null });
    if (ctx.climateDataLayer) ctx.climateDataLayer.setMap(null);
    if (ctx.vegetationDataLayer) ctx.vegetationDataLayer.setMap(null);
    document.querySelectorAll(".map-legend").forEach(function (el) { el.classList.add("is-hidden"); });
  }

  // Entscheidet, ob der raeumliche Untertyp-Filter aktiv sein muss.
  function shouldApplySubtypeSpatialFilter(ctx) {
    return ctx.enableSubtypeSpatialFilter && (
      (ctx.currentView === "climate" && ctx.activeClimateLegendColors.size > 0 && !ctx.areAllSubtypesOfSingleClimateGroupSelected()) ||
      (ctx.currentView === "vegetation" && ctx.activeVegetationLegendColors.size > 0)
    );
  }

  window.AppLegendController = {
    setLegendActiveState: setLegendActiveState, setElevationLegendActiveState: setElevationLegendActiveState,
    syncClimateLegendColorsFromSelection: syncClimateLegendColorsFromSelection, 
    syncVegetationLegendColorsFromSelection: syncVegetationLegendColorsFromSelection,
    applyClimateLegendFilter: applyClimateLegendFilter, applyVegetationLegendFilter: applyVegetationLegendFilter,
    handleClimateLegendClick: handleClimateLegendClick, handleVegetationLegendClick: handleVegetationLegendClick,
    handleElevationLegendClick: handleElevationLegendClick, initLegendFilters: initLegendFilters,
    hideAllThemeLayers: hideAllThemeLayers, isBroadClimateCode: isBroadClimateCode,
    shouldApplySubtypeSpatialFilter: shouldApplySubtypeSpatialFilter,
  };
})();
