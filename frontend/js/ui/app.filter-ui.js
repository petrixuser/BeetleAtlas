(function () {
  "use strict";

  // Liest die aktiven Set-Auswahlen fuer Klima, Vegetation und Hoehe.
  function readSelections(ctx) {
    var selections = (ctx && ctx.selections) || {};
    return {
      selectedClimateCodes: selections.selectedClimateCodes || new Set(),
      selectedVegetationCodes: selections.selectedVegetationCodes || new Set(),
      selectedElevationKeys: selections.selectedElevationKeys || new Set(),
    };
  }

  // Liest Getter-Funktionen mit sicheren Fallbacks.
  function readGetters(ctx) {
    var getters = (ctx && ctx.getters) || {};
    return {
      getSelectedClimateCodes: getters.getSelectedClimateCodes || function () { return []; },
      getSelectedVegetationCodes: getters.getSelectedVegetationCodes || function () { return []; },
      getSelectedElevationKeys: getters.getSelectedElevationKeys || function () { return []; },
    };
  }

  // Liefert den sichtbaren Optionstext fuer einen Select-Wert.
  function optionTextByValue(selectEl, value) {
    if (!selectEl || value === null || value === undefined) return "";
    var options = Array.prototype.slice.call(selectEl.options || []);
    var hit = options.find(function (opt) { return String(opt.value) === String(value); });
    return hit ? String(hit.text || "").trim() : "";
  }

  // Formatiert Hoehen-Keys (z. B. 0_100) lesbar wie im Dropdown (z. B. 0-100 m).
  function formatElevationChipText(getters, elements) {
    return getters.getSelectedElevationKeys().map(function (key) {
      return optionTextByValue(elements.elevationFilter, key) || String(key || "");
    }).join(", ");
  }

  // Baut die Rohdefinition aller Filter fuer Darstellung und Aktivstatus.
  function filterDescriptors(ctx) {
    var elements = (ctx && ctx.elements) || {};
    var selections = readSelections(ctx);
    var getters = readGetters(ctx);

    return [
      { key: "country", label: "Land", el: elements.countryFilter },
      {
        key: "climate",label: "Klima",el: elements.climateFilter,
        customActive: selections.selectedClimateCodes.size > 0,
        customText: getters.getSelectedClimateCodes().join(", "),
      },
      {
        key: "vegetation", label: "Vegetation", el: elements.vegetationFilter,
        customActive: selections.selectedVegetationCodes.size > 0,
        customText: getters.getSelectedVegetationCodes().join(", "),
      },
      {
        key: "elevation", label: "Hoehe", el: elements.elevationFilter,
        customActive: selections.selectedElevationKeys.size > 0,
        customText: formatElevationChipText(getters, elements),
      },
      { key: "soilPhBand", label: "Boden-pH-Band", el: elements.soilPhBandFilter },
      { key: "temperatureBand", label: "Temperaturband", el: elements.temperatureBandFilter },
      { key: "precipitationBand", label: "Niederschlagsband", el: elements.precipitationBandFilter },
      { key: "dataQuality", label: "Datenqualitaet", el: elements.dataQualityFilter },
      { key: "year", label: "Fundjahr", el: elements.yearFilter, freeText: true },
      { key: "image", label: "Bilder", el: elements.imageFilter },
    ];
  }

  // Ermittelt den Anzeigetext eines Filters fuer den Chip.
  function filterText(filter) {
    var freeText = Boolean(filter.freeText);
    if (filter.customText !== undefined) return filter.customText;
    if (freeText) return (filter.el && filter.el.value ? String(filter.el.value).trim() : "");
    return (filter.el && filter.el.selectedOptions && filter.el.selectedOptions[0])
      ? filter.el.selectedOptions[0].text: (filter.el ? filter.el.value : "");
  }

  // Bestimmt, ob ein Filter aktuell als aktiv gilt.
  function filterActiveState(filter) {
    var freeText = Boolean(filter.freeText);
    if (filter.customActive !== undefined) return Boolean(filter.customActive);
    if (freeText) return Boolean(filter.el && String(filter.el.value || "").trim() !== "");
    return Boolean(filter.el && filter.el.value !== "all");
  }

  // Normalisiert einen Filtereintrag fuer die UI-Weiterverarbeitung.
  function normalizeFilter(filter) {
    return {
      key: filter.key,label: filter.label,el: filter.el,
      freeText: Boolean(filter.freeText),
      active: filterActiveState(filter),
      text: filterText(filter),
    };
  }

  // Setzt Klima-Filter und zugehoerige Klima-Legendenzustaende zurueck.
  function clearClimateFilter(ctx) {
    var actions = (ctx && ctx.actions) || {};
    var legendState = (ctx && ctx.legendState) || {};
    if (typeof actions.setSelectedClimateCodes === "function") actions.setSelectedClimateCodes([]);
    if (legendState.activeClimateLegendColors) legendState.activeClimateLegendColors.clear();
    if (typeof actions.applyClimateLegendFilter === "function") actions.applyClimateLegendFilter();
  }

  // Setzt Vegetations-Filter und zugehoerige Legendenzustaende zurueck.
  function clearVegetationFilter(ctx) {
    var actions = (ctx && ctx.actions) || {};
    var legendState = (ctx && ctx.legendState) || {};
    if (typeof actions.setSelectedVegetationCodes === "function") actions.setSelectedVegetationCodes([]);
    if (legendState.activeVegetationLegendColors) legendState.activeVegetationLegendColors.clear();
    if (typeof actions.applyVegetationLegendFilter === "function") actions.applyVegetationLegendFilter();
  }

  // Setzt Hoehen-Filter inklusive Legendenstatus zurueck.
  function clearElevationFilter(ctx) {
    var actions = (ctx && ctx.actions) || {};
    if (typeof actions.setSelectedElevations === "function") actions.setSelectedElevations([]);
    if (typeof actions.setElevationLegendActiveState === "function") actions.setElevationLegendActiveState();
  }

  // Setzt einfache Select-/Text-Filter auf ihren Standardwert.
  function clearSimpleFilter(filter) {
    if (!filter.el) return;
    filter.el.value = filter.freeText ? "" : "all";
  }

  // Rendert einen einzelnen Filter-Chip mit Remove-Aktion.
  function renderChip(filter, ctx, activeFiltersEl) {
    var chip = document.createElement("span");
    chip.className = "filter-chip";

    var text = document.createElement("span");
    text.textContent = filter.label + ": " + filter.text;
    chip.appendChild(text);

    var remove = document.createElement("button");
    remove.type = "button";
    remove.className = "filter-chip-remove";
    remove.setAttribute("aria-label", filter.label + "-Filter entfernen");
    remove.textContent = "x";
    remove.addEventListener("click", function () {
      clearFilter(filter, ctx);
      if (typeof ctx.onApplyFilters === "function") ctx.onApplyFilters();
    });

    chip.appendChild(remove);
    activeFiltersEl.appendChild(chip);
  }

  // Rendert alle aktiven Filter-Chips in den Zielcontainer.
  function renderFilterChips(activeFilters, ctx, activeFiltersEl) {
    activeFiltersEl.innerHTML = "";
    activeFilters.forEach(function (filter) {
      renderChip(filter, ctx, activeFiltersEl);
    });
  }

  // Aktualisiert den numerischen Badge fuer aktive Filter.
  function renderFilterBadge(activeCount, filterBadgeEl) {
    filterBadgeEl.textContent = String(activeCount);
    filterBadgeEl.classList.toggle("is-hidden", activeCount === 0);
  }

  // Liest die aktuell aktiven Mehrfachselektionen aus dem Context.
  function panelFilterState(ctx) {
    return filterDescriptors(ctx).map(normalizeFilter);
  }

  // Setzt einen Filter inklusive zugehoeriger Legendenzustaende zurueck.
  function clearFilter(filter, ctx) {
    if (filter.key === "climate") {
      clearClimateFilter(ctx);
      return;
    }
    if (filter.key === "vegetation") {
      clearVegetationFilter(ctx);
      return;
    }
    if (filter.key === "elevation") {
      clearElevationFilter(ctx);
      return;
    }
    clearSimpleFilter(filter);
  }

  // Rendert Badge + Filter-Chips auf Basis der aktuell aktiven Filter.
  function updateFilterUI(ctx) {
    var elements = ctx.elements || {};
    var filterBadge = elements.filterBadge;
    var activeFilters = elements.activeFilters;
    if (!filterBadge || !activeFilters) return;

    var filters = panelFilterState(ctx);
    var active = filters.filter(function (f) { return f.active; });

    renderFilterBadge(active.length, filterBadge);
    renderFilterChips(active, ctx, activeFilters);
  }

  window.AppFilterUI = {
    panelFilterState: panelFilterState, updateFilterUI: updateFilterUI,
  };
})();
