(function () {
  "use strict";

  // Liest den Element-Container defensiv aus dem Context.
  function readElements(ctx) {
    return (ctx && ctx.elements) || {};
  }

  // Liest den Actions-Container defensiv aus dem Context.
  function readActions(ctx) {
    return (ctx && ctx.actions) || {};
  }

  // Schaltet eine Ergebnis-Karte zwischen eingeklappt und aufgeklappt um.
  function toggleResultCard(ctx, card, head) {
    var id = String(card.dataset.id);
    var willExpand = !ctx.expandedIds.has(id);
    if (willExpand) ctx.expandedIds.add(id);
    else ctx.expandedIds.delete(id);

    card.classList.toggle("is-expanded", willExpand);
    head.setAttribute("aria-expanded", String(willExpand));
    ctx.actions.saveMainState();
  }

  // Synchronisiert den Expand-Status von Artenkarten in der Ergebnisliste.
  function bindResultListToggle(ctx) {
    var resultList = readElements(ctx).resultList;
    if (!resultList) return;
    resultList.addEventListener("click", function (event) {
      var delBtn = event.target.closest(".beetle-delete");
      if (delBtn) {
        event.preventDefault();
        event.stopPropagation();
        if (ctx.actions && typeof ctx.actions.deleteBeetle === "function") {
          ctx.actions.deleteBeetle(delBtn.getAttribute("data-delete-id"));
        }
        return;
      }

      var head = event.target.closest(".species-card-head");
      if (!head) return;

      var card = head.closest(".species-card");
      if (!card) return;
      toggleResultCard(ctx, card, head);
    });
  }

  // Bindet Sofort-Filter (Selects ohne Debounce) an applyFilters.
  function attachImmediateFilterChanges(elements, actions) {
    [
      elements.countryFilter, elements.soilPhBandFilter, elements.temperatureBandFilter,
      elements.precipitationBandFilter, elements.dataQualityFilter, elements.imageFilter,
    ].forEach(function (element) {
      if (!element) return;
      element.addEventListener("change", actions.applyFilters);
    });
  }

  // Synchronisiert Klima-Auswahl zwischen Dropdown, Legende und Datenfilter.
  function syncClimateSelection(elements, actions, state) {
    if (elements.climateFilter.value === "all") actions.setSelectedClimateCodes([]);
    else actions.setSelectedClimateCodes([elements.climateFilter.value]);
    actions.syncClimateLegendColorsFromSelection();
    actions.setLegendActiveState("climateLegend", state.activeClimateLegendColors);
    actions.applyClimateLegendFilter();
    actions.applyFilters();
  }

  // Synchronisiert Vegetations-Auswahl zwischen Dropdown, Legende und Datenfilter.
  function syncVegetationSelection(elements, actions, state) {
    if (elements.vegetationFilter.value === "all") actions.setSelectedVegetationCodes([]);
    else actions.setSelectedVegetationCodes([elements.vegetationFilter.value]);
    actions.syncVegetationLegendColorsFromSelection();
    actions.setLegendActiveState("vegetationLegend", state.activeVegetationLegendColors);
    actions.applyVegetationLegendFilter();
    actions.applyFilters();
  }

  // Synchronisiert Hoehen-Auswahl zwischen Dropdown, Legende und Datenfilter.
  function syncElevationSelection(elements, actions) {
    if (elements.elevationFilter.value === "all") actions.setSelectedElevations([]);
    else actions.setSelectedElevations([elements.elevationFilter.value]);
    actions.setElevationLegendActiveState();
    actions.applyFilters();
  }

  // Bindet die Suche mit Debounce, um zu haeufige Filterlaeufe zu vermeiden.
  function bindSearchInput(elements, actions, debounceRef) {
    if (!elements.searchInput) return;
    elements.searchInput.addEventListener("input", function () {
      clearTimeout(debounceRef.value);
      debounceRef.value = setTimeout(actions.applyFilters, 500);
    });
  }

  // Bindet das Jahresfeld mit kurzer Debounce-Logik fuer Eingaben.
  function bindYearInput(elements, actions, debounceRef) {
    if (!elements.yearFilter) return;
    elements.yearFilter.addEventListener("change", actions.applyFilters);
    elements.yearFilter.addEventListener("input", function () {
      clearTimeout(debounceRef.value);
      debounceRef.value = setTimeout(actions.applyFilters, 300);
    });
  }

  // Schaltet das Filterpanel ein/aus und pflegt aria-expanded.
  function bindFilterToggle(elements) {
    if (!elements.filterToggle || !elements.filterPanel) return;
    elements.filterToggle.addEventListener("click", function () {
      var collapsed = elements.filterPanel.classList.toggle("is-collapsed");
      elements.filterToggle.setAttribute("aria-expanded", String(!collapsed));
    });
  }

  // Verdrahtet alle Eingabefilter inkl. Debounce- und Legendensynchronisierung.
  function bindFilterInputs(ctx) {
    var elements = readElements(ctx);
    var actions = readActions(ctx);
    var state = (ctx && ctx.state) || {};
    var debounceRef = { value: null };

    bindSearchInput(elements, actions, debounceRef);
    attachImmediateFilterChanges(elements, actions);
    if (elements.climateFilter) {
      elements.climateFilter.addEventListener("change", function () {
        syncClimateSelection(elements, actions, state);
      });
    }
    if (elements.vegetationFilter) {
      elements.vegetationFilter.addEventListener("change", function () {
        syncVegetationSelection(elements, actions, state);
      });
    }
    if (elements.elevationFilter) {
      elements.elevationFilter.addEventListener("change", function () {
        syncElevationSelection(elements, actions);
      });
    }
    bindYearInput(elements, actions, debounceRef);
    bindFilterToggle(elements);
  }

  // Berechnet den Zoom-Mittelpunkt relativ zur SVG-Fläche.
  function mapWheelCenter(atlasSvg, event) {
    var rect = atlasSvg.getBoundingClientRect();
    return {
      centerX: ((event.clientX - rect.left) / rect.width) * 1000, centerY: ((event.clientY - rect.top) / rect.height) * 980,
    };
  }

  // Bindet Zoom-In/Out und Reset der Kartenansicht.
  function bindMapZoomButtons(elements, actions) {
    if (elements.zoomInButton) {
      elements.zoomInButton.addEventListener("click", function () {
        actions.setZoom(actions.getZoom() * 1.25);
      });
    }
    if (elements.zoomOutButton) {
      elements.zoomOutButton.addEventListener("click", function () {
        actions.setZoom(actions.getZoom() / 1.25);
      });
    }
    if (elements.resetMapButton) {
      elements.resetMapButton.addEventListener("click", actions.resetMapView);
    }
  }

  // Bindet Mausrad-Zoom auf die SVG-Karte.
  function bindMapWheel(atlasSvg, actions) {
    if (!atlasSvg) return;
    atlasSvg.addEventListener("wheel", function (event) {
      event.preventDefault();
      var center = mapWheelCenter(atlasSvg, event);
      var nextZoom = event.deltaY < 0 ? actions.getZoom() * 1.12 : actions.getZoom() / 1.12;
      actions.setZoom(nextZoom, center.centerX, center.centerY);
    });
  }

  // Bindet Drag-Pan fuer die SVG-Karte inklusive Drag-Zustand.
  function bindMapDrag(atlasSvg, actions) {
    if (!atlasSvg) return;
    var dragStart = null;

    atlasSvg.addEventListener("pointerdown", function (event) {
      if (event.target.closest(".country-label") || event.target.closest(".beetle-point")) return;
      actions.closePointPopup();
      atlasSvg.setPointerCapture(event.pointerId);
      atlasSvg.classList.add("is-dragging");
      dragStart = {
        x: event.clientX,
        y: event.clientY,
        panX: actions.getPanState().panX,
        panY: actions.getPanState().panY,
      };
    });

    atlasSvg.addEventListener("pointermove", function (event) {
      if (!dragStart) return;
      actions.setPanFromDrag(dragStart, event.clientX, event.clientY);
    });

    atlasSvg.addEventListener("pointerup", function () {
      dragStart = null;
      atlasSvg.classList.remove("is-dragging");
    });

    atlasSvg.addEventListener("pointerleave", function () {
      dragStart = null;
      atlasSvg.classList.remove("is-dragging");
    });
  }

  // Verdrahtet Zoom, Scroll-Zoom und Drag-Pan fuer die SVG-Karte.
  function bindMapInteraction(ctx) {
    var elements = readElements(ctx);
    var actions = readActions(ctx);
    bindMapZoomButtons(elements, actions);
    bindMapWheel(elements.atlasSvg, actions);
    bindMapDrag(elements.atlasSvg, actions);
  }

  // Verknuepft den globalen Reset-Button mit der zentralen Reset-Logik.
  function bindResetActions(ctx) {
    var elements = readElements(ctx);
    var actions = readActions(ctx);
    if (!elements.resetButton || typeof actions.resetAllFilters !== "function") return;
    elements.resetButton.addEventListener("click", ctx.actions.resetAllFilters);
  }

  // Bindet den Ergebnis-Modus (Featured vs Stoeber) an die Datenlogik.
  function bindResultModeToggle(ctx) {
    var elements = readElements(ctx);
    var actions = readActions(ctx);
    if (typeof actions.setResultMode !== "function") return;

    if (elements.featuredModeButton) {
      elements.featuredModeButton.addEventListener("click", function () {
        actions.setResultMode("featured");
      });
    }

    if (elements.browseModeButton) {
      elements.browseModeButton.addEventListener("click", function () {
        actions.setResultMode("browse", { forceRefresh: true });
      });
    }
  }

  // Initialisiert die UI-Interaktionen des Hauptscreens in definierter Reihenfolge.
  function init(ctx) {
    if (!ctx || !ctx.elements || !ctx.actions) return;
    bindResultListToggle(ctx);
    bindFilterInputs(ctx);
    bindMapInteraction(ctx);
    bindResetActions(ctx);
    bindResultModeToggle(ctx);
  }

  // Verknuepft die InfoWindow-Aktion "Alle Infos" mit der Detailoeffnung.
  function bindInfoWindowDetailsAction(ctx) {
    if (!ctx || typeof ctx.onOpenDetails !== "function") return;
    var btn = document.querySelector(".iw-more");
    if (!btn) return;
    btn.addEventListener("click", function () {
      ctx.onOpenDetails();
    });
  }

  window.AppEvents = {
    init: init,
    bindInfoWindowDetailsAction: bindInfoWindowDetailsAction,
  };
})();
