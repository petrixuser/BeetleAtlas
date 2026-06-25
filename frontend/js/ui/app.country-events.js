(function () {
  "use strict";

  // Liefert das angeklickte Laenderlabel-Element oder null.
  function findCountryLabel(event) {
    return event && event.target && event.target.closest
      ? event.target.closest(".country-label")
      : null;
  }

  // Liefert das angeklickte Kaeferpunkt-Element oder null.
  function findBeetlePoint(event) {
    return event && event.target && event.target.closest
      ? event.target.closest(".beetle-point")
      : null;
  }

  // Reagiert auf Klicks auf Laenderlabel und oeffnet die Sidebar.
  function onCountryLabelClick(ctx, event) {
    var label = findCountryLabel(event);
    if (!label) return;
    ctx.closePointPopup();
    if (typeof ctx.selectCountryFromMap === "function") {
      ctx.selectCountryFromMap(label.dataset.country);
    }
    ctx.openCountrySidebar(label.dataset.country);
  }

  // Erlaubt Tastatursteuerung (Enter/Space) fuer Laenderlabel.
  function onCountryLabelKeydown(ctx, event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    var label = findCountryLabel(event);
    if (!label) return;

    event.preventDefault();
    ctx.closePointPopup();
    if (typeof ctx.selectCountryFromMap === "function") {
      ctx.selectCountryFromMap(label.dataset.country);
    }
    ctx.openCountrySidebar(label.dataset.country);
  }

  // Oeffnet den Punkt-Popup fuer den geklickten Kaeferpunkt.
  function onBeetlePointClick(ctx, event) {
    var point = findBeetlePoint(event);
    if (!point) return;
    var beetle = ctx.findBeetleById(point.dataset.id);
    if (!beetle) return;

    ctx.closeCountrySidebar();
    ctx.openPointPopup(beetle, event);
  }

  // Bindet alle Interaktionen fuer Laenderlabel, Kaeferpunkte und Sidebar-Close.
  function bindCountryLayerEvents(ctx) {
    var labelLayer = ctx && ctx.labelLayer;
    var beetleLayer = ctx && ctx.beetleLayer;
    var closeSidebarButton = ctx && ctx.closeSidebarButton;
    if (!labelLayer || !beetleLayer || !closeSidebarButton) return;

    labelLayer.addEventListener("click", function (event) {
      onCountryLabelClick(ctx, event);
    });
    labelLayer.addEventListener("keydown", function (event) {
      onCountryLabelKeydown(ctx, event);
    });
    beetleLayer.addEventListener("click", function (event) {
      onBeetlePointClick(ctx, event);
    });
    closeSidebarButton.addEventListener("click", ctx.closeCountrySidebar);
  }

  // Initialisiert die Country-Interaktionen auf der Karte.
  function init(ctx) {
    bindCountryLayerEvents(ctx);
  }

  window.AppCountryEvents = {
    init: init,
  };
})();
