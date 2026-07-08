// Persistenz-Hilfsfunktionen der Startseite (Session-State).
// Ausgelagert aus core/app.js; nutzt die dort definierten globalen Zustaende und
// Filter-Elemente sowie readMainState/setSelected* aus app.selection-filters.js.
// Als klassisches Script teilen sich diese Datei und app.js denselben globalen
// Gueltigkeitsbereich.

// Speichert den aktuellen Filter-, Listen- und Kartenzustand in der Session.
function saveMainState() {
  try {
    const climateParam = getClimateParamValue();
    const vegetationParam = getVegetationParamValue();
    const elevationParam = getElevationParamValue();
    const state = {
      search: searchInput.value,
      country: countryFilter.value,
      climate: climateParam,
      vegetation: vegetationParam,
      elevation: elevationParam,
      soilPhBand: soilPhBandFilter.value,
      temperatureBand: temperatureBandFilter.value,
      precipitationBand: precipitationBandFilter.value,
      dataQuality: dataQualityFilter.value,
      year: yearFilter.value,
      image: imageFilter.value,
      resultMode: selectedResultMode,
      offset: listOffset,
      expandedIds: Array.from(expandedIds),
      pinnedBeetleId: pinnedBeetle ? String(pinnedBeetle.id) : pendingPinnedBeetleId,
      mapView: currentView,
    };
    sessionStorage.setItem(MAIN_STATE_KEY, JSON.stringify(state));
  } catch {
  }
}

// Stellt Filter-, Listen- und Kartenzustand aus der Session wieder her.
function restoreMainState() {
  const state = readMainState();
  if (!state || typeof state !== "object") return;

  if (typeof state.search === "string") searchInput.value = state.search;
  if (typeof state.country === "string" && countryFilter.querySelector(`option[value="${state.country}"]`)) countryFilter.value = state.country;
  if (typeof state.climate === "string") setSelectedClimateCodes(state.climate.split(","));
  if (typeof state.vegetation === "string") setSelectedVegetationCodes(state.vegetation.split(","));
  if (typeof state.elevation === "string") {
    setSelectedElevations(state.elevation.split(","));
  }
  if (typeof state.soilPhBand === "string") soilPhBandFilter.value = state.soilPhBand;
  if (typeof state.temperatureBand === "string") temperatureBandFilter.value = state.temperatureBand;
  if (typeof state.precipitationBand === "string") precipitationBandFilter.value = state.precipitationBand;
  if (typeof state.dataQuality === "string") dataQualityFilter.value = state.dataQuality;
  if (typeof state.year === "string") yearFilter.value = state.year;
  if (typeof state.image === "string") imageFilter.value = state.image;
  if (state.resultMode === RESULT_MODE_FEATURED || state.resultMode === RESULT_MODE_BROWSE) {
    selectedResultMode = state.resultMode;
  }
  if (Number.isFinite(Number(state.offset))) {
    listOffset = Math.max(0, Number(state.offset));
  }

  expandedIds.clear();
  if (Array.isArray(state.expandedIds)) {
    state.expandedIds.forEach((id) => {
      if (id !== null && id !== undefined) expandedIds.add(String(id));
    });
  }

  pendingPinnedBeetleId = state.pinnedBeetleId ? String(state.pinnedBeetleId) : null;
  pendingMapView = state.mapView ? String(state.mapView) : null;
}

// Stellt einen vorgemerkten, gepinnten Kaefer nach dem Laden wieder her.
function restorePinnedBeetleIfNeeded() {
  if (!pendingPinnedBeetleId || pinnedBeetle) return;
  const found = beetles.find((b) => String(b.id) === pendingPinnedBeetleId);
  if (!found) return;
  pinnedBeetle = found;
  expandedIds.add(String(found.id));
  pendingPinnedBeetleId = null;
}
