// Auswahl- und Filter-Hilfsfunktionen der Startseite.

// Prueft, ob ein Wert eine gueltige Hoehenstufe ist, sonst null.
function normalizeElevationKey(value) {
  return ELEVATION_KEYS.includes(value) ? value : null;
}

// Gibt die aktuell ausgewaehlten Hoehenstufen in stabiler Reihenfolge zurueck.
function getSelectedElevationKeys() {
  return ELEVATION_KEYS.filter((key) => selectedElevationKeys.has(key));
}

// Uebernimmt Hoehenstufen in den Zustand und synchronisiert das Select-Element.
function setSelectedElevations(keys) {
  selectedElevationKeys.clear();
  (keys || []).forEach((key) => {
    const normalized = normalizeElevationKey(String(key || "").trim());
    if (normalized) selectedElevationKeys.add(normalized);
  });
  elevationFilter.value = selectedElevationKeys.size === 1 ? getSelectedElevationKeys()[0] : "all";
}

// Gibt die Hoehenauswahl als API-Parameterwert zurueck.
function getElevationParamValue() {
  const keys = getSelectedElevationKeys();
  if (!keys.length) return "all";
  if (keys.length === 1) return keys[0];
  return keys.join(",");
}

// Uebernimmt ausgewaehlte Klimacodes in Zustand und Select-Wert.
function setSelectedClimateCodes(codes) {
  selectedClimateCodes.clear();
  (codes || []).forEach((code) => {
    const value = String(code || "").trim();
    if (value && value !== "all") selectedClimateCodes.add(value);
  });
  climateFilter.value = selectedClimateCodes.size === 1 ? Array.from(selectedClimateCodes)[0] : "all";
}

// Uebernimmt ausgewaehlte Vegetationscodes in Zustand und Select-Wert.
function setSelectedVegetationCodes(codes) {
  selectedVegetationCodes.clear();
  (codes || []).forEach((code) => {
    const value = String(code || "").trim();
    if (value && value !== "all") selectedVegetationCodes.add(value);
  });
  vegetationFilter.value = selectedVegetationCodes.size === 1 ? Array.from(selectedVegetationCodes)[0] : "all";
}

// Gibt alle aktiv gewaehlten Klimacodes als Array zurueck.
function getSelectedClimateCodes() {
  return Array.from(selectedClimateCodes);
}

// Gibt alle aktiv gewaehlten Vegetationscodes als Array zurueck.
function getSelectedVegetationCodes() {
  return Array.from(selectedVegetationCodes);
}

// Liefert den Klima-Querywert aus Multi-Select oder Dropdown-Fallback.
function getClimateParamValue() {
  const values = getSelectedClimateCodes();
  if (values.length) return values.join(",");
  return climateFilter.value || "all";
}

// Liefert den Vegetations-Querywert aus Multi-Select oder Dropdown-Fallback.
function getVegetationParamValue() {
  const values = getSelectedVegetationCodes();
  if (values.length) return values.join(",");
  return vegetationFilter.value || "all";
}

// Liefert die aktiven Werte oder einen gueltigen Fallback fuer Kombinationsabfragen.
function getFilterValueList(setValues, fallbackValue) {
  if (setValues.length) return setValues;
  if (fallbackValue && fallbackValue !== "all") return [fallbackValue];
  return ["all"];
}

// Erzeugt alle relevanten Filterkombinationen fuer Backend-Abfragen.
function buildFilterCombinations() {
  const climateValues = [getClimateParamValue()];
  const vegetationValues = [getVegetationParamValue()];
  const elevationValues = getFilterValueList(getSelectedElevationKeys(), elevationFilter.value);
  const combos = [];
  climateValues.forEach((climate) => {
    vegetationValues.forEach((vegetation) => {
      elevationValues.forEach((elevation) => {
        combos.push({ climate, vegetation, elevation });
      });
    });
  });
  return combos;
}

// Liest den gespeicherten Hauptzustand aus der Session (fehlertolerant).
function readMainState() {
  try {
    const raw = sessionStorage.getItem(MAIN_STATE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
