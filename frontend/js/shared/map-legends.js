(function () {
  "use strict";

  var ELEVATION_ROWS = [
    { key: "4500_plus", color: "#c4c5cc", label: "&gt; 4500 m" },
    { key: "3000_4500", color: "#b89e7e", label: "3000&ndash;4500 m" },
    { key: "2000_3000", color: "#c1a27c", label: "2000&ndash;3000 m" },
    { key: "1000_2000", color: "#d8c8a4", label: "1000&ndash;2000 m" },
    { key: "500_1000", color: "#e7e5c9", label: "500&ndash;1000 m" },
    { key: "100_500", color: "#cee5b9", label: "100&ndash;500 m" },
    { key: "0_100", color: "#aecfa4", label: "0&ndash;100 m" },
  ];

  var CLIMATE_GROUPS = [
    {
      code: "A",
      title: "Tropisch",
      rows: [
        { code: "Af", color: "#006400", label: "Af Regenwald" },
        { code: "Am", color: "#228B22", label: "Am Monsun" },
        { code: "Aw", color: "#96D26C", label: "Aw Savanne" },
      ],
    },
    {
      code: "B",
      title: "Arid",
      rows: [
        { code: "BWh", color: "#FF4500", label: "BWh W&uuml;ste hei&szlig;" },
        { code: "BWk", color: "#FF8C69", label: "BWk W&uuml;ste kalt" },
        { code: "BSh", color: "#F5A623", label: "BSh Steppe hei&szlig;" },
        { code: "BSk", color: "#F5DCA0", label: "BSk Steppe kalt" },
      ],
    },
    {
      code: "C",
      title: "Gem&auml;&szlig;igt",
      rows: [
        { code: "Csa", color: "#FFFF00", label: "Csa tr. Sommer, hei&szlig;" },
        { code: "Csb", color: "#D4D400", label: "Csb tr. Sommer, warm" },
        { code: "Csc", color: "#AAAA00", label: "Csc tr. Sommer, k&uuml;hl" },
        { code: "Cwa", color: "#AAFFAA", label: "Cwa tr. Winter, hei&szlig;" },
        { code: "Cwb", color: "#78C878", label: "Cwb tr. Winter, warm" },
        { code: "Cwc", color: "#449944", label: "Cwc tr. Winter, k&uuml;hl" },
        { code: "Cfa", color: "#C8FF50", label: "Cfa feucht, hei&szlig;" },
        { code: "Cfb", color: "#78FF50", label: "Cfb feucht, warm" },
        { code: "Cfc", color: "#40C800", label: "Cfc feucht, k&uuml;hl" },
      ],
    },
    {
      code: "D",
      title: "Kalt",
      rows: [
        { code: "Dsb", color: "#CC00CC", label: "Dsb tr. Sommer, warm" }, 
        { code: "Dsc", color: "#990099", label: "Dsc tr. Sommer, k&uuml;hl" },
        { code: "Dfb", color: "#38CCFF", label: "Dfb feucht, warm" },
        { code: "Dfc", color: "#0088AA", label: "Dfc feucht, k&uuml;hl" },
      ],
    },
    {
      code: "E",
      title: "Polar",
      rows: [
        { code: "ET", color: "#B0B0B0", label: "ET Tundra" }, 
        { code: "EF", color: "#808080", label: "EF Eis" },
      ],
    },
  ];

  var VEGETATION_ROWS = [
    { key: "tree_cover", color: "#006400", label: "Tropischer Regenwald" },
    { key: "tree_cover", color: "#55A857", label: "Tropischer Trockenwald" },
    { key: "tree_cover", color: "#2E8B57", label: "Tropischer Nadelwald" },
    { key: "tree_cover", color: "#8B9B2E", label: "Gem&auml;&szlig;igter Laubwald" },
    { key: "tree_cover", color: "#556B2F", label: "Gem&auml;&szlig;igter Nadelwald" },
    { key: "tree_cover", color: "#1E5C3A", label: "Borealer Wald / Taiga" },
    { key: "grassland", color: "#C8B400", label: "Tropisches Grasland / Savanne" },
    { key: "grassland", color: "#C8D250", label: "Gem&auml;&szlig;tes Grasland" },
    { key: "wetland", color: "#00CED1", label: "&Uuml;berschwemmtes Grasland" },
    { key: "grassland", color: "#8B7355", label: "Gebirgs-Grasland" },
    { key: "moss_lichen", color: "#B0C4DE", label: "Tundra" },
    { key: "shrubland", color: "#D4A84B", label: "Mittelmeervegetation" },
    { key: "bare_sparse", color: "#F5DEB3", label: "W&uuml;ste / Trockengebiete" },
    { key: "mangroves", color: "#20B2AA", label: "Mangroven" },
  ];

  // Holt ein DOM-Element per ID.
  function byId(id) {
    return document.getElementById(id);
  }

  // Rendert nur dann HTML, wenn das Ziel-Element existiert.
  function setLegendHtml(elementId, html) {
    var el = byId(elementId);
    if (!el) return;
    el.innerHTML = html;
  }

  // Baut einen einzelnen Legendeneintrag mit optionalen Data-Attributen.
  function buildLegendItem(color, label, attrs) {
    var attrText = attrs ? " " + attrs : "";
    return '<li' + attrText + '><span class="legend-swatch" style="background:' + color + '"></span> ' + label + "</li>";
  }

  // Liefert den gemeinsamen "Alle anzeigen"-Eintrag fuer interaktive Legenden.
  function buildAllItem() {
    return '<li data-legend-all="true" class="is-active">Alle anzeigen</li>';
  }

  // Baut die Hoehenlegende als HTML-Block.
  function buildElevationLegendHtml(interactive) {
    var items = ELEVATION_ROWS.map(function (row) {
      var attrs = interactive ? 'data-elevation="' + row.key + '"' : "";
      return buildLegendItem(row.color, row.label, attrs);
    });

    if (interactive) {
      items.unshift(buildAllItem());
    }

    var source = interactive
      ? '<p style="font-size:0.7rem;color:#888;margin-top:0.4rem">&copy; OpenTopoMap (CC-BY-SA)</p>'
      : "";

    return [
      '<p class="legend-title">H&ouml;he &uuml;. NN</p>',
      '<ul class="legend-list">',
      items.join("\n"), "</ul>", source,
    ].join("\n");
  }

  // Baut einen Klimagruppenblock inklusive Eintraegen.
  function buildClimateGroupHtml(group, interactive) {
    var items = group.rows.map(function (row) {
      var attrs = interactive
        ? 'data-filter-climate="' + row.code + '" data-climate-group="' + group.code + '"'
        : "";
      return buildLegendItem(row.color, row.label, attrs);
    });

    return [
      '<div class="legend-group">',
      '  <p class="legend-group-title">' + group.code + " &mdash; " + group.title + "</p>",
      '  <ul class="legend-list">',
      items.join("\n"),"  </ul>", "</div>",
    ].join("\n");
  }

  // Baut die komplette Klimalegende.
  function buildClimateLegendHtml(interactive) {
    var topAll = interactive
      ? ['<ul class="legend-list legend-list-all">', '  ' + buildAllItem(), "</ul>"].join("\n")
      : "";
    var groups = CLIMATE_GROUPS.map(function (group) {
      return buildClimateGroupHtml(group, interactive);
    }).join("\n");

    return [
      '<p class="legend-title">K&ouml;ppen-Geiger Klimazonen</p>', topAll,
      groups, '<p style="font-size:0.7rem;color:#888;margin-top:0.4rem">Beck et al. (2023), CC-BY 4.0</p>',
    ].join("\n");
  }

  // Baut die Vegetationslegende.
  function buildVegetationLegendHtml(interactive) {
    var items = VEGETATION_ROWS.map(function (row) {
      var attrs = interactive ? 'data-filter-vegetation="' + row.key + '"' : "";
      return buildLegendItem(row.color, row.label, attrs);
    });

    if (interactive) {
      items.unshift(buildAllItem());
    }

    return [
      '<p class="legend-title">Vegetationszonen</p>',
      '<ul class="legend-list">',
      items.join("\n"),
      "</ul>",
      '<p style="font-size:0.7rem;color:#888;margin-top:0.4rem">WWF Terrestrial Ecoregions</p>',
    ].join("\n");
  }

  // Rendert die interaktiven Legenden auf der Startseite.
  function renderIndexLegends() {
    setLegendHtml("elevationLegend", buildElevationLegendHtml(true));
    setLegendHtml("climateLegend", buildClimateLegendHtml(true));
    setLegendHtml("vegetationLegend", buildVegetationLegendHtml(true));
  }

  // Rendert die statischen Legenden auf der Detailseite.
  function renderDetailLegends() {
    setLegendHtml("detailElevationLegend", buildElevationLegendHtml(false));
    setLegendHtml("detailClimateLegend", buildClimateLegendHtml(false));
    setLegendHtml("detailVegetationLegend", buildVegetationLegendHtml(false));
  }

  window.BEETLE_LEGENDS = {
    renderIndexLegends: renderIndexLegends, renderDetailLegends: renderDetailLegends,
  };
})();
