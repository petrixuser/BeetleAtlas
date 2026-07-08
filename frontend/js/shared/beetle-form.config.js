(function () {
  var BASIS_OF_RECORD = [
    "HUMAN_OBSERVATION",
    "MACHINE_OBSERVATION",
    "PRESERVED_SPECIMEN",
  ];

  var LATAM_BOUNDS = {
    minLat: -56.0,
    maxLat: 33.5,
    minLon: -118.5,
    maxLon: -30.0,
  };

  // type: text | url | number | textarea | select ; section: core | advanced
  var FIELD_SPECS = [
    { key: "scientific_name", label: "Wissenschaftlicher Name", type: "text", section: "core", required: true },
    { key: "family", label: "Familie", type: "text", section: "core", required: true },
    { key: "genus", label: "Gattung", type: "text", section: "core" },
    { key: "specific_epithet", label: "Art-Epitheton", type: "text", section: "core" },
    { key: "event_date", label: "Funddatum", type: "text", section: "core", placeholder: "JJJJ-MM-TT", hint: "Format: JJJJ, JJJJ-MM oder JJJJ-MM-TT" },
    { key: "country", label: "Land", type: "text", section: "core" },
    { key: "latitude", label: "Breitengrad", type: "number", section: "core", min: -56, max: 33.5, step: "any", placeholder: "z. B. -12.34", hint: "Dezimalgrad, nur Lateinamerika (-56 bis 33.5)." },
    { key: "longitude", label: "Längengrad", type: "number", section: "core", min: -118.5, max: -30, step: "any", placeholder: "z. B. -70.12", hint: "Dezimalgrad, nur Lateinamerika (-118.5 bis -30)." },
    { key: "image_url", label: "Bild-URLs", type: "textarea", section: "core", placeholder: "https://... (eine URL pro Zeile)", hint: "Mehrere Bilder moeglich: eine URL pro Zeile." },
    { key: "notes", label: "Notizen", type: "textarea", section: "core" },

    { key: "scientific_name_authorship", label: "Autorschaft", type: "text", section: "advanced" },
    { key: "taxon_id", label: "Taxon-ID", type: "text", section: "advanced" },
    { key: "recorded_by", label: "Gesammelt von", type: "text", section: "advanced" },
    { key: "identified_by", label: "Bestimmt von", type: "text", section: "advanced" },
    { key: "identification_id", label: "Bestimmungs-ID", type: "text", section: "advanced" },
    { key: "basis_of_record", label: "Art des Nachweises", type: "select", section: "advanced", options: BASIS_OF_RECORD },
    { key: "catalogue_number", label: "Katalognummer", type: "text", section: "advanced" },
    { key: "institution_code", label: "Institution", type: "text", section: "advanced" },
    { key: "dataset_name", label: "Datensatz", type: "text", section: "advanced" },
    { key: "region", label: "Region", type: "text", section: "advanced" },
    { key: "city", label: "Ort / Stadt", type: "text", section: "advanced" },
    { key: "verbatim_locality", label: "Fundort (Text)", type: "textarea", section: "advanced" },
    { key: "location", label: "Standort", type: "text", section: "advanced" },
    { key: "coordinate_uncertainty", label: "Koordinaten-Unsicherheit", type: "text", section: "advanced" },
    { key: "verbatim_event_date", label: "Funddatum (Originaltext)", type: "text", section: "advanced" },
    { key: "media_references", label: "Medien-Referenz", type: "text", section: "advanced" },
    { key: "media_creator", label: "Medien-Urheber", type: "text", section: "advanced" },
    { key: "media_publisher", label: "Medien-Herausgeber", type: "text", section: "advanced" },
    { key: "media_rights_holder", label: "Medien-Rechteinhaber", type: "text", section: "advanced" },
    { key: "media_license", label: "Medien-Lizenz", type: "text", section: "advanced" },
  ];

  window.BeetleFormConfig = {
    BASIS_OF_RECORD: BASIS_OF_RECORD,
    LATAM_BOUNDS: LATAM_BOUNDS,
    FIELD_SPECS: FIELD_SPECS,
  };
})();
