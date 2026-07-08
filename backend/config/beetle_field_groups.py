"""Kanonischer Katalog der Feldgruppen fuer den Kaefer-Schreib-Pfad.

Einzige Quelle fuer die Zuordnung "welches Payload-Feld gehoert in welche
Zieltabelle" (Core-Wiederverwendung). Wird von den SQL-Buildern
(config/sql/beetle_write_repository_sql.py) und vom Schreib-Repository
(repositories/beetle_write_repository.py) importiert, damit die Listen an
einer Stelle gepflegt werden.
"""

# Von der API beschreibbare Felder (Nicht-Umwelt). Wird vom Controller genutzt.
BEETLE_RECORD_MUTABLE_FIELDS = (
    "gbif_id",
    "taxon_id",
    "scientific_name",
    "scientific_name_authorship",
    "family",
    "genus",
    "specific_epithet",
    "recorded_by",
    "catalogue_number",
    "identification_id",
    "identified_by",
    "event_date",
    "verbatim_event_date",
    "basis_of_record",
    "dataset_name",
    "institution_code",
    "image_available",
    "image_url",
    "media_references",
    "media_creator",
    "media_publisher",
    "media_rights_holder",
    "media_license",
    "latitude",
    "longitude",
    "coordinate_uncertainty",
    "country",
    "region",
    "city",
    "verbatim_locality",
    "location",
    "notes",
)

# Umwelt-/EE-Felder (statisch -> location, dynamisch -> climate_snapshot).
BEETLE_RECORD_EE_FIELDS = (
    "elevation",
    "temperature",
    "precipitation",
    "soil_moisture",
    "ndvi",
    "relative_humidity",
    "surface_pressure_hpa",
    "nighttime_lights",
    "slope",
    "distance_to_water_m",
    "human_modification",
    "landcover_class",
    "ecoregion_id",
    "biome_id",
    "soil_ph",
    "soil_organic_carbon",
    "worldclim_bio01",
    "worldclim_bio12",
)

# Art (beetle_species).
BEETLE_RECORD_SPECIES_FIELDS = (
    "taxon_id",
    "family",
    "genus",
    "specific_epithet",
    "scientific_name",
    "scientific_name_authorship",
)

# Ort + statische Umwelt (location). 'location' (Anzeigestring) hat keine eigene
# Spalte mehr -> die View leitet ihn aus verbatim_locality/city/region/country ab.
BEETLE_RECORD_LOCATION_FIELDS = (
    "latitude",
    "longitude",
    "coordinate_uncertainty",
    "country",
    "region",
    "city",
    "verbatim_locality",
    "elevation",
    "slope",
    "landcover_class",
    "soil_ph",
    "soil_organic_carbon",
    "worldclim_bio01",
    "worldclim_bio12",
    "distance_to_water_m",
    "ecoregion_id",
    "biome_id",
    "human_modification",
)

# Dynamische Umwelt (climate_snapshot). Payload 'temperature' -> Spalte avg_temperature.
BEETLE_RECORD_CLIMATE_FIELDS = (
    "temperature",
    "precipitation",
    "soil_moisture",
    "ndvi",
    "relative_humidity",
    "surface_pressure_hpa",
    "nighttime_lights",
)

# Kernfelder der Zentraltabelle beetle_record_core (ohne beetle_id/location_id).
BEETLE_RECORD_CORE_FIELDS = (
    "gbif_id",
    "recorded_by",
    "catalogue_number",
    "identification_id",
    "identified_by",
    "event_date",
    "verbatim_event_date",
    "basis_of_record",
    "dataset_name",
    "institution_code",
    "notes",
)

# Medien (beetle_record_media).
BEETLE_RECORD_MEDIA_FIELDS = (
    "image_available",
    "image_url",
    "media_references",
    "media_creator",
    "media_publisher",
    "media_rights_holder",
    "media_license",
)
