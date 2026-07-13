(function () {
  const CLIMATE_LABELS = {
    A: "A Tropisch",
    B: "B Arid",
    C: "C Gemaessigt",
    D: "D Kalt",
    E: "E Polar",
    cold: "D/E Kalt/Polar",
    mild: "C Gemaessigt",
    warm: "B Arid",
    hot: "A Tropisch",
    unknown: "Unbekannt",
  };

  const VEGETATION_LABELS = {
    tree_cover: "Wald",
    shrubland: "Buschland",
    grassland: "Grasland",
    cropland: "Ackerland",
    built_up: "Bebaut",
    bare_sparse: "Vegetationsarm",
    snow_ice: "Schnee/Eis",
    water: "Wasser",
    wetland: "Feuchtgebiet",
    mangroves: "Mangroven",
    moss_lichen: "Moos/Flechten",
    unknown: "Unbekannt",
  };

  const COUNTRY_NAME_TO_ISO = {
    ARGENTINA: "AR",
    BELIZE: "BZ",
    BOLIVIA: "BO",
    BRAZIL: "BR",
    CHILE: "CL",
    COLOMBIA: "CO",
    "COSTA RICA": "CR",
    CUBA: "CU",
    "DOMINICAN REPUBLIC": "DO",
    ECUADOR: "EC",
    "EL SALVADOR": "SV",
    "FRENCH GUIANA": "GF",
    GUATEMALA: "GT",
    GUYANA: "GY",
    HAITI: "HT",
    HONDURAS: "HN",
    JAMAICA: "JM",
    MEXICO: "MX",
    NICARAGUA: "NI",
    PANAMA: "PA",
    PARAGUAY: "PY",
    PERU: "PE",
    "PUERTO RICO": "PR",
    SURINAME: "SR",
    URUGUAY: "UY",
    VENEZUELA: "VE",
  };

  const ISO_TO_COUNTRY_NAME = {
    AR: "Argentina",
    BZ: "Belize",
    BO: "Bolivia",
    BR: "Brazil",
    CL: "Chile",
    CO: "Colombia",
    CR: "Costa Rica",
    CU: "Cuba",
    DO: "Dominican Republic",
    EC: "Ecuador",
    SV: "El Salvador",
    GF: "French Guiana",
    GT: "Guatemala",
    GY: "Guyana",
    HT: "Haiti",
    HN: "Honduras",
    JM: "Jamaica",
    MX: "Mexico",
    NI: "Nicaragua",
    PA: "Panama",
    PY: "Paraguay",
    PE: "Peru",
    PR: "Puerto Rico",
    SR: "Suriname",
    UY: "Uruguay",
    VE: "Venezuela",
  };

  const labelPositions = {
    Argentina: [-38, -64],
    Belize: [17.2, -88.7],
    Bolivia: [-17, -64],
    Brazil: [-10, -53],
    Chile: [-30, -71],
    Colombia: [4.5, -73],
    "Costa Rica": [9.8, -84.1],
    Cuba: [21.8, -79],
    "Dominican Republic": [19, -70.2],
    Ecuador: [-1.6, -78.4],
    "El Salvador": [13.8, -88.9],
    "French Guiana": [4.1, -53.1],
    Guatemala: [15.5, -90.3],
    Guyana: [5, -58.9],
    Haiti: [19, -72.4],
    Honduras: [14.8, -86.6],
    Jamaica: [18.1, -77.3],
    Mexico: [23, -102],
    Nicaragua: [12.8, -85],
    Panama: [8.6, -80.1],
    Paraguay: [-23.4, -58.4],
    Peru: [-9.5, -75],
    "Puerto Rico": [18.2, -66.5],
    Suriname: [4.1, -55.9],
    Uruguay: [-32.8, -56],
    Venezuela: [7, -66],
  };

  const tinyLabels = new Set([
    "Belize",
    "Costa Rica",
    "Dominican Republic",
    "El Salvador",
    "French Guiana",
    "Guyana",
    "Haiti",
    "Jamaica",
    "Panama",
    "Puerto Rico",
    "Suriname",
    "Uruguay",
  ]);

  const SOIL_PH_BAND_LABELS = {
    strongly_acidic: "stark sauer",
    acidic: "sauer",
    neutral: "neutral",
    alkaline: "alkalisch",
    strongly_alkaline: "stark alkalisch",
  };

  // Gemeinsame Uebersetzungen technischer Klassifikations-Codes fuer UI-Texte.
  const CODE_VALUE_DE = {
    a: "A Tropisch",
    b: "B Arid",
    c: "C Gemaessigt",
    d: "D Kalt",
    e: "E Polar",
    unknown: "Unbekannt",
    cold: "Kalt",
    mild: "Mild",
    warm: "Warm",
    hot: "Heiss",
    tree_cover: "Wald",
    shrubland: "Buschland",
    grassland: "Grasland",
    cropland: "Ackerland",
    built_up: "Bebaut",
    bare_sparse: "Vegetationsarm",
    wetland: "Feuchtgebiet",
    mangroves: "Mangroven",
    water: "Wasser",
    snow_ice: "Schnee/Eis",
    moss_lichen: "Moos/Flechten",
    complete_date: "Vollstaendiges Datum",
    year_month_only: "Nur Jahr/Monat",
    year_only: "Nur Jahr",
    missing_or_invalid: "Fehlend oder ungueltig",
    observation: "Beobachtung",
    specimen_or_collection: "Praeparat oder Sammlung",
    machine_or_sensor: "Maschinell oder Sensor",
    unknown_basis: "Unbekannte Nachweisart",
    unresolved: "Unaufgeloest",
    species_level: "Artniveau",
    genus_level: "Gattungsniveau",
    higher_level: "Hoehere Taxonstufe",
    no_images: "Keine Bilder",
    one_image: "Ein Bild",
    multiple_images: "Mehrere Bilder",
    open: "Offen",
    restricted_or_unclear: "Eingeschraenkt oder unklar",
    very_low: "Sehr niedrig",
    low: "Niedrig",
    medium: "Mittel",
    high: "Hoch",
    very_high: "Sehr hoch",
    very_dry: "Sehr trocken",
    dry: "Trocken",
    moderate: "Moderat",
    humid: "Feucht",
    wet: "Nass",
    very_humid: "Sehr feucht",
    moist: "Feucht",
    arid: "Sehr trocken (arid)",
    semi_arid: "Halbtrocken (semiarid)",
    sub_humid: "Maessig feucht (subhumid)",
    per_humid: "Sehr feucht (perhumid)",
    barren: "Vegetationslos",
    sparse_vegetation: "Spaerliche Vegetation",
    moderate_vegetation: "Mittlere Vegetation",
    dense_vegetation: "Dichte Vegetation",
    dry_air: "Trockene Luft",
    normal_air: "Normale Luftfeuchte",
    moderate_humidity: "Mittlere Luftfeuchte",
    humid_air: "Feuchte Luft",
    very_humid_air: "Sehr feuchte Luft",
    extreme_low_pressure: "Extrem niedriger Luftdruck",
    very_low_pressure: "Sehr niedriger Luftdruck",
    low_pressure: "Niedriger Luftdruck",
    normal_pressure: "Normaler Luftdruck",
    high_pressure: "Hoher Luftdruck",
    dark: "Dunkel",
    dim_light: "Schwach beleuchtet",
    low_light: "Schwach beleuchtet",
    moderate_light: "Maessig beleuchtet",
    bright_light: "Hell beleuchtet",
    level: "Eben",
    gentle: "Leicht geneigt",
    undulating: "Wellig",
    steep: "Steil",
    very_steep: "Sehr steil",
    riparian: "Ufernah",
    near_water: "Gewaessernah",
    intermediate_distance: "Mittlere Gewaesserdistanz",
    inland: "Binnenland",
    far_inland: "Weit im Binnenland",
    natural: "Naturnah",
    low_modification: "Geringe Veraenderung",
    moderate_modification: "Mittlere Veraenderung",
    high_modification: "Hohe Veraenderung",
    strong_modification: "Sehr starke Veraenderung",
    mixed_cover: "Gemischte Bedeckung",
    very_low_carbon: "Sehr niedriger Kohlenstoffgehalt",
    moderate_carbon: "Mittlerer Kohlenstoffgehalt",
    high_carbon: "Hoher Kohlenstoffgehalt",
    low_carbon: "Niedriger Kohlenstoffgehalt",
    very_high_carbon: "Sehr hoher Kohlenstoffgehalt",
    unklar_oder_restriktiv: "Unklar oder restriktiv",
    mehrere_bilder: "Mehrere Bilder",
    eine_abbildung: "Ein Bild",
    keine_bilder: "Keine Bilder",
    vollstaendig: "Vollstaendiges Datum (YYYY-MM-DD)",
    jahr_monat: "Nur Jahr und Monat (YYYY-MM)",
    nur_jahr: "Nur Jahr (YYYY)",
    frei_text: "Freitext oder Zeitraum (nicht exakt YYYY-MM-DD)",
    artniveau: "Artniveau",
    beobachtung: "Beobachtung",
  };

  const LATAM_BOUNDS = {
    west: -160,
    south: -58,
    east: -32,
    north: 34,
  };

  // Fuehrt die zugehoerige Logik fuer diese Funktion aus.
  function climateLabel(code) {
    if (code === null || code === undefined) return "Unbekannt";
    var raw = String(code).trim();
    if (!raw) return "Unbekannt";
    var upper = raw.toUpperCase();
    var lower = raw.toLowerCase();
    return CLIMATE_LABELS[raw] ?? CLIMATE_LABELS[upper] ?? CLIMATE_LABELS[lower] ?? raw;
  }

  // Fuehrt die zugehoerige Logik fuer diese Funktion aus.
  function vegetationLabel(code) {
    if (code === null || code === undefined) return "Unbekannt";
    var raw = String(code).trim();
    if (!raw) return "Unbekannt";
    var lower = raw.toLowerCase();
    return VEGETATION_LABELS[raw] ?? VEGETATION_LABELS[lower] ?? raw;
  }

  // ESA-WorldCover-Klassencodes (10..100) auf deutsche Bezeichnungen abbilden.
  var LANDCOVER_CLASS_LABELS = {
    "10": "Wald",
    "20": "Buschland",
    "30": "Grasland",
    "40": "Ackerland",
    "50": "Bebaut",
    "60": "Vegetationsarm",
    "70": "Schnee/Eis",
    "80": "Wasser",
    "90": "Feuchtgebiet",
    "95": "Mangroven",
    "100": "Moos/Flechten",
  };

  // Uebersetzt einen numerischen Landbedeckungs-Code in eine deutsche Bezeichnung.
  function landcoverClassLabel(code) {
    if (code === null || code === undefined || code === "") return null;
    var key = String(code).trim();
    if (!key) return null;
    return LANDCOVER_CLASS_LABELS[key] || null;
  }

  window.AppCatalog = {
    CLIMATE_LABELS,
    VEGETATION_LABELS,
    COUNTRY_NAME_TO_ISO,
    ISO_TO_COUNTRY_NAME,
    labelPositions,
    tinyLabels,
    SOIL_PH_BAND_LABELS,
    CODE_VALUE_DE,
    LANDCOVER_CLASS_LABELS,
    LATAM_BOUNDS,
    climateLabel,
    vegetationLabel,
    landcoverClassLabel,
  };
})();
