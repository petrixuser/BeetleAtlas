(function () {

    // Punkt-in-Ring-Test (Ray-Casting-Algorithmus)
    function ringContainsPoint(lat, lng, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0];
      const yi = ring[i][1];
      const xj = ring[j][0];
      const yj = ring[j][1];
      const intersects = ((yi > lat) !== (yj > lat)) &&
        (lng < ((xj - xi) * (lat - yi)) / ((yj - yi) || 1e-12) + xi);
      if (intersects) inside = !inside;
    }
    return inside;
  }

  // Punkt-in-Polygon-Test
  function polygonContainsPoint(lat, lng, rings) {
    if (!rings.length) return false;
    if (!ringContainsPoint(lat, lng, rings[0])) return false;
    for (let i = 1; i < rings.length; i += 1) {
      if (ringContainsPoint(lat, lng, rings[i])) return false;
    }
    return true;
  }

  // Geometrie-zu-Polygon-Konvertierung
  function geometryToPolygons(geometry) {
    if (!geometry || !geometry.getType) return [];
    const type = geometry.getType();

    if (type === "Polygon") {
      const rings = geometry.getArray().map((ring) =>
        ring.getArray().map((ll) => [ll.lng(), ll.lat()])
      );
      return rings.length ? [rings] : [];
    }

    if (type === "MultiPolygon") {
      return geometry.getArray().flatMap((poly) => geometryToPolygons(poly));
    }

    if (type === "GeometryCollection") {
      return geometry.getArray().flatMap((part) => geometryToPolygons(part));
    }

    return [];
  }

  // Berechnet die Bounding-Box eines Polygons
  function polygonBounds(rings) {
    let minLng = Infinity;
    let minLat = Infinity;
    let maxLng = -Infinity;
    let maxLat = -Infinity;
    rings.forEach((ring) => {
      ring.forEach(([lng, lat]) => {
        if (lng < minLng) minLng = lng; 
        if (lng > maxLng) maxLng = lng;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      });
    });
    if (!Number.isFinite(minLng) || !Number.isFinite(minLat) || !Number.isFinite(maxLng) || !Number.isFinite(maxLat)) {
      return null;
    }
    return { minLng, minLat, maxLng, maxLat };
  }

  // Prüft, ob ein Punkt innerhalb der Bounding-Box liegt.
  function pointInsideBounds(lat, lng, bounds) {
    return bounds && lng >= bounds.minLng && lng <= bounds.maxLng && lat >= bounds.minLat && lat <= bounds.maxLat;
  }

  // Generiert einen Schlüssel für die aktive Farbpalette.
  function legendColorSetKey(activeColors) {
    return Array.from(activeColors).sort().join("|");
  }

  // Indiziert die Polygone nach ihrer Farbe, um die spätere Filterung zu beschleunigen.
  function buildPolygonsByColorIndex(dataLayer, indexMap, normalizeColor) {
    if (!dataLayer || !indexMap || indexMap.size > 0) return;
    dataLayer.forEach((feature) => {
      const color = normalizeColor(feature.getProperty("color"));
      if (!color) return;
      let list = indexMap.get(color);
      if (!list) {
        list = [];
        indexMap.set(color, list);
      }
      geometryToPolygons(feature.getGeometry()).forEach((rings) => {
        const bounds = polygonBounds(rings);
        if (!bounds) return;
        list.push({ rings, bounds });
      });
    });
  }

  // Sammelt die aktiven Polygone basierend auf den aktiven Farben.
  function collectActivePolygons(dataLayer, activeColors, cache, normalizeColor, indexMap) {
    if (!dataLayer || !activeColors || activeColors.size === 0) return [];
    const cacheKey = legendColorSetKey(activeColors);
    if (cache && cache.has(cacheKey)) {
      return cache.get(cacheKey);
    }

    if (indexMap) {
      buildPolygonsByColorIndex(dataLayer, indexMap, normalizeColor);
      const precomputed = [];
      activeColors.forEach((color) => {
        const polygons = indexMap.get(color);
        if (polygons && polygons.length) precomputed.push(...polygons);
      });
      if (cache) cache.set(cacheKey, precomputed);
      return precomputed;
    }

    const polygons = [];
    dataLayer.forEach((feature) => {
      const color = normalizeColor(feature.getProperty("color"));
      if (!activeColors.has(color)) return;
      geometryToPolygons(feature.getGeometry()).forEach((rings) => {
        const bounds = polygonBounds(rings);
        if (!bounds) return;
        polygons.push({ rings, bounds });
      });
    });
    if (cache) cache.set(cacheKey, polygons);
    return polygons;
  }

  // Filtert die Daten nach den aktiven Kriterien.
  function getActivePolygonsForCurrentView(ctx) {
    const {
      currentView, climateDataLayer, activeClimateLegendColors,
      climatePolygonsCache, climatePolygonsByColor, vegetationDataLayer,
      activeVegetationLegendColors, vegetationPolygonsCache, vegetationPolygonsByColor,
      normalizeColor,
    } = ctx;

    if (currentView === "climate") {
      return collectActivePolygons(
        climateDataLayer, activeClimateLegendColors, climatePolygonsCache,
        normalizeColor, climatePolygonsByColor
      );
    }

    if (currentView === "vegetation") {
      return collectActivePolygons(
        vegetationDataLayer, activeVegetationLegendColors, vegetationPolygonsCache,
        normalizeColor,vegetationPolygonsByColor
      );
    }

    return null;
  }

  // Prueft einen Punkt gegen alle aktiven Themenpolygone.
  function pointInAnyPolygon(lat, lng, polygons) {
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
    return polygons.some((poly) => pointInsideBounds(lat, lng, poly.bounds) && polygonContainsPoint(lat, lng, poly.rings));
  }

  // Filtert eine Liste ueber einen Koordinaten-Extractor gegen aktive Themenpolygone.
  function filterItemsByThemePolygons(items, polygons, getCoords) {
    if (!polygons) return items;
    if (!polygons.length) return [];

    return items.filter((item) => {
      const coords = getCoords(item);
      const lat = Number(coords && coords.lat);
      const lng = Number(coords && coords.lng);
      return pointInAnyPolygon(lat, lng, polygons);
    });
  }

  // Filtert Kaeferdaten anhand der aktiven Themenpolygone.
  function filterBeetlesByActiveThemePolygons(ctx) {
    const {
      beetleList,
      shouldApplySubtypeSpatialFilter,
    } = ctx;

    if (!shouldApplySubtypeSpatialFilter) return beetleList;
    const polygons = getActivePolygonsForCurrentView(ctx);
    return filterItemsByThemePolygons(beetleList, polygons, (beetle) => {
      const coords = beetle && beetle.coordinates;
      return {
        lat: coords && coords[1],
        lng: coords && coords[0],
      };
    });
  }

  // Filtert Kartenpunkte anhand der aktiven Themenpolygone.
  function filterPointsByActiveThemePolygons(ctx) {
    const {
      points,
      shouldApplySubtypeSpatialFilter,
    } = ctx;

    if (!shouldApplySubtypeSpatialFilter) return points;
    const polygons = getActivePolygonsForCurrentView(ctx);
    return filterItemsByThemePolygons(points, polygons, (point) => ({
      lat: point && point.lat,
      lng: point && point.lng,
    }));
  }

  window.AppSpatialFilter = {
    legendColorSetKey, buildPolygonsByColorIndex,
    filterBeetlesByActiveThemePolygons, filterPointsByActiveThemePolygons,
  };
})();
