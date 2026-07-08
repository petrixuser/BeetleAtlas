// Datenlade-Schicht der Detailseite: API-Requests, Medien-Paging, lokaler
// Fallback (Featured/Demo) und Umwelt-Wertebereiche.
// Ausgelagert aus core/detail.js; stellt die Funktionen ueber window.DetailData
// bereit (die Detailseite selbst ist ein eigenes IIFE).
(function () {
  "use strict";

  // Liefert die API-Basis-URL (leer, wenn kein Backend konfiguriert ist).
  function apiBase() {
    return window.API_BASE_URL || "";
  }

  // Prueft, ob mit Backend-API gearbeitet werden kann.
  function apiEnabled() {
    return Boolean(apiBase());
  }

  // Gemeinsamer API-Helper mit einheitlicher Fehleraufbereitung.
  async function fetchJson(path) {
    var res = await fetch(apiBase() + path);
    if (!res.ok) {
      var text = "HTTP " + res.status;
      try {
        var body = await res.json();
        if (body && body.message) text = body.message;
      } catch (e) {
        // Fallback-Text beibehalten
      }
      var err = new Error(text);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  // Laedt alle Medienseiten fuer einen Kaefer nacheinander.
  async function fetchAllMedia(beetleId) {
    var limit = 200;
    var offset = 0;
    var all = [];
    var total = Infinity;

    while (all.length < total) {
      var page = await fetchJson("/api/beetles/" + encodeURIComponent(beetleId) + "/media?limit=" + limit + "&offset=" + offset);
      var items = page.items || [];
      total = Number(page.total || items.length);
      if (items.length === 0) break;
      all = all.concat(items);
      offset += items.length;
    }

    return all;
  }

  // Laedt Detaildaten und Medien ueber die Backend-API (parallel, da unabhaengig).
  async function loadFromApi(beetleId) {
    var results = await Promise.all([
      fetchJson("/api/beetles/" + encodeURIComponent(beetleId)),
      fetchAllMedia(beetleId),
    ]);
    return { detail: results[0], media: results[1] };
  }

  // Laedt Wertebereiche aus Cache/API fuer skalierte Umweltbalken.
  async function loadEnvironmentRanges() {
    var cacheKey = "detailEnvRangesV1";
    var cacheTsKey = "detailEnvRangesV1Ts";
    var now = Date.now();
    var ttlMs = 30 * 60 * 1000;

    try {
      var cachedRaw = window.sessionStorage.getItem(cacheKey);
      var cachedTs = Number(window.sessionStorage.getItem(cacheTsKey) || "0");
      if (cachedRaw && Number.isFinite(cachedTs) && now - cachedTs < ttlMs) {
        return JSON.parse(cachedRaw);
      }
    } catch (error) {
      // Fehler beim Parsen/Zugriff auf den Speicher ignorieren
    }

    if (!apiEnabled()) return null;
    try {
      var ranges = await fetchJson("/api/beetles/ranges/environment");
      try {
        window.sessionStorage.setItem(cacheKey, JSON.stringify(ranges));
        window.sessionStorage.setItem(cacheTsKey, String(now));
      } catch (error) {
      }
      return ranges;
    } catch (error) {
      return null;
    }
  }

  // Baut Detaildaten aus lokalen Demo-/Featured-Quellen auf.
  function loadFromLocal(beetleId) {
    var pool = []
      .concat(window.FEATURED_BEETLES || [])
      .concat(window.DEMO_BEETLES || []);

    var hit = pool.find(function (item) {
      return String(item.id) === String(beetleId);
    });

    if (!hit) return null;

    var media = [];
    if (hit.imageUrl) {
      media.push({
        mediaId: "local-1",
        url: hit.imageUrl,
        license: null,
        creator: null,
        publisher: null,
        rightsHolder: null,
        references: null,
      });
    }

    return {
      detail: {
        id: hit.id,
        name: hit.name,
        family: hit.family,
        location: hit.location,
        coordinates: hit.coordinates,
        climate: hit.climate,
        vegetation: hit.vegetation,
        elevation: hit.elevation,
        temperature: hit.temperature,
        soil: hit.soil,
        observedAt: hit.observedAt,
        imageUrl: hit.imageUrl,
        meta: {
          local: true,
          note: hit.note || null,
          commonName: hit.commonName || null,
        },
        ee: null,
      },
      media: media,
    };
  }

  // Vereinigt Medienquellen und entfernt doppelte URLs.
  function uniqueMediaUrls(detail, mediaItems) {
    var seen = new Set();
    var all = [];

    (mediaItems || []).forEach(function (item) {
      if (!item || !item.url || seen.has(item.url)) return;
      seen.add(item.url);
      all.push(item);
    });

    var embedded = detail && detail.meta && detail.meta.media && detail.meta.media.items;
    if (Array.isArray(embedded)) {
      embedded.forEach(function (item, index) {
        if (!item || !item.url || seen.has(item.url)) return;
        seen.add(item.url);
        all.push({
          mediaId: "embedded-" + index,
          url: item.url,
          license: item.license,
          creator: item.creator,
          publisher: item.publisher,
          rightsHolder: item.rightsHolder,
          references: null,
        });
      });
    }

    if (detail && detail.imageUrl && !seen.has(detail.imageUrl)) {
      seen.add(detail.imageUrl);
      all.unshift({
        mediaId: "primary",
        url: detail.imageUrl,
        license: null,
        creator: null,
        publisher: null,
        rightsHolder: null,
        references: null,
      });
    }

    return all;
  }

  // Nach aussen bereitgestellte Datenlade-Schnittstelle.
  window.DetailData = {
    apiEnabled: apiEnabled,
    loadFromApi: loadFromApi,
    loadFromLocal: loadFromLocal,
    loadEnvironmentRanges: loadEnvironmentRanges,
    uniqueMediaUrls: uniqueMediaUrls,
  };
})();
