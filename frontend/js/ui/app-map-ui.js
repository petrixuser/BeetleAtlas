(function () {
  "use strict";

  // Liest den gewuenschten View-Namen aus dem Context.
  function viewName(ctx) {
    return ctx && ctx.view;
  }

  // Ordnet einen View der passenden Legenden-ID zu.
  function legendIdForView(view) {
    if (view === "elevation") return "elevationLegend";
    if (view === "climate") return "climateLegend";
    if (view === "vegetation") return "vegetationLegend";
    return null;
  }

  // Markiert den aktuell ausgewaehlten Kartenmodus in der Toolbar.
  function setViewButtonsActive(ctx) {
    var view = viewName(ctx);
    document.querySelectorAll(".map-view-toggle .toggle-btn").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.view === view);
    });
  }

  // Versteckt alle Karten-Legenden.
  function hideAllLegends() {
    document.querySelectorAll(".map-legend").forEach(function (el) {
      el.classList.add("is-hidden");
    });
  }

  // Blendet nur die Legende ein, die zum aktuellen View passt.
  function showLegendForView(ctx) {
    var id = legendIdForView(viewName(ctx));
    if (!id) return;

    var el = document.getElementById(id);
    if (el) el.classList.remove("is-hidden");
  }

  var ui = {setViewButtonsActive: setViewButtonsActive, hideAllLegends: hideAllLegends, showLegendForView: showLegendForView,};

  window.UI = ui;
  window.AppMapUI = ui;
})();
