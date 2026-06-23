(function () {
  "use strict";

  // Fuehrt die zugehoerige Logik fuer diese Funktion aus.
  function soilBandLabel(value, labels) {
    if (!value || value === "unknown") return null;
    return (labels && labels[value]) || value;
  }

  // Fuehrt die zugehoerige Logik fuer diese Funktion aus.
  function soilTypeLabel(value, labels) {
    if (!value || value === "unknown") return null;
    return (labels && labels[value]) || value;
  }

  // Formatiert den Wert fuer die Anzeige.
  function formatSoilPhFromRecord(record, labels) {
    var phValue = record && record.meta && record.meta.location && record.meta.location.soilPh;
    var phBand = soilBandLabel(
      record && record.meta && record.meta.location && record.meta.location.soilPhBand, labels
    );
    var soilType = soilTypeLabel(record && record.soil, labels);
    var numeric = Number(phValue);
    if (Number.isFinite(numeric)) {
      var phText = phBand ? numeric.toFixed(1) + " (" + phBand + ")" : numeric.toFixed(1);
      if (soilType && phBand && soilType !== phBand) return phText + " · Boden: " + soilType;
      return soilType ? phText + " · Boden: " + soilType : phText;
    }
    if (phBand) {
      if (soilType && soilType !== phBand) return phBand + " · Boden: " + soilType;
      return soilType ? phBand + " · Boden: " + soilType : phBand;
    }
    if (soilType) return "unbekannt · Boden: " + soilType;
    return "unbekannt";
  }

  window.BeetleFormatters = {
    soilBandLabel: soilBandLabel, soilTypeLabel: soilTypeLabel, formatSoilPhFromRecord: formatSoilPhFromRecord,
  };
})();
