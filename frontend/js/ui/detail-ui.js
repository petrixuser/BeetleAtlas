(function () {
  "use strict";

  var stickyObserver = null;
  var MISSING_TEXT = "—";

  // Liefert ein Detail-Element per ID.
  function $(id) {
    return document.getElementById(id);
  }

  // Formatiert den Temperaturtext fuer den Sticky-Header.
  function stickyTempText(raw, detail, formatOneDecimal) {
    var stickyRawTemp = raw.temperature;
    var stickyFallbackTemp = detail.temperature;
    return stickyRawTemp != null
      ? "Temp: " + formatOneDecimal(stickyRawTemp) + " °C"
      : stickyFallbackTemp != null
        ? "Temp: " + formatOneDecimal(stickyFallbackTemp) + " °C"
        : "Temp: " + MISSING_TEXT;
  }

  // Formatiert den Niederschlagstext fuer den Sticky-Header.
  function stickyPrecipText(raw) {
    return raw.precipitation != null
      ? "Niederschlag: " + Math.round(Number(raw.precipitation)) + " mm"
      : "Niederschlag: " + MISSING_TEXT;
  }

  // Formatiert den Boden-pH-Text fuer Sticky-Header und Chips.
  function formatSoilPhText(location, formatOneDecimal, soilPhBandLabel, formatCodeValue, detail) {
    var stickyPhValue = location.soilPh != null ? formatOneDecimal(location.soilPh) : null;
    var stickyPhBand = soilPhBandLabel(location.soilPhBand) || formatCodeValue(detail && detail.soil);
    return stickyPhValue
      ? stickyPhBand
        ? stickyPhValue + " (" + stickyPhBand + ")"
        : stickyPhValue
      : stickyPhBand || null;
  }

  // Befuellt die einzelnen Sticky-Felder mit den berechneten Werten.
  function populateStickyFields(ctx) {
    var detail = ctx.detail;
    var sticky = ctx.sticky;
    var raw = ctx.raw;
    var location = ctx.location;
    var formatCodeValue = ctx.formatCodeValue;
    var formatOneDecimal = ctx.formatOneDecimal;
    var soilPhBandLabel = ctx.soilPhBandLabel;
    var elevationText = ctx.elevationText;

    var nameEl = $("detailStickyName");
    var metaEl = $("detailStickyMeta");
    var tempEl = $("detailStickyTemp");
    var precipEl = $("detailStickyPrecip");
    var climateEl = $("detailStickyClimate");
    var vegetationEl = $("detailStickyVegetation");
    var elevationEl = $("detailStickyElevation");
    var phEl = $("detailStickyPh");

    if (nameEl) nameEl.textContent = detail.name || "Unbekannter Kaefer";
    if (metaEl) metaEl.textContent = [detail.family, detail.location].filter(Boolean).join(" · ") || MISSING_TEXT;
    if (tempEl) tempEl.textContent = stickyTempText(raw, detail, formatOneDecimal);
    if (precipEl) precipEl.textContent = stickyPrecipText(raw);
    if (climateEl) climateEl.textContent = "Klimazone: " + (formatCodeValue(detail && detail.climate) || MISSING_TEXT);
    if (vegetationEl) vegetationEl.textContent = "Vegetation: " + (formatCodeValue(detail && detail.vegetation) || MISSING_TEXT);
    if (elevationEl) elevationEl.textContent = "Hoehe: " + (elevationText(detail) || MISSING_TEXT);

    if (phEl) {
      var stickyPhText = formatSoilPhText(location, formatOneDecimal, soilPhBandLabel, formatCodeValue, detail);
      phEl.textContent = "pH: " + (stickyPhText || MISSING_TEXT);
    }

    sticky.classList.add("is-hidden");
  }

  // Baut die Datensaetze fuer die Klima-/Standort-Chips auf.
  function buildClimateChipRows(detail, bands, raw, formatCodeValue, chipPhText, landcoverText) {
    var landcoverFn = typeof landcoverText === "function"
      ? landcoverText
      : function (group) { return formatCodeValue(group); };
    return [
      ["Klimazone", formatCodeValue(detail && detail.climate)], 
      ["Vegetation", formatCodeValue(detail && detail.vegetation)],
      ["Boden-pH", chipPhText],
      ["Temperatur", formatCodeValue(bands.temperature)],
      ["Niederschlag", formatCodeValue(bands.precipitation)],
      ["Bodenfeuchte", formatCodeValue(bands.soilMoisture)],
      ["NDVI", formatCodeValue(bands.ndvi)],
      ["Luftfeuchte", formatCodeValue(bands.humidity)],
      ["Luftdruck", formatCodeValue(bands.pressure)],
      ["Nachtlicht", formatCodeValue(bands.lightPollution)],
      ["Hangneigung", formatCodeValue(bands.slope)],
      ["Distanz zu Wasser", formatCodeValue(bands.waterDistance)],
      ["Menschlicher Einfluss", formatCodeValue(bands.humanImpact)],
      ["Landbedeckung", landcoverFn(bands.landcoverGroup, raw.landcoverClass)],
    ];
  }

  // Rendert Chip-Elemente in den Zielcontainer.
  function renderChipElements(chipsEl, chips) {
    chipsEl.innerHTML = "";
    chipsEl.classList.remove("is-hidden");
    chips.forEach(function (chip) {
      if (!chip[1]) return;
      var span = document.createElement("span");
      span.className = "detail-chip";
      span.textContent = chip[0] + ": " + chip[1];
      chipsEl.appendChild(span);
    });
  }

  // Erzeugt die Zeilen mit Metadaten unter einem Medienbild.
  function buildMediaCaptionLines(item) {
    return [
      ["Lizenz", item.license], ["Creator", item.creator], ["Publisher", item.publisher],
      ["Rights Holder", item.rightsHolder], ["Referenz", item.references],
    ];
  }

  // Erzeugt eine einzelne Medienkarte inklusive Bild und Caption.
  function createMediaCard(item, index) {
    var card = document.createElement("article");
    card.className = "detail-media-card";

    var img = document.createElement("img");
    img.loading = "lazy";
    img.src = item.url;
    img.alt = "Kaeferbild " + (index + 1);
    card.appendChild(img);

    var caption = document.createElement("div");
    caption.className = "detail-media-caption";

    buildMediaCaptionLines(item).forEach(function (line) {
      if (!line[1]) return;
      var p = document.createElement("p");
      p.textContent = line[0] + ": " + line[1];
      caption.appendChild(p);
    });

    card.appendChild(caption);
    return card;
  }

  // Rendert den Leerzustand der Mediensektion.
  function renderMediaEmpty(mediaGrid) {
    var empty = document.createElement("p");
    empty.className = "detail-muted";
    empty.textContent = "Zu diesem Kaefer wurden keine Bilder gefunden.";
    mediaGrid.appendChild(empty);
  }

  // Erzeugt die obere Zeile (Label/Wert) eines Umweltbalkens.
  function createMetricBarTop(row) {
    var top = document.createElement("div");
    top.className = "detail-bar-top";

    var label = document.createElement("span");
    label.textContent = row.label;
    var value = document.createElement("span");
    value.textContent = row.valueText;
    top.appendChild(label);
    top.appendChild(value);
    return top;
  }

  // Erzeugt Track + dynamisch eingefaerbte Fuelle fuer einen Umweltbalken.
  function createMetricBarTrack(row, clampPct) {
    var track = document.createElement("div");
    track.className = "detail-bar-track";

    var fill = document.createElement("span");
    fill.className = "detail-bar-fill";
    fill.style.width = row.pct + "%";

    var ratio = clampPct(row.pct) / 100;
    var tone = BAR_TONE_COLORS[row.tone] || { start: "#8fb69c", end: "#2f6b47" };
    var dynamicEnd = mixToneColor(tone.start, tone.end, ratio);
    fill.style.background = "linear-gradient(90deg, " + tone.start + " 0%, " + dynamicEnd + " 100%)";

    track.appendChild(fill);
    return track;
  }

  // Erzeugt eine einzelne Balken-Zeile fuer Umweltdaten.
  function createMetricBarRow(row, clampPct) {
    var wrap = document.createElement("div");
    wrap.className = "detail-bar-row" + (row.tone ? " detail-bar-row--" + row.tone : "");
    wrap.appendChild(createMetricBarTop(row));
    wrap.appendChild(createMetricBarTrack(row, clampPct));
    return wrap;
  }

  // Rendert den kompakten Sticky-Header fuer den Detailbereich.
  function renderStickyHeader(ctx) {
    var detail = (ctx && ctx.detail) || {};
    var formatCodeValue = ctx && ctx.formatCodeValue;
    var formatOneDecimal = ctx && ctx.formatOneDecimal;
    var soilPhBandLabel = ctx && ctx.soilPhBandLabel;
    var elevationText = ctx && ctx.elevationText;

    if (typeof formatCodeValue !== "function") return;
    if (typeof formatOneDecimal !== "function") return;
    if (typeof soilPhBandLabel !== "function") return;
    if (typeof elevationText !== "function") return;

    var sticky = $("detailSticky");
    if (!sticky) return;
    var location = (detail.meta && detail.meta.location) || {};
    var raw = (detail.ee && detail.ee.raw) || {};

    populateStickyFields({
      detail: detail,sticky: sticky, raw: raw,location: location,
      formatCodeValue: formatCodeValue, formatOneDecimal: formatOneDecimal,
      soilPhBandLabel: soilPhBandLabel, elevationText: elevationText,
    });
  }

  // Steuert das Ein-/Ausblenden des Sticky-Headers ueber den Scrollzustand.
  function setupStickyVisibility() {
    var sticky = $("detailSticky");
    var title = $("detailTitle");
    if (!sticky || !title) return;

    if (stickyObserver) {
      stickyObserver.disconnect();
      stickyObserver = null;
    }

    var heroSection = title.closest(".detail-panel") || title;
    if (!("IntersectionObserver" in window)) {
      sticky.classList.remove("is-hidden");
      return;
    }

    stickyObserver = new IntersectionObserver(
      function (entries) {
        var entry = entries && entries[0];
        if (!entry) return;
        if (entry.isIntersecting) {
          sticky.classList.add("is-hidden");
        } else {
          sticky.classList.remove("is-hidden");
        }
      },
      { threshold: 0.15 }
    );

    stickyObserver.observe(heroSection);
  }

  // Rendert die Klima-/Standort-Chips unterhalb der Umweltdaten.
  function renderClimateChips(ctx) {
    var detail = (ctx && ctx.detail) || {};
    var formatCodeValue = ctx && ctx.formatCodeValue;
    var formatOneDecimal = ctx && ctx.formatOneDecimal;
    var soilPhBandLabel = ctx && ctx.soilPhBandLabel;
    var landcoverText = ctx && ctx.landcoverText;

    if (typeof formatCodeValue !== "function") return;
    if (typeof formatOneDecimal !== "function") return;
    if (typeof soilPhBandLabel !== "function") return;

    var chipsEl = $("detailClimateChips");
    if (!chipsEl) return;

    var meta = detail.meta || {};
    var location = meta.location || {};
    var ee = detail.ee || {};
    var bands = ee.bands || {};
    var raw = ee.raw || {};
    var chipPhText = formatSoilPhText(location, formatOneDecimal, soilPhBandLabel, formatCodeValue, detail);
    var chips = buildClimateChipRows(detail, bands, raw, formatCodeValue, chipPhText, landcoverText);
    renderChipElements(chipsEl, chips);
  }

  // Rendert die Mediengalerie inklusive Metadaten pro Bild.
  function renderMedia(ctx) {
    var mediaItems = (ctx && ctx.mediaItems) || [];
    var mediaGrid = $("detailMediaGrid");
    var mediaCount = $("detailMediaCount");
    if (!mediaGrid || !mediaCount) return;

    mediaGrid.innerHTML = "";
    mediaCount.textContent = mediaItems.length + " Bild" + (mediaItems.length === 1 ? "" : "er");

    if (!mediaItems.length) {
      renderMediaEmpty(mediaGrid);
      return;
    }

    mediaItems.forEach(function (item, index) {
      mediaGrid.appendChild(createMediaCard(item, index));
    });
  }

  // Rendert ein Definitionslisten-Blockpaar aus [Label, Wert]-Zeilen.
  function renderKeyValue(ctx) {
    var dl = ctx && ctx.dl;
    var rows = (ctx && ctx.rows) || [];
    var formatValue = ctx && ctx.formatValue;
    if (!dl || typeof formatValue !== "function") return;

    dl.innerHTML = "";
    rows.forEach(function (row) {
      var label = row[0];
      var value = row[1];
      if (value === undefined) return;
      var dt = document.createElement("dt");
      dt.textContent = label;
      var dd = document.createElement("dd");
      dd.textContent = formatValue(value);
      dl.appendChild(dt);
      dl.appendChild(dd);
    });
  }

  // Rendert das Hero-Bild oder einen Platzhaltertext auf der Detailseite.
  function renderHero(ctx) {
    var detail = (ctx && ctx.detail) || {};
    var hero = $("detailHeroFigure");
    if (!hero) return;

    hero.innerHTML = "";
    if (detail.imageUrl) {
      var image = document.createElement("img");
      image.src = detail.imageUrl;
      image.alt = detail.name || "Kaefer";
      hero.appendChild(image);
      return;
    }

    var noImage = document.createElement("p");
    noImage.className = "detail-muted";
    noImage.textContent = "Kein Vorschaubild verfuegbar.";
    hero.appendChild(noImage);
  }

  var BAR_TONE_COLORS = {
    temp: { start: "#f3b087", end: "#bf4b1a" },
    precip: { start: "#9bc6ea", end: "#2667a3" },
    moisture: { start: "#8fd6cb", end: "#22786b" },
    ndvi: { start: "#98cc98", end: "#387b38" },
    humidity: { start: "#8eb8dc", end: "#1f5f98" },
    pressure: { start: "#b0b0de", end: "#5f5fa2" },
    light: { start: "#e8cd8f", end: "#b68424" },
    slope: { start: "#c3b8a6", end: "#736751" },
    water: { start: "#8bc4c6", end: "#2b7578" },
    impact: { start: "#cfa292", end: "#8d5140" },
  };

  // Parst einen Hex-Farbwert in RGB-Kanäle.
  function parseHexColor(hex) {
    var clean = String(hex || "").replace("#", "").trim();
    if (clean.length !== 6) return null;
    var r = parseInt(clean.slice(0, 2), 16);
    var g = parseInt(clean.slice(2, 4), 16);
    var b = parseInt(clean.slice(4, 6), 16);
    if (!Number.isFinite(r) || !Number.isFinite(g) || !Number.isFinite(b)) return null;
    return { r: r, g: g, b: b };
  }

  // Interpoliert zwei Farben fuer einen dynamischen Balkenverlauf.
  function mixToneColor(startHex, endHex, ratio) {
    var start = parseHexColor(startHex);
    var end = parseHexColor(endHex);
    if (!start || !end) return endHex || startHex || "#2f6b47";
    var t = Math.max(0, Math.min(1, Number(ratio) || 0));
    var r = Math.round(start.r + (end.r - start.r) * t);
    var g = Math.round(start.g + (end.g - start.g) * t);
    var b = Math.round(start.b + (end.b - start.b) * t);
    return "rgb(" + r + ", " + g + ", " + b + ")";
  }

  // Rendert die Umwelt-Balken inklusive dynamischer Farbverlaeufe.
  function renderMetricBars(ctx) {
    var rows = (ctx && ctx.rows) || [];
    var clampPct = ctx && ctx.clampPct;
    var barsEl = $("detailMetricBars");
    if (!barsEl || typeof clampPct !== "function") return;

    barsEl.innerHTML = "";
    rows.forEach(function (row) {
      barsEl.appendChild(createMetricBarRow(row, clampPct));
    });
  }

  window.DetailUI = {
    renderStickyHeader: renderStickyHeader, setupStickyVisibility: setupStickyVisibility,
    renderClimateChips: renderClimateChips, renderMedia: renderMedia,
    renderKeyValue: renderKeyValue, renderHero: renderHero,
    renderMetricBars: renderMetricBars,
  };
})();
