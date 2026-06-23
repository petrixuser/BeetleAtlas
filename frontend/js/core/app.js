
let beetles = [];

// ===== App state =====

let totalBeetles = 0;
const BEETLE_FETCH_LIMIT = 200;
const API_MAX_OFFSET = 200000;
const MAIN_STATE_KEY = "beetleatlas:main-state:v1";
const LIST_PAGE_SIZE = BEETLE_FETCH_LIMIT;
let pendingPinnedBeetleId = null;
let pendingMapView = null;
let listOffset = 0;
let latestApplyToken = 0;
const RESULT_MODE_FEATURED = "featured";
const RESULT_MODE_BROWSE = "browse";
let selectedResultMode = RESULT_MODE_FEATURED;

const ELEVATION_KEYS = ["0_100", "100_500", "500_1000", "1000_2000", "2000_3000", "3000_4500", "4500_plus"];
const selectedElevationKeys = new Set();
const selectedClimateCodes = new Set();
const selectedVegetationCodes = new Set();
const {
  climateLabel = (code) => (code ?? "Unbekannt"),
  vegetationLabel = (code) => (code ?? "Unbekannt"),
  COUNTRY_NAME_TO_ISO = {},
  ISO_TO_COUNTRY_NAME = {},
  labelPositions = {},
  tinyLabels = new Set(),
  SOIL_PH_BAND_LABELS = {},
} = window.AppCatalog || {};
const AppPageUtils = window.AppPageUtils || {};

// Kapselt UI-Aufrufe fuer Kartenansicht/Legenden, damit Core-Logik schlank bleibt.
function callMapUi(method, fallback, arg) {
  const ui = window.UI || window.AppMapUI;
  if (!ui || typeof ui[method] !== "function") return fallback;
  return ui[method](arg);
}

// During startup, map scripts may initialize after core code paths run.
// Access map instance defensively to avoid ReferenceError races.
function getGoogleMapInstanceSafe() {
  return (typeof googleMapInstance !== "undefined") ? googleMapInstance : null;
}

// ===== Selection and filter helpers =====

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

// ===== Persistence helpers =====

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

// Baut den Querystring fuer die aktuelle Kaeferabfrage.
function buildBeetleQuery(overrides = null) {
  const applied = overrides || {};
  const params = new URLSearchParams();
  const search = searchInput.value.trim();
  if (search) params.set("q", search);
  if (countryFilter.value !== "all") params.set("country", countryFilter.value);
  const climateParam = applied.climate || getClimateParamValue();
  const vegetationParam = applied.vegetation || getVegetationParamValue();
  const elevationParam = applied.elevation || getElevationParamValue();
  if (climateParam !== "all") params.set("climate", climateParam);
  if (vegetationParam !== "all") params.set("vegetation", vegetationParam);
  if (elevationParam !== "all") params.set("elevation", elevationParam);
  if (soilPhBandFilter.value !== "all") params.set("soil_ph_band", soilPhBandFilter.value);
  if (temperatureBandFilter.value !== "all") params.set("temperature_band", temperatureBandFilter.value);
  if (precipitationBandFilter.value !== "all") params.set("precipitation_band", precipitationBandFilter.value);
  if (dataQualityFilter.value !== "all") params.set("event_date_quality", dataQualityFilter.value);
  if (yearFilter.value.trim()) params.set("observed_year", yearFilter.value.trim());
  if (imageFilter.value === "with_images") params.set("has_image", "true");
  if (imageFilter.value === "no_images") params.set("has_image", "false");
  params.set("limit", String(BEETLE_FETCH_LIMIT));
  params.set("compact", "1");
  const offset = Number.isFinite(Number(applied.offset)) ? Number(applied.offset) : listOffset;
  params.set("offset", String(Math.max(0, offset)));
  return params.toString();
}

// Prueft, ob aktuell mindestens ein Filter aktiv gesetzt ist.
function hasActiveFilters() {
  return (
    searchInput.value.trim() !== "" ||
    countryFilter.value !== "all" ||
    climateFilter.value !== "all" ||
    vegetationFilter.value !== "all" ||
    selectedClimateCodes.size > 0 ||
    selectedVegetationCodes.size > 0 ||
    selectedElevationKeys.size > 0 ||
    soilPhBandFilter.value !== "all" ||
    temperatureBandFilter.value !== "all" ||
    precipitationBandFilter.value !== "all" ||
    dataQualityFilter.value !== "all" ||
    yearFilter.value.trim() !== "" ||
    imageFilter.value !== "all"
  );
}

let featuredMode = false;
const beetlesCache = new Map();
let browseBeetlesCache = null;

function shuffleList(items) {
  const list = Array.isArray(items) ? items.slice() : [];
  for (let i = list.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = list[i];
    list[i] = list[j];
    list[j] = tmp;
  }
  return list;
}

async function loadBrowseBeetles(forceRefresh, requestToken = 0) {
  const browseCacheKey = `${buildBeetleQuery()}|offset=${listOffset}`;
  if (!forceRefresh && browseBeetlesCache && browseBeetlesCache.key === browseCacheKey) {
    beetles = browseBeetlesCache.items;
    totalBeetles = browseBeetlesCache.total;
    return;
  }

  if (window.API_BASE_URL) {
    try {
      const params = new URLSearchParams(buildBeetleQuery());
      params.set("limit", String(BEETLE_FETCH_LIMIT));
      params.set("offset", String(Math.min(Math.max(0, listOffset), API_MAX_OFFSET)));
      params.set("sort_by", "id");
      params.set("sort_dir", "asc");

      const res = await fetch(`${window.API_BASE_URL}/api/beetles?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (requestToken && requestToken !== latestApplyToken) return;
      beetles = data.items ?? [];
      totalBeetles = Number(data.total || beetles.length);
      browseBeetlesCache = { key: browseCacheKey, items: beetles, total: totalBeetles };
      return;
    } catch (error) {
      console.error("Stoeber-Modus konnte nicht aus dem Backend geladen werden:", error);
      // Do not silently switch to demo data when API mode is active.
      beetles = Array.isArray(beetles) ? beetles : [];
      totalBeetles = Number.isFinite(totalBeetles) ? totalBeetles : beetles.length;
      return;
    }
  }

  beetles = (window.DEMO_BEETLES ?? []).slice(0, BEETLE_FETCH_LIMIT);
  totalBeetles = beetles.length;
  browseBeetlesCache = { key: browseCacheKey, items: beetles, total: totalBeetles };
}

// ===== Data loading =====

async function loadBeetles(options = {}) {
  const forceBrowseRefresh = !!options.forceBrowseRefresh;
  const requestToken = Number(options.requestToken || 0);
  const activeFilters = hasActiveFilters();

  if (!activeFilters && selectedResultMode === RESULT_MODE_FEATURED && (window.FEATURED_BEETLES?.length)) {
    featuredMode = true;
    beetles = window.FEATURED_BEETLES;
    totalBeetles = beetles.length;
    return;
  }

  if (selectedResultMode === RESULT_MODE_BROWSE) {
    featuredMode = false;
    await loadBrowseBeetles(forceBrowseRefresh, requestToken);
    return;
  }

  featuredMode = false;
  try {
    if (window.API_BASE_URL) {
      const combos = buildFilterCombinations();
      if (combos.length <= 1) {
        const query = buildBeetleQuery(combos[0]);
        const cached = beetlesCache.get(query);
        if (cached) {
          beetles = cached.items;
          totalBeetles = cached.total;
          return;
        }
        const res = await fetch(`${window.API_BASE_URL}/api/beetles?${query}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        beetles = data.items ?? [];
        totalBeetles = data.total ?? beetles.length;
        beetlesCache.set(query, { items: beetles, total: totalBeetles });
        return;
      }

      const merged = [];
      const seen = new Set();
      let mergedTotal = 0;

      for (const combo of combos) {
        const query = buildBeetleQuery(combo);
        const cached = beetlesCache.get(query);
        let data;
        if (cached) {
          data = cached;
        } else {
          const res = await fetch(`${window.API_BASE_URL}/api/beetles?${query}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const json = await res.json();
          data = { items: json.items ?? [], total: json.total ?? (json.items ?? []).length };
          beetlesCache.set(query, data);
        }

        mergedTotal += Number(data.total || 0);
        (data.items || []).forEach((item) => {
          const id = String(item?.id ?? "");
          if (!id || seen.has(id)) return;
          seen.add(id);
          merged.push(item);
        });
      }

      beetles = merged;
      totalBeetles = mergedTotal || merged.length;
    } else {
      // Mock-Modus: Demo-Daten aus demo-beetles.js
      beetles = window.DEMO_BEETLES ?? [];
      totalBeetles = beetles.length;
    }
  } catch (error) {
    console.error("Kaeferdaten konnten nicht geladen werden:", error);
    // Keep last server state; no demo fallback in API mode.
    beetles = Array.isArray(beetles) ? beetles : [];
    totalBeetles = Number.isFinite(totalBeetles) ? totalBeetles : beetles.length;
  }
}

// Zeigt einen temporaeren Ladezustand fuer die Ergebnisliste.
function showLoadingState() {
  resultHeading.textContent = "Kaeferdaten werden geladen ...";
  resultList.innerHTML = `
    <div class="empty-state">Kaeferdaten werden geladen ...</div>
  `;
  if (resultPagerTop) resultPagerTop.innerHTML = "";
  if (resultPager) resultPager.innerHTML = "";
}

// Wird bei jeder Filteraenderung aufgerufen. Im Backend-Modus wird neu geladen
// (serverseitige Filterung), im Demo-Modus reicht ein erneutes Rendern.
async function applyFilters(options = {}) {
  const forceBrowseRefresh = !!options.forceBrowseRefresh;
  const keepPage = !!options.keepPage;
  suppressNextMapRefresh = !!options.suppressMapRefresh;
  const requestedOffset = Number.isFinite(Number(options.pageOffset)) ? Number(options.pageOffset) : 0;
  const applyToken = ++latestApplyToken;
  listOffset = keepPage ? Math.max(0, requestedOffset) : 0;
  // Neue Suche/Filterung -> die per Karten-Pin gewaehlte Karte oben zuruecksetzen.
  if (!keepPage) pinnedBeetle = null;
  lastRenderedMapPointTotal = null;
  mapListBeetles = null;
  subtypeListLoading = false;
  if (climateFilter.value !== "all") {
    setSelectedClimateCodes([climateFilter.value]);
  } else if (selectedClimateCodes.size <= 1) {
    setSelectedClimateCodes([]);
  }
  if (vegetationFilter.value !== "all") {
    setSelectedVegetationCodes([vegetationFilter.value]);
  } else if (selectedVegetationCodes.size <= 1) {
    setSelectedVegetationCodes([]);
  }
  if (elevationFilter.value !== "all") {
    setSelectedElevations([elevationFilter.value]);
  } else if (selectedElevationKeys.size <= 1) {
    setSelectedElevations([]);
  }
  setElevationLegendActiveState();
  updateFilterUI();
  updateResultModeToggle();
  updateCountryHighlight();
  
  const shouldShowLoadingState = window.API_BASE_URL && (
    hasActiveFilters() ||
    selectedResultMode === RESULT_MODE_BROWSE ||
    keepPage ||
    forceBrowseRefresh
  );
  if (shouldShowLoadingState) {
    setListLoading(true);
    showLoadingState();
  } else {
    setListLoading(false);
  }

  if (window.API_BASE_URL && shouldApplySubtypeSpatialFilter()) {
    featuredMode = false;
    beetles = [];
    totalBeetles = 0;
    mapListBeetles = [];
    subtypeListLoading = true;
    render();
    saveMainState();
    if (getGoogleMapInstanceSafe()) {
      scheduleMapPoints();
    } else {
      // Avoid locking result-mode controls when map bootstrap is not ready yet.
      setListLoading(false);
    }
    return;
  }

  try {
    await loadBeetles({ forceBrowseRefresh, requestToken: applyToken });
    if (applyToken !== latestApplyToken) return;
    restorePinnedBeetleIfNeeded();
    render();
    saveMainState();
  } catch (error) {
    if (applyToken !== latestApplyToken) return;
    console.error("Filter konnten nicht vollstaendig angewendet werden:", error);
    beetles = shuffleList(window.DEMO_BEETLES ?? []).slice(0, BEETLE_FETCH_LIMIT);
    totalBeetles = beetles.length;
    render();
    saveMainState();
  } finally {
    if (applyToken === latestApplyToken) setListLoading(false);
  }
}


// Normalisiert Eingabewerte fuer konsistente Verarbeitung.
function normalizeCountryName(value) {
  const fn = AppPageUtils.normalizeCountryName;
  if (fn) return fn(value);
  return String(value || "").trim().replace(/\s+/g, " ");
}

// Uebernimmt ein auf der Karte gewaehltes Land in den Dropdown-Filter.
function selectCountryFromMap(countryName) {
  const normalized = normalizeCountryName(countryName).toUpperCase();
  if (!normalized) return;

  let nextValue = "";
  const isoCode = COUNTRY_NAME_TO_ISO[normalized];
  if (isoCode && countryFilter.querySelector(`option[value="${isoCode}"]`)) {
    nextValue = isoCode;
  } else {
    const options = Array.from(countryFilter.options || []);
    const byLabel = options.find((opt) => {
      const optionName = normalizeCountryName(opt.dataset.countryName || "").toUpperCase();
      return optionName && optionName === normalized;
    });
    nextValue = byLabel ? byLabel.value : "";
  }

  if (!nextValue || countryFilter.value === nextValue) return;
  countryFilter.value = nextValue;
  applyFilters();
}

// Liefert den aktuell ausgewaehlten Laendernamen aus dem Dropdown.
function selectedCountryNameFromFilter() {
  if (!countryFilter || countryFilter.value === "all") return "";
  const selected = countryFilter.selectedOptions && countryFilter.selectedOptions[0];
  const byDataset = selected ? String(selected.dataset.countryName || "") : "";
  if (byDataset) return byDataset;
  return ISO_TO_COUNTRY_NAME[countryFilter.value] || "";
}

// Prueft, ob ein Name dem aktuell gesetzten Laenderfilter entspricht.
function isCountrySelected(countryName) {
  const active = normalizeCountryName(selectedCountryNameFromFilter()).toUpperCase();
  const current = normalizeCountryName(countryName).toUpperCase();
  return Boolean(active && current && active === current);
}

// Markiert das aktiv gefilterte Land in der SVG-Fallback-Karte.
function updateSvgCountryHighlight() {
  const mark = (selector) => {
    document.querySelectorAll(selector).forEach((el) => {
      const name = el.dataset.country || "";
      el.classList.toggle("is-active", isCountrySelected(name));
    });
  };
  mark(".country");
  mark(".country-line");
  mark(".country-label");
}

// Markiert das aktiv gefilterte Land im Google-GeoJSON-Layer.
function updateGoogleCountryHighlight() {
  const mapInstance = getGoogleMapInstanceSafe();
  if (!mapInstance || !mapInstance.data) return;
  mapInstance.data.setStyle((feature) => {
    const name = feature.getProperty("name") || "";
    if (isCountrySelected(name)) {
      return {
        fillColor: "#2f6b47",
        fillOpacity: 0.22,
        strokeColor: "#1f4f34",
        strokeOpacity: 0.9,
        strokeWeight: 1.2,
      };
    }
    return {
      fillOpacity: 0,
      strokeOpacity: 0,
      strokeWeight: 0,
    };
  });
}

// Synchronisiert die aktive Laendermarkierung in beiden Kartenmodi.
function updateCountryHighlight() {
  updateSvgCountryHighlight();
  updateGoogleCountryHighlight();
}

// ===== DOM references =====

function resolveCountryDisplay(entry) {
  const fn = AppPageUtils.resolveCountryDisplay;
  if (!fn) return { labelName: String(entry?.name || entry?.code || ""), iso: "" };
  return fn(entry, { COUNTRY_NAME_TO_ISO, ISO_TO_COUNTRY_NAME });
}


let geoBounds;
let zoom = 1;
let panX = 0;
let panY = 0;
let dragStart = null;

const searchInput = document.querySelector("#searchInput");
const countryFilter = document.querySelector("#countryFilter");
const climateFilter = document.querySelector("#climateFilter");
const vegetationFilter = document.querySelector("#vegetationFilter");
const elevationFilter = document.querySelector("#elevationFilter");
const soilPhBandFilter = document.querySelector("#soilPhBandFilter");
const temperatureBandFilter = document.querySelector("#temperatureBandFilter");
const precipitationBandFilter = document.querySelector("#precipitationBandFilter");
const dataQualityFilter = document.querySelector("#dataQualityFilter");
const yearFilter = document.querySelector("#yearFilter");
const imageFilter = document.querySelector("#imageFilter");
const resetButton = document.querySelector("#resetButton");
const filterToggle = document.querySelector("#filterToggle");
const filterPanel = document.querySelector("#filterPanel");
const filterBadge = document.querySelector("#filterBadge");
const activeFilters = document.querySelector("#activeFilters");
const resultHeading = document.querySelector("#resultHeading");
const resultList = document.querySelector("#resultList");
const resultPagerTop = document.querySelector("#resultPagerTop");
const resultPager = document.querySelector("#resultPager");
const featuredModeButton = document.querySelector("#featuredModeButton");
const browseModeButton = document.querySelector("#browseModeButton");
let lastRenderedMapPointCount = 0;
let lastRenderedMapPointTotal = null;
let mapListBeetles = null;
let syncingListFromMap = false;
let subtypeListLoading = false;
let isListLoading = false;
let suppressNextMapRefresh = false;

function setListLoading(loading) {
  isListLoading = Boolean(loading);
  updateResultModeToggle();
}

function updateResultModeToggle() {
  const browseActive = selectedResultMode === RESULT_MODE_BROWSE;
  const controlsDisabled = isListLoading;
  if (featuredModeButton) {
    featuredModeButton.classList.toggle("is-active", selectedResultMode === RESULT_MODE_FEATURED);
    featuredModeButton.setAttribute("aria-pressed", String(selectedResultMode === RESULT_MODE_FEATURED));
    featuredModeButton.disabled = controlsDisabled;
  }
  if (browseModeButton) {
    browseModeButton.classList.toggle("is-active", browseActive);
    browseModeButton.setAttribute("aria-pressed", String(browseActive));
    browseModeButton.disabled = controlsDisabled;
  }
}

function setResultMode(mode, options = {}) {
  if (mode !== RESULT_MODE_FEATURED && mode !== RESULT_MODE_BROWSE) return;
  const forceRefresh = !!options.forceRefresh;
  const changed = selectedResultMode !== mode;
  selectedResultMode = mode;
  if (changed) listOffset = 0;
  if (mode !== RESULT_MODE_BROWSE) browseBeetlesCache = null;
  updateResultModeToggle();
  if (!changed && !forceRefresh) {
    saveMainState();
    return;
  }
  const keepPage = mode === RESULT_MODE_BROWSE && forceRefresh;
  applyFilters({
    forceBrowseRefresh: mode === RESULT_MODE_BROWSE,
    keepPage,
    pageOffset: listOffset,
    suppressMapRefresh: keepPage,
  });
}

// ===== Result heading helpers =====

function activeSubtypeLabel() {
  const legendId = currentView === "climate"
    ? "climateLegend"
    : (currentView === "vegetation" ? "vegetationLegend" : null);
  if (!legendId) return "Subtyp";
  const root = document.getElementById(legendId);
  if (!root) return "Subtyp";
  const activeItems = Array.from(root.querySelectorAll("li.is-active:not([data-legend-all])"));
  if (activeItems.length === 1) return activeItems[0].textContent.trim();
  if (activeItems.length > 1) return `${activeItems.length} Subtypen`;
  return "Subtyp";
}

// Baut den Kontexttext fuer aktive Klima-/Vegetationsfilter im Ergebniskopf.
function activeFilterContextLabel() {
  const parts = [];
  const climates = getSelectedClimateCodes();
  const vegetations = getSelectedVegetationCodes();
  if (climates.length) {
    const climateText = climates.map((code) => climateLabel(code)).join(", ");
    parts.push(`Klima: ${climateText}`);
  }
  if (vegetations.length) {
    const vegetationText = vegetations.map((code) => vegetationLabel(code)).join(", ");
    parts.push(`Vegetation: ${vegetationText}`);
  }
  if (shouldApplySubtypeSpatialFilter()) {
    const group = currentView === "climate" ? "Klima-Untergruppe" : "Vegetations-Untergruppe";
    parts.push(`${group}: ${activeSubtypeLabel()}`);
  }
  return parts.join(" | ");
}

// Aktualisiert den Ergebniskopf mit Trefferzahl und aktivem Filterkontext.
function updateResultHeading(shown) {
  if (featuredMode) {
    resultHeading.textContent = "Bekannte Kaefer Lateinamerikas";
    return;
  }

  if (!hasActiveFilters() && selectedResultMode === RESULT_MODE_BROWSE) {
    resultHeading.textContent = "Stoeber-Modus: Kaefer aus der Datenbank";
    return;
  }

  if (window.API_BASE_URL && shouldApplySubtypeSpatialFilter() && subtypeListLoading) {
    resultHeading.textContent = "Kaeferdaten werden geladen ...";
    return;
  }

  const shouldUseMapTotal =
    window.API_BASE_URL &&
    Number.isFinite(lastRenderedMapPointTotal) &&
    lastRenderedMapPointTotal >= shown;

  if (shouldUseMapTotal) {
    resultHeading.textContent = `${shown} von ${lastRenderedMapPointTotal} Treffern`;
  } else

  if (window.API_BASE_URL && totalBeetles > shown) {
    resultHeading.textContent = `${shown} von ${totalBeetles} Treffern`;
  } else {
    resultHeading.textContent = `${shown} gefundene Arten`;
  }

  const context = activeFilterContextLabel();
  if (context) resultHeading.textContent = `${resultHeading.textContent} | ${context}`;

}

function updateResultPager(shown) {
  const pagerTargets = [resultPagerTop, resultPager].filter(Boolean);
  if (!pagerTargets.length) return;
  const canPaginate = window.API_BASE_URL && !featuredMode && !shouldApplySubtypeSpatialFilter() && totalBeetles > LIST_PAGE_SIZE;
  if (!canPaginate) {
    pagerTargets.forEach((el) => {
      el.innerHTML = "";
    });
    return;
  }

  const start = totalBeetles > 0 ? listOffset + 1 : 0;
  const end = Math.min(listOffset + shown, totalBeetles);
  const page = Math.floor(listOffset / LIST_PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(totalBeetles / LIST_PAGE_SIZE));
  const hasPrev = listOffset > 0;
  const hasNext = listOffset + LIST_PAGE_SIZE < totalBeetles;

  const pagerHtml = `
    <div class="result-pager-meta">Seite ${page}/${pages} | ${start}-${end} von ${totalBeetles}</div>
    <div class="result-pager-actions">
      <button type="button" class="result-pager-btn" data-page="prev" ${hasPrev ? "" : "disabled"}>Vorherige 200</button>
      <button type="button" class="result-pager-btn" data-page="next" ${hasNext ? "" : "disabled"}>Naechste 200</button>
    </div>
  `;

  pagerTargets.forEach((el) => {
    el.innerHTML = pagerHtml;
    const prevBtn = el.querySelector('[data-page="prev"]');
    const nextBtn = el.querySelector('[data-page="next"]');
    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        applyFilters({
          keepPage: true,
          pageOffset: Math.max(0, listOffset - LIST_PAGE_SIZE),
          forceBrowseRefresh: selectedResultMode === RESULT_MODE_BROWSE,
          suppressMapRefresh: selectedResultMode === RESULT_MODE_BROWSE,
        });
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        applyFilters({
          keepPage: true,
          pageOffset: listOffset + LIST_PAGE_SIZE,
          forceBrowseRefresh: selectedResultMode === RESULT_MODE_BROWSE,
          suppressMapRefresh: selectedResultMode === RESULT_MODE_BROWSE,
        });
      });
    }
  });
}

// Laender-Dropdown alphabetisch aus dem vorberechneten Snapshot fuellen.
// option.value = COUNTRY_STATS.code (= DB-Wert, den der Backend-Filter erwartet),
// option.text = Anzeigename.
(function populateCountryFilter() {
  if (!countryFilter || !window.COUNTRY_STATS) return;
  Object.values(window.COUNTRY_STATS)
    .map((c) => ({ code: c.code, name: c.name }))
    .sort((a, b) => resolveCountryDisplay(a).labelName.localeCompare(resolveCountryDisplay(b).labelName, "de"))
    .forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.code;
      const display = resolveCountryDisplay(c);
      opt.dataset.countryName = display.labelName;
      opt.textContent = display.iso ? `${display.labelName} (${display.iso})` : display.labelName;
      countryFilter.appendChild(opt);
    });
})();
const atlasSvg = document.querySelector("#atlasSvg");
const mapViewport = document.querySelector("#mapViewport");
const baseLayer = document.querySelector("#baseLayer");
const countryLineLayer = document.querySelector("#countryLineLayer");
const labelLayer = document.querySelector("#labelLayer");
const beetleLayer = document.querySelector("#beetleLayer");
const pointPopup = document.querySelector("#pointPopup");
const countrySidebar = document.querySelector("#countrySidebar");
const countrySidebarTitle = document.querySelector("#countrySidebarTitle");
const countrySidebarContent = document.querySelector("#countrySidebarContent");
const closeSidebarButton = document.querySelector("#closeSidebarButton");
const zoomInButton = document.querySelector("#zoomInButton");
const zoomOutButton = document.querySelector("#zoomOutButton");
const resetMapButton = document.querySelector("#resetMapButton");

// Ordnet eine Hoehe ihrer definierten Hoehengruppe zu.
function getElevationGroup(elevation) {
  const fn = AppPageUtils.getElevationGroup;
  return fn ? fn(elevation) : "4500_plus";
}

// Liefert die aktuell sichtbare Kaeferliste fuer Liste und Karte.
function getFilteredBeetles() {
  // Startliste (kuratierte Featured-Kaefer) direkt anzeigen.
  if (featuredMode) {
    return beetles;
  }

  // Backend liefert die Grundfilter; aktive Klima/Vegetation-Subtypen werden
  // zusaetzlich polygonbasiert auf Liste + Karte gleich angewendet.
  if (window.API_BASE_URL) {
    if (shouldApplySubtypeSpatialFilter() && Array.isArray(mapListBeetles)) {
      return mapListBeetles.slice(0, BEETLE_FETCH_LIMIT);
    }
    return beetles;
  }

  const search = searchInput.value.trim().toLowerCase();
  const country = countryFilter.value;
  const selectedCountryName = countryFilter.selectedOptions[0]?.dataset.countryName || "";
  const countryName = country === "all" ? "" : selectedCountryName.toLowerCase();
  const climateSet = new Set(getSelectedClimateCodes());
  const vegetationSet = new Set(getSelectedVegetationCodes());
  const elevationSet = new Set(getSelectedElevationKeys());
  const soilPhBand = soilPhBandFilter.value;
  const temperatureBand = temperatureBandFilter.value;
  const precipitationBand = precipitationBandFilter.value;
  const dataQuality = dataQualityFilter.value;
  const observedYear = yearFilter.value.trim();
  const imageMode = imageFilter.value;
  const matcher = AppPageUtils.beetleMatchesClientFilters;
  if (typeof matcher !== "function") return beetles;

  const filterContext = {
    search,
    country,
    countryName,
    climateSet,
    vegetationSet,
    elevationSet,
    soilPhBand,
    temperatureBand,
    precipitationBand,
    dataQuality,
    observedYear,
    imageMode,
    getElevationGroup,
  };

  return beetles.filter((beetle) => matcher(beetle, filterContext));
}

// ===== SVG map rendering =====

function svgElement(name, attributes = {}) {
  const fn = AppPageUtils.svgElement;
  return fn ? fn(name, attributes) : document.createElementNS("http://www.w3.org/2000/svg", name);
}

// Projiziert Koordinaten in das benoetigte Zielsystem.
function project([lon, lat]) {
  const fn = AppPageUtils.project;
  if (!fn) return [lon, lat];
  return fn([lon, lat], geoBounds);
}

// Erzeugt den SVG-Pfadstring fuer eine GeoJSON-Geometrie.
function pathFromGeometry(geometry) {
  const fn = AppPageUtils.pathFromGeometry;
  return fn ? fn(geometry, geoBounds) : "";
}

// Berechnet den benoetigten Wert fuer den weiteren Ablauf.
function calculateBounds(features) {
  const fn = AppPageUtils.calculateBounds;
  if (!fn) return { minLon: -120, maxLon: -30, minLat: -60, maxLat: 35 };
  return fn(features);
}

// Rendert die SVG-Landkarte inkl. Laenderflaechen, Grenzen und Labels.
function renderAtlasMap(featureCollection) {
  geoBounds = calculateBounds(featureCollection.features);
  baseLayer.innerHTML = "";
  countryLineLayer.innerHTML = "";
  labelLayer.innerHTML = "";
  beetleLayer.innerHTML = "";

  featureCollection.features.forEach((feature) => {
    const pathData = pathFromGeometry(feature.geometry);
    const name = feature.properties.name;

    baseLayer.appendChild(svgElement("path", {
      class: "country",
      d: pathData,
      "data-country": name,
    }));

    countryLineLayer.appendChild(svgElement("path", {
      class: "country-line",
      d: pathData,
      "data-country": name,
    }));

    const labelCoordinate = labelPositions[name];
    if (!labelCoordinate) return;

    const [x, y] = project([labelCoordinate[1], labelCoordinate[0]]);
    const label = svgElement("text", {
      class: tinyLabels.has(name) ? "country-label tiny-label" : "country-label",
      x,
      y,
      "data-country": name,
      tabindex: 0
    });
    label.textContent = name;
    labelLayer.appendChild(label);
  });

  updateCountryHighlight();
}

// Rendert die Kaeferpunkte auf der SVG-Karte.
function renderBeetlePoints() {
  if (!geoBounds) return;

  beetleLayer.innerHTML = "";

  getFilteredBeetles().forEach((beetle) => {
    const [x, y] = project(beetle.coordinates);
    const point = svgElement("circle", {
      class: "beetle-point",
      cx: x,
      cy: y,
      r: 2.5,
      "data-id": beetle.id
    });
    beetleLayer.appendChild(point);
  });
}

// Aktualisiert den aktuellen Pan/Zoom-Transform der SVG-Karte.
function updateMapTransform() {
  mapViewport.setAttribute("transform", `translate(${panX} ${panY}) scale(${zoom})`);
}

// Setzt den Zoomfaktor und haelt die angegebene Position als Zoomzentrum stabil.
function setZoom(nextZoom, centerX = 500, centerY = 490) {
  const oldZoom = zoom;
  zoom = Math.min(5, Math.max(1, nextZoom));
  panX = centerX - ((centerX - panX) / oldZoom) * zoom;
  panY = centerY - ((centerY - panY) / oldZoom) * zoom;
  updateMapTransform();
}

// Setzt den Zustand auf den Ausgangswert zurueck.
function resetMapView() {
  zoom = 1;
  panX = 0;
  panY = 0;
  updateMapTransform();
}

// IDs der aktuell aufgeklappten Karten. Mehrere koennen gleichzeitig offen sein;
// der Zustand bleibt ueber Re-Renders hinweg erhalten.
const expandedIds = new Set();

// Per Karten-InfoWindow ("▼ Alle Infos") ausgewaehlter Kaefer -> erste,
// aufgeklappte Detailkarte oben in der Liste. null = keiner gewaehlt.
let pinnedBeetle = null;

restoreMainState();

// Formatiert den Wert fuer die Anzeige.
function formatTemperature(value) {
  const fn = AppPageUtils.formatTemperature;
  if (!fn) return "—";
  return fn(value);
}

// Baut die URL zur Detailseite fuer einen Kaefer.
function detailPageUrl(beetleId) {
  const fn = AppPageUtils.detailPageUrl;
  if (!fn) return "detail.html";
  return fn(beetleId);
}

// Formatiert den Wert fuer die Anzeige.
function formatSoilPh(beetle) {
  const fn = AppPageUtils.formatSoilPh;
  if (!fn) return "unbekannt";
  return fn(beetle, SOIL_PH_BAND_LABELS);
}

// Rendert den HTML-Inhalt der ausklappbaren Kaefer-Detailkarte.
function beetleDetailHtml(beetle) {
  const image = beetle.imageUrl
    ? `<figure class="detail-figure">
         <img class="detail-bg" src="${beetle.imageUrl}" alt="" aria-hidden="true" loading="lazy" />
         <img class="detail-image" src="${beetle.imageUrl}" alt="${beetle.name}" loading="lazy" />
       </figure>`
    : "";
  const note = beetle.note ? `<p class="detail-note">${beetle.note}</p>` : "";
  const detailLink = beetle.id
    ? `<p><a class="detail-page-link" href="${detailPageUrl(beetle.id)}">Zur Detailseite mit allen Daten und Bildern</a></p>`
    : "";
  return `
    ${image}
    ${note}
    ${detailLink}
    <ul class="detail-list">
      <li><strong>Fundort</strong>${beetle.location}</li>
      <li><strong>Klimazone</strong>${climateLabel(beetle.climate)}</li>
      <li><strong>Vegetation</strong>${vegetationLabel(beetle.vegetation)}</li>
      <li><strong>Hoehenlage</strong>${beetle.elevation} m</li>
      <li><strong>Temperatur</strong>${formatTemperature(beetle.temperature)}</li>
      <li><strong>Boden-pH</strong>${formatSoilPh(beetle)}</li>
    </ul>
  `;
}

// Rendert Ergebnisliste und synchronisiert die aktive Kartenansicht.
function render() {
  restorePinnedBeetleIfNeeded();
  const filteredBeetles = getFilteredBeetles();
  const shown = filteredBeetles.length;
  updateResultHeading(shown);

  // Ein per Karten-Pin gewaehlter Kaefer steht als erste Karte oben
  // (dedupliziert, falls er ohnehin in der gefilterten Liste ist).
  const displayBeetles = pinnedBeetle
    ? [pinnedBeetle, ...filteredBeetles.filter((b) => String(b.id) !== String(pinnedBeetle.id))]
    : filteredBeetles;

  if (displayBeetles.length === 0) {
    if (window.API_BASE_URL && shouldApplySubtypeSpatialFilter() && subtypeListLoading) {
      resultList.innerHTML = `
        <div class="empty-state">Kaeferdaten werden geladen ...</div>
      `;
      updateResultPager(0);
      return;
    }
    resultList.innerHTML = `
      <div class="empty-state">Keine passenden Arten gefunden.</div>
    `;
    updateResultPager(0);
    return;
  }

  resultList.innerHTML = displayBeetles
    .map((beetle) => {
      const expanded = expandedIds.has(String(beetle.id));
      const commonName = beetle.commonName
        ? ` <span class="common-name">${beetle.commonName}</span>`
        : "";
      const sub = [beetle.family, beetle.location].filter(Boolean).join(" - ");
      return `
        <article class="species-card ${expanded ? "is-expanded" : ""}" data-id="${beetle.id}">
          <button class="species-card-head" type="button" aria-expanded="${expanded}">
            <h3>${beetle.name}${commonName}</h3>
            <p>${sub || "—"}</p>
            <div class="meta-row">
              <span class="tag">${climateLabel(beetle.climate)}</span>
              <span class="tag">${vegetationLabel(beetle.vegetation)}</span>
              <span class="tag">${beetle.elevation ?? 0} m</span>
            </div>
            <span class="expand-hint" aria-hidden="true"></span>
          </button>
          <div class="species-card-detail">${beetleDetailHtml(beetle)}</div>
        </article>
      `;
    })
    .join("");

  resultList.querySelectorAll("a.detail-page-link").forEach((link) => {
    link.addEventListener("click", () => {
      const card = link.closest(".species-card");
      const beetleId = card && card.dataset ? String(card.dataset.id || "") : "";
      if (beetleId) {
        pendingPinnedBeetleId = beetleId;
        expandedIds.add(beetleId);
      }
      saveMainState();
    });
  });

  updateResultPager(shown);

  if (!syncingListFromMap && !suppressNextMapRefresh) renderMapPoints();
  suppressNextMapRefresh = false;
}

// ===== List and map interactions =====

function scrollToList() {
  resultHeading.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Vom Karten-InfoWindow ("▼ Alle Infos"): Kaefer als erste, aufgeklappte
// Detailkarte unter die Karte holen und dorthin scrollen. needsFetch=true
// (Backend-Pins liefern nur Kurzdaten) -> volle DB-Details + Bild nachladen.
async function selectBeetleFromMap(beetle, needsFetch) {
  pinnedBeetle = beetle;
  expandedIds.add(String(beetle.id));
  pendingPinnedBeetleId = String(beetle.id);
  if (activeInfoWindow) activeInfoWindow.close();
  render();
  saveMainState();
  scrollToList();

  if (needsFetch && window.API_BASE_URL) {
    try {
      const res = await fetch(`${window.API_BASE_URL}/api/beetles/${beetle.id}`);
      if (!res.ok) return;
      const full = await res.json();
      // Nur uebernehmen, wenn inzwischen kein anderer Pin gewaehlt wurde.
      if (!pinnedBeetle || String(pinnedBeetle.id) !== String(beetle.id)) return;
      pinnedBeetle = full;
      expandedIds.add(String(full.id));
      render();
      pendingPinnedBeetleId = String(full.id);
      saveMainState();
    } catch (error) {
      console.error("Detaildaten konnten nicht geladen werden:", error);
    }
  }
}

// Kompaktes Karten-InfoWindow: Name + Familie + "Alle Infos"-Link (kein Bild).
function openBeetleInfoWindow(marker, beetle, needsFetch) {
  closeCountrySidebar();
  const fam = beetle.family
    ? `<div style="color:#66736b;font-size:0.82rem;margin-top:0.1rem">${beetle.family}</div>`
    : "";
  const details = beetle.id
    ? `<a href="${detailPageUrl(beetle.id)}" style="display:inline-block;margin-top:0.45rem;color:#2f6b47;font-weight:700;font-size:0.82rem;text-decoration:none">Zur Detailseite</a>`
    : "";
  activeInfoWindow.setContent(`
    <div style="font-family:Arial,sans-serif;min-width:120px;max-width:210px">
      <strong style="font-size:0.95rem">${beetle.name}</strong>
      ${fam}
      <button type="button" class="iw-more" style="margin-top:0.55rem;background:none;border:0;color:#2f6b47;font-weight:700;cursor:pointer;padding:0;font-size:0.85rem">▼ Alle Infos</button>
      ${details}
    </div>
  `);
  activeInfoWindow.open(googleMapInstance, marker);
  google.maps.event.addListenerOnce(activeInfoWindow, "domready", () => {
    const btn = document.querySelector(".iw-more");
    if (btn) btn.addEventListener("click", () => selectBeetleFromMap(beetle, needsFetch));
  });
}

// Rendert Marker entweder auf Google Maps oder im SVG-Fallback.
function renderMapPoints() {
  const hasGoogleMap = typeof googleMapInstance !== "undefined" && !!googleMapInstance;
  if (hasGoogleMap) {
    if (featuredMode) {
      // Startseite: nur die kuratierten Featured-Kaefer als Marker (nicht den
      // gesamten Datenbestand als Cluster laden).
      renderGoogleMapMarkers();
    } else if (window.API_BASE_URL) {
      // Suche/Filter: bbox-/zoom-basierte Punkte mit Clustering nachladen.
      scheduleMapPoints();
    } else {
      // Demo-Modus: die geladene Liste als Marker zeichnen.
      renderGoogleMapMarkers();
    }
  } else {
    renderBeetlePoints();
  }
}

function openCountrySidebar(countryName) {
  const fn = window.AppCountryUI && window.AppCountryUI.openCountrySidebar;
  if (!fn) return;
  fn(countryName, {
    titleEl: countrySidebarTitle,
    contentEl: countrySidebarContent,
    sidebarEl: countrySidebar,
    climateLabel,
    vegetationLabel,
  });
}

function closeCountrySidebar() {
  const fn = window.AppCountryUI && window.AppCountryUI.closeCountrySidebar;
  if (!fn) return;
  fn({ sidebarEl: countrySidebar });
}

// Oeffnet das Popup fuer einen SVG-Kartenpunkt an der Mausposition.
function openPointPopup(beetle, event) {
  pointPopup.innerHTML = `
    <h3>${beetle.name}</h3>
    <p>Hoehe: noch nicht eingetragen</p>
    <p>Vegetation: noch nicht eingetragen</p>
    <p>Klimazone: noch nicht eingetragen</p>
  `;

  const canvas = event.currentTarget.closest(".map-canvas");
  const canvasRect = canvas.getBoundingClientRect();
  const left = Math.min(event.clientX - canvasRect.left + 12, canvasRect.width - 210);
  const top = Math.min(event.clientY - canvasRect.top + 12, canvasRect.height - 150);

  pointPopup.style.left = `${Math.max(12, left)}px`;
  pointPopup.style.top = `${Math.max(12, top)}px`;
  pointPopup.classList.remove("is-hidden");
}

// Schliesst die zugehoerige UI-Ansicht.
function closePointPopup() {
  pointPopup.classList.add("is-hidden");
}

function resetAllFilters() {
  searchInput.value = "";
  countryFilter.value = "all";
  setSelectedClimateCodes([]);
  setSelectedVegetationCodes([]);
  activeClimateLegendColors.clear();
  activeVegetationLegendColors.clear();
  applyClimateLegendFilter();
  applyVegetationLegendFilter();
  setSelectedElevations([]);
  setElevationLegendActiveState();
  soilPhBandFilter.value = "all";
  temperatureBandFilter.value = "all";
  precipitationBandFilter.value = "all";
  dataQualityFilter.value = "all";
  yearFilter.value = "";
  imageFilter.value = "all";
  listOffset = 0;
  expandedIds.clear();
  applyFilters();
}

function initCountryEvents() {
  const fn = window.AppCountryEvents && window.AppCountryEvents.init;
  if (typeof fn !== "function") return;
  fn({
    labelLayer,
    beetleLayer,
    closeSidebarButton,
    closePointPopup,
    openCountrySidebar,
    closeCountrySidebar,
    openPointPopup,
    selectCountryFromMap,
    findBeetleById: (id) => beetles.find((item) => String(item.id) === String(id)),
  });
}

function initAppEvents() {
  const fn = window.AppEvents && window.AppEvents.init;
  if (typeof fn !== "function") return;
  fn({
    expandedIds,
    elements: {
      resultList,
      searchInput,
      countryFilter,
      climateFilter,
      vegetationFilter,
      elevationFilter,
      soilPhBandFilter,
      temperatureBandFilter,
      precipitationBandFilter,
      dataQualityFilter,
      yearFilter,
      imageFilter,
      filterToggle,
      filterPanel,
      zoomInButton,
      zoomOutButton,
      resetMapButton,
      atlasSvg,
      resetButton,
      featuredModeButton,
      browseModeButton,
    },
    state: {
      activeClimateLegendColors,
      activeVegetationLegendColors,
    },
    actions: {
      saveMainState,
      applyFilters,
      setSelectedClimateCodes,
      setSelectedVegetationCodes,
      setSelectedElevations,
      syncClimateLegendColorsFromSelection,
      syncVegetationLegendColorsFromSelection,
      setLegendActiveState,
      applyClimateLegendFilter,
      applyVegetationLegendFilter,
      setElevationLegendActiveState,
      setZoom,
      getZoom: () => zoom,
      resetMapView,
      setResultMode,
      closePointPopup,
      getPanState: () => ({ panX, panY }),
      setPanFromDrag: (dragStart, x, y) => {
        panX = dragStart.panX + x - dragStart.x;
        panY = dragStart.panY + y - dragStart.y;
        updateMapTransform();
      },
      resetAllFilters,
    },
  });
}

// Badge-Zahl + Chips nach jeder Filteraenderung aktualisieren.
function updateFilterUI() {
  const fn = window.AppFilterUI && window.AppFilterUI.updateFilterUI;
  if (typeof fn !== "function") return;

  fn({
    elements: {
      countryFilter,
      climateFilter,
      vegetationFilter,
      elevationFilter,
      soilPhBandFilter,
      temperatureBandFilter,
      precipitationBandFilter,
      dataQualityFilter,
      yearFilter,
      imageFilter,
      filterBadge,
      activeFilters,
    },
    selections: {
      selectedClimateCodes,
      selectedVegetationCodes,
      selectedElevationKeys,
    },
    getters: {
      getSelectedClimateCodes,
      getSelectedVegetationCodes,
      getSelectedElevationKeys,
    },
    actions: {
      setSelectedClimateCodes,
      setSelectedVegetationCodes,
      setSelectedElevations,
      applyClimateLegendFilter,
      applyVegetationLegendFilter,
      setElevationLegendActiveState,
    },
    legendState: {
      activeClimateLegendColors,
      activeVegetationLegendColors,
    },
    onApplyFilters: applyFilters,
  });
}

let currentView = pendingMapView || "normal";

// ===== Google map theme state =====

// Layer-Instanzen (einmalig erstellt, dann nur ein-/ausgeblendet)
let elevationTileType = null;
let climateDataLayer = null;
let vegetationDataLayer = null;
const ENABLE_SUBTYPE_SPATIAL_FILTER = true;
const activeClimateLegendColors = new Set();
const activeVegetationLegendColors = new Set();

initCountryEvents();
initAppEvents();
updateResultModeToggle();

// Defensive startup: if another bootstrap step fails silently, ensure
// the homepage still loads featured beetles and map/list content.
async function ensureInitialResultsLoaded() {
  const hasCards = document.querySelectorAll(".species-card").length > 0;
  if (hasCards) return;
  try {
    await applyFilters({
      keepPage: true,
      pageOffset: listOffset,
      forceBrowseRefresh: selectedResultMode === RESULT_MODE_BROWSE,
    });
  } catch (error) {
    console.error("Initiale Kaeferliste konnte nicht geladen werden:", error);
  }
}

setTimeout(() => {
  ensureInitialResultsLoaded();
}, 0);

// Normalisiert Eingabewerte fuer konsistente Verarbeitung.
function normalizeLegendColor(value) {
  const fn = window.MapCommon && window.MapCommon.normalizeLegendColor;
  if (typeof fn === "function") return fn(value);
  return String(value || "").trim().toLowerCase();
}

// ===== Legend helpers and handlers =====

function legendItemColor(li) {
  const fn = window.AppLegendHelpers && window.AppLegendHelpers.legendItemColor;
  if (typeof fn === "function") return fn(li, normalizeLegendColor);
  return "";
}

// Extrahiert den relevanten Legendeneintrag aus einem Click-Event.
function legendItemFromEvent(event) {
  const fn = window.AppLegendHelpers && window.AppLegendHelpers.legendItemFromEvent;
  return typeof fn === "function" ? fn(event) : null;
}

function getLegendControllerCtx() {
  const mapInstance = (typeof googleMapInstance !== "undefined") ? googleMapInstance : null;
  return {
    legendItemColor,
    legendItemFromEvent,
    normalizeLegendColor,
    activeClimateLegendColors,
    activeVegetationLegendColors,
    selectedClimateCodes,
    selectedVegetationCodes,
    selectedElevationKeys,
    climateFilter,
    vegetationFilter,
    elevationFilter,
    climateDataLayer,
    vegetationDataLayer,
    googleMapInstance: mapInstance,
    currentView,
    enableSubtypeSpatialFilter: ENABLE_SUBTYPE_SPATIAL_FILTER,
    getSelectedClimateCodes,
    getSelectedVegetationCodes,
    getSelectedElevationKeys,
    setSelectedClimateCodes,
    setSelectedVegetationCodes,
    setSelectedElevations,
    applyFilters,
    areAllSubtypesOfSingleClimateGroupSelected,
  };
}

// Aktualisiert aktive Zustandsklassen einer Farb-Legende.
function setLegendActiveState(legendId, activeColors) {
  const fn = window.AppLegendController && window.AppLegendController.setLegendActiveState;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx(), legendId, activeColors);
}

// Aktualisiert aktive Zustandsklassen der Hoehen-Legende.
function setElevationLegendActiveState() {
  const fn = window.AppLegendController && window.AppLegendController.setElevationLegendActiveState;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx());
}

// Synchronisiert den Zustand zwischen Auswahl und Darstellung.
function syncClimateLegendColorsFromSelection() {
  const fn = window.AppLegendController && window.AppLegendController.syncClimateLegendColorsFromSelection;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx());
}

// Synchronisiert den Zustand zwischen Auswahl und Darstellung.
function syncVegetationLegendColorsFromSelection() {
  const fn = window.AppLegendController && window.AppLegendController.syncVegetationLegendColorsFromSelection;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx());
}

// Wendet die Logik/Filter auf den aktuellen Zustand an.
function applyClimateLegendFilter() {
  const fn = window.AppLegendController && window.AppLegendController.applyClimateLegendFilter;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx());
}

// Wendet die Logik/Filter auf den aktuellen Zustand an.
function applyVegetationLegendFilter() {
  const fn = window.AppLegendController && window.AppLegendController.applyVegetationLegendFilter;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx());
}

// Verarbeitet das Ereignis und fuehrt die zugehoerige Logik aus.
function handleClimateLegendClick(event) {
  const fn = window.AppLegendController && window.AppLegendController.handleClimateLegendClick;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx(), event);
}

// Verarbeitet das Ereignis und fuehrt die zugehoerige Logik aus.
function handleVegetationLegendClick(event) {
  const fn = window.AppLegendController && window.AppLegendController.handleVegetationLegendClick;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx(), event);
}

// Verarbeitet das Ereignis und fuehrt die zugehoerige Logik aus.
function handleElevationLegendClick(event) {
  const fn = window.AppLegendController && window.AppLegendController.handleElevationLegendClick;
  if (typeof fn !== "function") return;
  fn(getLegendControllerCtx(), event);
}

// Initialisiert die benoetigten Ablaufe und Startwerte.
function initLegendFilters() {
  const fn = window.AppLegendController && window.AppLegendController.initLegendFilters;
  if (typeof fn !== "function") return;
  fn(() => getLegendControllerCtx());
}

// Entfernt aktive Themenlayer und blendet zugehoerige Legenden aus.
function hideAllThemeLayers() {
  const fn = window.AppLegendController && window.AppLegendController.hideAllThemeLayers;
  if (typeof fn === "function") fn(getLegendControllerCtx());
  callMapUi("hideAllLegends");
}

// Prueft, ob ein Klimacode als breite Sammelkategorie gilt.
function isBroadClimateCode(code) {
  const fn = window.AppLegendController && window.AppLegendController.isBroadClimateCode;
  if (typeof fn === "function") return fn(code);
  return false;
}

// Leitet den Klima-Hauptgruppen-Code (A-E) aus einem Legendeneintrag ab.
function climateLegendGroupCode(li) {
  const fn = window.AppLegendHelpers && window.AppLegendHelpers.climateLegendGroupCode;
  return typeof fn === "function" ? fn(li) : "";
}

// Prueft, ob alle aktiven Klima-Subtypen in genau einer Hauptgruppe liegen.
function areAllSubtypesOfSingleClimateGroupSelected() {
  const fn = window.AppLegendHelpers && window.AppLegendHelpers.areAllSubtypesOfSingleClimateGroupSelected;
  if (typeof fn !== "function") return false;
  return fn({
    root: document.getElementById("climateLegend"),
    activeClimateLegendColors,
    legendItemColor,
    climateLegendGroupCode,
  });
}

// Entscheidet, ob der raeumliche Subtyp-Polygonfilter aktiv sein soll.
function shouldApplySubtypeSpatialFilter() {
  const fn = window.AppLegendController && window.AppLegendController.shouldApplySubtypeSpatialFilter;
  if (typeof fn === "function") return fn(getLegendControllerCtx());
  return false;
}

// ===== Spatial filter bridge to app.spatial-filter.js =====

const climatePolygonsCache = new Map();
const vegetationPolygonsCache = new Map();
const climatePolygonsByColor = new Map();
const vegetationPolygonsByColor = new Map();

// Erzeugt einen stabilen Schluessel aus aktiven Legendenfarben.
function legendColorSetKey(activeColors) {
  const fn = window.AppSpatialFilter && window.AppSpatialFilter.legendColorSetKey;
  return fn ? fn(activeColors) : Array.from(activeColors).sort().join("|");
}

// Baut den Farbindex fuer Theme-Polygone zur schnelleren Punktpruefung auf.
function buildPolygonsByColorIndex(dataLayer, indexMap) {
  const fn = window.AppSpatialFilter && window.AppSpatialFilter.buildPolygonsByColorIndex;
  if (!fn) return;
  fn(dataLayer, indexMap, normalizeLegendColor);
}

// Filtert Kaeferlisten mit den aktuell aktiven Theme-Polygonen.
function filterBeetlesByActiveThemePolygons(beetleList) {
  const fn = window.AppSpatialFilter && window.AppSpatialFilter.filterBeetlesByActiveThemePolygons;
  if (!fn) return beetleList;
  return fn({
    beetleList,
    shouldApplySubtypeSpatialFilter: shouldApplySubtypeSpatialFilter(),
    currentView,
    climateDataLayer,
    activeClimateLegendColors,
    climatePolygonsCache,
    climatePolygonsByColor,
    vegetationDataLayer,
    activeVegetationLegendColors,
    vegetationPolygonsCache,
    vegetationPolygonsByColor,
    normalizeColor: normalizeLegendColor,
  });
}

// Filtert Kartenpunkte mit den aktuell aktiven Theme-Polygonen.
function filterPointsByActiveThemePolygons(points) {
  const fn = window.AppSpatialFilter && window.AppSpatialFilter.filterPointsByActiveThemePolygons;
  if (!fn) return points;
  return fn({
    points,
    shouldApplySubtypeSpatialFilter: shouldApplySubtypeSpatialFilter(),
    currentView,
    climateDataLayer,
    activeClimateLegendColors,
    climatePolygonsCache,
    climatePolygonsByColor,
    vegetationDataLayer,
    activeVegetationLegendColors,
    vegetationPolygonsCache,
    vegetationPolygonsByColor,
    normalizeColor: normalizeLegendColor,
  });
}

// Setzt den aktiven Zustand der View-Toggle-Buttons.
function setViewButtonsActive(view) {
  callMapUi("setViewButtonsActive", undefined, { view });
}

// Plant die Ausfuehrung asynchron im naechsten Schritt ein.
function scheduleMapRefreshByView() {
  if (featuredMode || !window.API_BASE_URL) {
    renderGoogleMapMarkers();
    return;
  }

  const hasSubtypeFilter = shouldApplySubtypeSpatialFilter();
  if (hasSubtypeFilter) subtypeListLoading = true;
  scheduleMapPoints();
}

// Initialisiert den Hoehen-Overlay-Layer bei Bedarf und aktiviert ihn.
function ensureElevationViewLayer() {
  const mapInstance = getGoogleMapInstanceSafe();
  if (!mapInstance) return;
  if (!elevationTileType) {
    elevationTileType = new google.maps.ImageMapType({
      getTileUrl: (coord, zoom) =>
        `https://tile.opentopomap.org/${zoom}/${coord.x}/${coord.y}.png`,
      tileSize: new google.maps.Size(256, 256),
      opacity: 0.85,
      name: "Topographie",
      maxZoom: 17,
    });
  }
  mapInstance.overlayMapTypes.push(elevationTileType);
  setElevationLegendActiveState();
  callMapUi("showLegendForView", undefined, { view: "elevation" });
}

// Initialisiert den Klima-Layer bei Bedarf und aktiviert ihn.
async function ensureClimateViewLayer() {
  const mapInstance = getGoogleMapInstanceSafe();
  if (!mapInstance) return;
  if (!climateDataLayer) {
    const data = await fetch("/assets/koppen-latam.geojson").then((r) => r.json());
    climateDataLayer = new google.maps.Data();
    climateDataLayer.addGeoJson(data);
    climatePolygonsByColor.clear();
    climatePolygonsCache.clear();
    buildPolygonsByColorIndex(climateDataLayer, climatePolygonsByColor);
    applyClimateLegendFilter();
  }
  applyClimateLegendFilter();
  climateDataLayer.setMap(mapInstance);
  callMapUi("showLegendForView", undefined, { view: "climate" });
}

// Initialisiert den Vegetations-Layer bei Bedarf und aktiviert ihn.
async function ensureVegetationViewLayer() {
  const mapInstance = getGoogleMapInstanceSafe();
  if (!mapInstance) return;
  if (!vegetationDataLayer) {
    const data = await fetch("/assets/ecoregions-latam.geojson").then((r) => r.json());
    vegetationDataLayer = new google.maps.Data();
    vegetationDataLayer.addGeoJson(data);
    vegetationPolygonsByColor.clear();
    vegetationPolygonsCache.clear();
    buildPolygonsByColorIndex(vegetationDataLayer, vegetationPolygonsByColor);
    applyVegetationLegendFilter();
  }
  applyVegetationLegendFilter();
  vegetationDataLayer.setMap(mapInstance);
  callMapUi("showLegendForView", undefined, { view: "vegetation" });
}

// Wechselt die Kartenansicht und synchronisiert Layer, Legende und Marker-Refresh.
async function setMapView(view) {
  setViewButtonsActive(view);

  if (!getGoogleMapInstanceSafe()) { currentView = view; return; }

  hideAllThemeLayers();
  currentView = view;
  saveMainState();

  if (view === "elevation" || view === "climate" || view === "vegetation") {
    callMapUi("showLegendForView", undefined, { view });
  }

  if (view === "elevation") {
    ensureElevationViewLayer();
  } else if (view === "climate") {
    try {
      await ensureClimateViewLayer();
    } catch (error) {
      console.error("Klima-Layer konnte nicht geladen werden:", error);
    }
  } else if (view === "vegetation") {
    try {
      await ensureVegetationViewLayer();
    } catch (error) {
      console.error("Vegetations-Layer konnte nicht geladen werden:", error);
    }
  }

  scheduleMapRefreshByView();
}



