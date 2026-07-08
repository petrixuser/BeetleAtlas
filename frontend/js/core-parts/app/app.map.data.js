// Datenversorgung fuer Google Maps: Laden, Caching und Marker-Rendering.

// ===== Laufzeitzustand der Karte =====

let googleMapInstance = null;
let activeMarkers = [];
let activeInfoWindow = null;
let lastMapPoints = [];

// Kartenpunkte aus dem Backend (bbox-/zoom-basiert, mit Clustering).
let mapPointsDebounce;
let mapPointsRequestId = 0;
let mapPointsAbortController = null;
const MAP_POINTS_LIMIT = 200;

// ===== Ablaufsteuerung fuer das Nachladen der Kartenpunkte =====

// Entprellt das Nachladen der Kartenpunkte (Pan/Zoom/Filter loesen es aus).
function scheduleMapPoints() {
  clearTimeout(mapPointsDebounce);
  mapPointsDebounce = setTimeout(loadMapPoints, 180);
}

// Session-Caches: identische Kartenabfragen und exakte Subtyp-Abfragen werden wiederverwendet.
const mapPointsCache = new Map();
const subtypeExactCache = new Map();
const LATAM_BOUNDS = (window.MapCommon && window.MapCommon.LATAM_BOUNDS)
  || { west: -160, south: -58, east: -32, north: 34 };

// ===== Caching keys =====

// Wandelt aktive Subtyp-Farben in einen stabilen Cache-Key um.
function activeSubtypeColorKey() {
  if (currentView === "climate") return legendColorSetKey(activeClimateLegendColors);
  if (currentView === "vegetation") return legendColorSetKey(activeVegetationLegendColors);
  return "";
}

// Generiert einen Cache-Key fuer die exakte Untertyp-Filterung, die bei aktiviertem räumlichen Filter notwendig ist.
function subtypeExactCacheKey(baseParams) {
  return `${currentView}|${activeSubtypeColorKey()}|${baseParams.toString()}`;
}

// Schreibt einen Eintrag in den Cache fuer die exakte Untertyp-Filterung.
function writeSubtypeExactCache(key, value) {
  subtypeExactCache.set(key, value);
  if (subtypeExactCache.size > 100) {
    const first = subtypeExactCache.keys().next().value;
    if (first) subtypeExactCache.delete(first);
  }
}

// Prueft, ob Kartenpunkte im aktuellen Modus ueberhaupt geladen werden sollen.
function canLoadMapPoints() {
  return Boolean(googleMapInstance && window.API_BASE_URL && !featuredMode);
}

// Erzeugt die gemeinsame Grundabfrage (bbox, zoom, Filter) fuer Kartenpunkte.
function buildMapPointsBaseQuery(useFullSubtypeBounds) {
  const bounds = googleMapInstance.getBounds();
  if (!bounds) return null;

  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();
  const bboxWest = useFullSubtypeBounds ? LATAM_BOUNDS.west : sw.lng();
  const bboxSouth = useFullSubtypeBounds ? LATAM_BOUNDS.south : sw.lat();
  const bboxEast = useFullSubtypeBounds ? LATAM_BOUNDS.east : ne.lng();
  const bboxNorth = useFullSubtypeBounds ? LATAM_BOUNDS.north : ne.lat();

  const params = new URLSearchParams();
  params.set("bbox", [bboxWest, bboxSouth, bboxEast, bboxNorth].join(","));

  const mapZoom = Math.round(googleMapInstance.getZoom());
  const effectiveZoom = useFullSubtypeBounds ? Math.max(7, mapZoom) : mapZoom;
  params.set("zoom", String(effectiveZoom));

  const search = searchInput.value.trim();
  if (search) params.set("q", search);
  if (countryFilter.value !== "all") params.set("country", countryFilter.value);
  if (soilPhBandFilter.value !== "all") params.set("soil_ph_band", soilPhBandFilter.value);
  if (temperatureBandFilter.value !== "all") params.set("temperature_band", temperatureBandFilter.value);
  if (precipitationBandFilter.value !== "all") params.set("precipitation_band", precipitationBandFilter.value);
  if (dataQualityFilter.value !== "all") params.set("event_date_quality", dataQualityFilter.value);
  // Fundjahr nur senden, wenn es der Backend-Validierung (2000-2026) entspricht,
  // sonst antwortet /api/map/points mit 422 und die Karte bleibt leer.
  const mapYearRaw = yearFilter.value.trim();
  if (/^\d{4}$/.test(mapYearRaw)) {
    const mapYear = Number(mapYearRaw);
    if (mapYear >= 2000 && mapYear <= 2026) params.set("observed_year", mapYearRaw);
  }
  if (imageFilter.value === "with_images") params.set("has_image", "true");
  if (imageFilter.value === "no_images") params.set("has_image", "false");
  params.set("limit", String(MAP_POINTS_LIMIT));
  params.set("offset", "0");

  return {
    params,
    combos: buildFilterCombinations(),
  };
}

// Erzeugt den Request-Kontext inkl. Abbruchsteuerung fuer veraltete Abfragen.
function createMapPointsRequestContext() {
  const reqId = ++mapPointsRequestId;
  if (mapPointsAbortController) {
    mapPointsAbortController.abort();
  }
  mapPointsAbortController = new AbortController();
  return {
    reqId,
    signal: mapPointsAbortController.signal,
  };
}

// Prueft, ob eine laufende Anfrage durch eine neuere ersetzt wurde.
function isStaleMapPointsRequest(reqId) {
  return reqId !== mapPointsRequestId;
}

// Normalisiert Cache- oder API-Rohdaten auf ein einheitliches Antwortformat.
function normalizeMapPointsEntry(cached) {
  if (!cached) return null;
  if (Array.isArray(cached)) {
    return { items: cached, total: cached.length, sourceTotalPoints: cached.length };
  }
  return {
    items: Array.isArray(cached.items) ? cached.items : [],
    total: Number.isFinite(cached.total) ? cached.total : (Array.isArray(cached.items) ? cached.items.length : 0),
    sourceTotalPoints: Number.isFinite(cached.sourceTotalPoints)
      ? cached.sourceTotalPoints
      : (Number.isFinite(cached.total) ? cached.total : (Array.isArray(cached.items) ? cached.items.length : 0)),
  };
}

// Liest einen Kartenpunkte-Cacheeintrag und normalisiert ihn.
function readMapPointsCache(cacheKey) {
  return normalizeMapPointsEntry(mapPointsCache.get(cacheKey));
}

// Holt Kartenpunkte von der API und liefert sie im Normalformat zurueck.
async function fetchMapPointsEntry(queryParams, signal) {
  const res = await fetch(`${window.API_BASE_URL}/api/map/points?${queryParams}`, { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return normalizeMapPointsEntry({
    items: data.items ?? [],
    total: Number(data.total ?? (data.items ?? []).length),
    sourceTotalPoints: Number(data.source_total_points ?? (data.total ?? (data.items ?? []).length)),
  });
}

// Liefert einen Eintrag aus Cache oder API und schreibt API-Treffer in den Cache.
async function getMapPointsEntry(queryParams, signal) {
  const key = queryParams.toString();
  const cached = readMapPointsCache(key);
  if (cached) return cached;

  const entry = await fetchMapPointsEntry(queryParams, signal);
  mapPointsCache.set(key, entry);
  return entry;
}

// Uebertraegt eine Filterkombination in die Query-Parameter. Klima-Subtypen (Af)
// und Vegetationszonen werden roh gesendet; das Backend filtert exakt ueber die
// vorberechneten Spalten koppen_code / vegetation_zone.
function applyComboToParams(params, combo) {
  if (combo.climate !== "all") params.set("climate", combo.climate);
  if (combo.vegetation !== "all") params.set("vegetation", combo.vegetation);
  if (combo.elevation !== "all") params.set("elevation", combo.elevation);
}

// Laedt den exakten Subtyp-Filter in einem Request und nutzt dessen Gesamtzahl.
async function fetchSubtypeExact(baseParams, requestCtx) {
  const paged = new URLSearchParams(baseParams);
  paged.set("offset", "0");
  paged.set("limit", String(MAP_POINTS_LIMIT));

  const entry = await getMapPointsEntry(paged, requestCtx.signal);
  if (isStaleMapPointsRequest(requestCtx.reqId)) {
    return { markerItems: [], filteredTotal: 0 };
  }

  const items = entry.items || [];
  const filtered = filterPointsByActiveThemePolygons(items);
  const filteredTotal = Number(entry.total ?? filtered.length);
  const markerItems = filtered.slice(0, MAP_POINTS_LIMIT);

  return { markerItems, filteredTotal };
}

// Verarbeitet den Ein-Kombinations-Fall und rendert Treffer direkt.
async function handleSingleComboMapPoints(baseParams, combo, useFullSubtypeBounds, requestCtx) {
  applyComboToParams(baseParams, combo || { climate: "all", vegetation: "all", elevation: "all" });

  if (useFullSubtypeBounds) {
    const exactKey = subtypeExactCacheKey(baseParams);
    const precomputed = subtypeExactCache.get(exactKey);
    if (precomputed) {
      if (isStaleMapPointsRequest(requestCtx.reqId)) return;
      renderMapMarkersFromPoints(precomputed.markerItems, precomputed.filteredTotal);
      return;
    }

    const exact = await fetchSubtypeExact(baseParams, requestCtx);
    if (isStaleMapPointsRequest(requestCtx.reqId)) return;

    writeSubtypeExactCache(exactKey, {
      markerItems: Array.isArray(exact.markerItems) ? exact.markerItems : [],
      filteredTotal: Number(exact.filteredTotal || 0),
    });
    renderMapMarkersFromPoints(exact.markerItems, exact.filteredTotal);
    return;
  }

  const entry = await getMapPointsEntry(baseParams, requestCtx.signal);
  if (isStaleMapPointsRequest(requestCtx.reqId)) return;
  renderMapMarkersFromPoints(entry.items, entry.sourceTotalPoints);
}

// Fasst Clusterpunkte gleicher Position aus mehreren Ergebnislisten zusammen.
function mergeClusterLists(allLists) {
  const buckets = new Map();
  allLists.flat().forEach((point) => {
    const clusterKey = `${Number(point.lat).toFixed(4)}:${Number(point.lng).toFixed(4)}`;
    const current = buckets.get(clusterKey) || {
      lat: point.lat, lng: point.lng,
      count: 0, isCluster: true,
    };
    current.count += Number(point.count || 0);
    buckets.set(clusterKey, current);
  });
  return Array.from(buckets.values()).sort((a, b) => b.count - a.count);
}

// Fuehrt Listen aus mehreren Kombinationen ueber eindeutige IDs zusammen.
function mergeUniquePointLists(allLists) {
  const merged = [];
  const seen = new Set();
  allLists.flat().forEach((point) => {
    const id = String(point?.id || "");
    if (!id || seen.has(id)) return;
    seen.add(id);
    merged.push(point);
  });
  return merged;
}

// Verarbeitet den Multi-Kombinations-Fall und rendert den kombinierten Trefferstand.
async function handleMultiComboMapPoints(baseParams, combos, requestCtx) {
  const allLists = [];
  let totalPoints = 0;

  for (const combo of combos) {
    const perParams = new URLSearchParams(baseParams);
    applyComboToParams(perParams, combo);
    const entry = await getMapPointsEntry(perParams, requestCtx.signal);
    allLists.push(entry.items);
    totalPoints += Number(entry.sourceTotalPoints || entry.total || 0);
  }

  if (isStaleMapPointsRequest(requestCtx.reqId)) return;

  const first = allLists[0] || [];
  if (first.length && first[0].isCluster) {
    renderMapMarkersFromPoints(mergeClusterLists(allLists), totalPoints);
    return;
  }

  const merged = mergeUniquePointLists(allLists);
  renderMapMarkersFromPoints(merged, totalPoints || merged.length);
}

// Laedt Kartenpunkte passend zu aktuellem Viewport, Zoom und Filtern.
async function loadMapPoints() {
  if (!canLoadMapPoints()) return;
  const useFullSubtypeBounds = shouldApplySubtypeSpatialFilter();
  const baseQuery = buildMapPointsBaseQuery(useFullSubtypeBounds);
  if (!baseQuery) return;
  const params = baseQuery.params;
  const combos = baseQuery.combos;
  const requestCtx = createMapPointsRequestContext();

  try {
    if (combos.length <= 1) {
      await handleSingleComboMapPoints(
        params, combos[0] || { climate: "all", vegetation: "all", elevation: "all" },
        useFullSubtypeBounds, requestCtx
      );
      return;
    }

    await handleMultiComboMapPoints(params, combos, requestCtx);
  } catch (error) {
    if (error?.name === "AbortError") return;
    console.error("Kartenpunkte konnten nicht geladen werden:", error);
    if (shouldApplySubtypeSpatialFilter()) {
      subtypeListLoading = false;
      if (typeof setListLoading === "function") setListLoading(false);
      render();
    }
  }
}

// Baut die Listenansicht fuer den Subtyp-Modus aus Markerpunkten auf.
function buildSubtypeMapListBeetles(markerPoints) {
  const dedup = new Map();
  markerPoints.forEach((point) => {
    if (point.isCluster || !point.id) return;
    const id = String(point.id);
    if (dedup.has(id)) return;
    dedup.set(id, {
      id, name: point.speciesName || "Unbekannt", family: point.family || "",
      location: point.location || "", coordinates: [Number(point.lng), Number(point.lat)],
      climate: point.climate || "unknown", vegetation: point.vegetation || "unknown",
      elevation: Number(point.elevation || 0), temperature: null, soil: null,
      imageUrl: null, observedAt: point.observedAt || null,
    });
  });
  return Array.from(dedup.values());
}

// Synchronisiert Trefferzaehler und Listenansicht mit den aktuell gerenderten Kartenpunkten.
function syncListStateFromMap(markerPoints, filteredPoints, totalPoints, partialSubtype) {
  const useSubtypeSpatialFilter = shouldApplySubtypeSpatialFilter();

  if (useSubtypeSpatialFilter) {
    mapListBeetles = buildSubtypeMapListBeetles(markerPoints);
    subtypeListLoading = partialSubtype;
  } else {
    mapListBeetles = null;
    subtypeListLoading = false;
  }

  lastRenderedMapPointCount = markerPoints.length;
  lastRenderedMapPointTotal = Number.isFinite(totalPoints)
    ? totalPoints
    : (useSubtypeSpatialFilter ? filteredPoints.length : markerPoints.length);
  updateResultHeading(getFilteredBeetles().length);

  syncingListFromMap = true;
  render();
  syncingListFromMap = false;
  if (typeof setListLoading === "function") setListLoading(false);
}

// Entfernt alle aktuell sichtbaren Google-Map-Marker.
function clearActiveMapMarkers() {
  activeMarkers.forEach((marker) => marker.setMap(null));
  activeMarkers = [];
}

// Erzeugt einen Cluster-Marker mit Zoom-in-Verhalten.
function createClusterMarker(point) {
  const scale = Math.min(24, 11 + Math.log10(Math.max(point.count, 1)) * 6);
  const marker = new google.maps.Marker({
    position: { lat: point.lat, lng: point.lng },
    map: googleMapInstance,
    label: {
      text: String(point.count), color: "#ffffff",
      fontSize: "11px", fontWeight: "bold"
    },
    icon: {
      path: google.maps.SymbolPath.CIRCLE, scale, fillColor: "#c0392b",
      fillOpacity: 0.85, strokeColor: "#ffd1d1", strokeWeight: 1.5
    }
  });

  marker.addListener("click", () => {
    googleMapInstance.panTo({ lat: point.lat, lng: point.lng });
    googleMapInstance.setZoom(Math.min(Math.round(googleMapInstance.getZoom()) + 3, 18));
  });

  return marker;
}

// Erzeugt einen Einzelmarker mit Info-Fenster fuer den Datensatz.
function createSinglePointMarker(point) {
  const marker = new google.maps.Marker({
    position: { lat: point.lat, lng: point.lng },
    map: googleMapInstance, title: point.speciesName,
    icon: {
      path: google.maps.SymbolPath.CIRCLE, scale: 6, fillColor: "#ff2b2b",
      fillOpacity: 0.9, strokeColor: "#ffd1d1", strokeWeight: 1.2
    }
  });

  marker.addListener("click", () => {
    const partial = {
      id: point.id, name: point.speciesName, family: "", location: "",
      climate: point.climate, vegetation: point.vegetation, elevation: point.elevation,
      temperature: null, soil: null, imageUrl: null, observedAt: point.observedAt,
    };
    openBeetleInfoWindow(marker, partial, true);
  });

  return marker;
}

// Rendert alle Markerpunkte als Cluster- oder Einzelmarker auf der Karte.
function renderMarkers(markerPoints) {
  markerPoints.forEach((point) => {
    const marker = point.isCluster ? createClusterMarker(point) : createSinglePointMarker(point);
    activeMarkers.push(marker);
  });
}

// Rendert Cluster- und Einzelmarker aus geladenen Kartenpunkten und synchronisiert die Liste.
function renderMapMarkersFromPoints(points, totalPoints = null, options = {}) {

  lastMapPoints = Array.isArray(points) ? points : [];
  const filteredPoints = filterPointsByActiveThemePolygons(lastMapPoints);
  const markerPoints = shouldApplySubtypeSpatialFilter()
    ? filteredPoints.slice(0, MAP_POINTS_LIMIT)
    : filteredPoints;
  const partialSubtype = Boolean(options && options.partialSubtype);

  syncListStateFromMap(markerPoints, filteredPoints, totalPoints, partialSubtype);
  clearActiveMapMarkers();
  renderMarkers(markerPoints);
}

