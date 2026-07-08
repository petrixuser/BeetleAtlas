// Legenden-Hilfsfunktionen: liest Farben und Codes aus Legendeneintraegen und
// prueft, ob die aktive Subtyp-Auswahl genau einer Klima-Hauptgruppe entspricht.
(function () {
  "use strict";

  // Liest die Farbe eines Legendeneintrags aus Swatch-Styles robust aus.
  function legendItemColor(li, normalizeLegendColor) {
    var swatch = li && li.querySelector ? li.querySelector(".legend-swatch") : null;
    if (!swatch) return "";
    var inlineStyle = swatch.getAttribute("style") || "";
    var match = inlineStyle.match(/background\s*:\s*([^;]+)/i);
    if (match && match[1]) return normalizeLegendColor(match[1]);
    return normalizeLegendColor(swatch.style.backgroundColor || "");
  }

  // Ermittelt den geklickten Legendeneintrag aus einem Event.
  function legendItemFromEvent(event) {
    var rawTarget = event ? event.target : null;
    var target = rawTarget instanceof Element ? rawTarget : rawTarget && rawTarget.parentElement;
    if (!target || !target.closest) return null;
    return target.closest("li");
  }

  // Leitet den Klima-Hauptcode (A-E) aus einem Legendeneintrag ab.
  function climateLegendGroupCode(li) {
    if (!li || !li.getAttribute) return "";
    var explicit = String(li.getAttribute("data-climate-group") || "").trim().toUpperCase();
    if (/^[A-E]$/.test(explicit)) return explicit;
    var code = String(li.getAttribute("data-filter-climate") || "").trim().toUpperCase();
    if (/^[A-E]$/.test(code)) return code;
    if (/^[A-E]/.test(code)) return code[0];
    return "";
  }

  // Prueft, ob alle aktiven Subtypen genau zu einer Klima-Hauptgruppe gehoeren.
  function areAllSubtypesOfSingleClimateGroupSelected(ctx) {
    var root = ctx && ctx.root;
    var activeClimateLegendColors = (ctx && ctx.activeClimateLegendColors) || new Set();
    var legendItemColorFn = (ctx && ctx.legendItemColor) || function () { return ""; };
    var climateLegendGroupCodeFn = (ctx && ctx.climateLegendGroupCode) || function () { return ""; };
    if (!root) return false;

    var activeGroupCodes = new Set(
      Array.from(root.querySelectorAll("li[data-filter-climate]"))
        .filter(function (li) {
          var color = legendItemColorFn(li);
          return color && activeClimateLegendColors.has(color);
        })
        .map(function (li) { return climateLegendGroupCodeFn(li); })
        .filter(function (code) { return /^[A-E]$/.test(code); })
    );

    if (activeGroupCodes.size !== 1) return false;
    var groupCode = Array.from(activeGroupCodes)[0];
    var groupColors = new Set(
      Array.from(root.querySelectorAll("li[data-filter-climate]"))
        .filter(function (li) { return climateLegendGroupCodeFn(li) === groupCode; })
        .map(function (li) { return legendItemColorFn(li); })
        .filter(Boolean)
    );

    if (!groupColors.size || !activeClimateLegendColors.size) return false;
    if (activeClimateLegendColors.size < groupColors.size) return false;
    return Array.from(groupColors).every(function (color) { return activeClimateLegendColors.has(color); });
  }

  window.AppLegendHelpers = {
    legendItemColor: legendItemColor,legendItemFromEvent: legendItemFromEvent,
    climateLegendGroupCode: climateLegendGroupCode,
    areAllSubtypesOfSingleClimateGroupSelected: areAllSubtypesOfSingleClimateGroupSelected,
  };
})();
