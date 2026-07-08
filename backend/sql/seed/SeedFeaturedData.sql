-- ============================================================================
--  Seed: Vorgestellte ("featured") Kaefer aus featured-beetles.js
--  Zweck: laedt kuratierte Datensaetze ueber eine Zwischentabelle und legt
--  daraus Arten, reservierte Orte, climate_snapshots, beetle_record_core und
--  zugehoerige Medien an.
--  Rolle beim DB-Aufbau: optionaler Seed-Schritt fuer Schau-/Startseiten-Daten
--  (nach Core-Schema und Auth-Seed, da ein created_by-Benutzer noetig ist).
--  Idempotent/mehrfach ausfuehrbar: alte Featured-Datensaetze, deren Medien und
--  reservierte Orte/Snapshots (ID-Bereich >= 1000000000) werden zuvor geloescht
--  und neu aufgebaut.
-- ============================================================================

USE beetle_db;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS featured_beetle_record_stage;
CREATE TABLE featured_beetle_record_stage (
  stage_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  scientific_name VARCHAR(512) NOT NULL,
  family VARCHAR(255) NOT NULL,
  genus VARCHAR(255) NULL,
  specific_epithet VARCHAR(255) NULL,
  country VARCHAR(255) NULL,
  location VARCHAR(1024) NULL,
  notes TEXT NULL,
  event_date VARCHAR(128) NULL,
  verbatim_event_date VARCHAR(255) NULL,
  basis_of_record VARCHAR(128) NULL,
  dataset_name VARCHAR(512) NULL,
  institution_code VARCHAR(255) NULL,
  image_available TINYINT(1) NULL,
  image_url TEXT NULL,
  media_references TEXT NULL,
  media_creator VARCHAR(512) NULL,
  media_publisher VARCHAR(512) NULL,
  media_rights_holder VARCHAR(512) NULL,
  media_license VARCHAR(512) NULL,
  latitude DECIMAL(9,6) NULL,
  longitude DECIMAL(9,6) NULL,
  coordinate_uncertainty VARCHAR(128) NULL,
  region VARCHAR(255) NULL,
  city VARCHAR(255) NULL,
  verbatim_locality TEXT NULL,
  elevation DOUBLE NULL,
  temperature DOUBLE NULL,
  precipitation DOUBLE NULL,
  soil_moisture DOUBLE NULL,
  ndvi DOUBLE NULL,
  relative_humidity DOUBLE NULL,
  surface_pressure_hpa DOUBLE NULL,
  nighttime_lights DOUBLE NULL,
  slope DOUBLE NULL,
  distance_to_water_m DOUBLE NULL,
  human_modification DOUBLE NULL,
  landcover_class INT NULL,
  ecoregion_id INT NULL,
  biome_id INT NULL,
  soil_ph DOUBLE NULL,
  soil_organic_carbon DOUBLE NULL,
  worldclim_bio01 DOUBLE NULL,
  worldclim_bio12 DOUBLE NULL
) ENGINE=InnoDB;

LOAD DATA INFILE '/var/lib/mysql-files/featured_beetle_record_import.csv'
INTO TABLE featured_beetle_record_stage
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
  scientific_name,
  family,
  genus,
  specific_epithet,
  country,
  location,
  notes,
  event_date,
  verbatim_event_date,
  basis_of_record,
  dataset_name,
  institution_code,
  image_available,
  image_url,
  media_references,
  media_creator,
  media_publisher,
  media_rights_holder,
  media_license,
  latitude,
  longitude,
  coordinate_uncertainty,
  region,
  city,
  verbatim_locality,
  elevation,
  temperature,
  precipitation,
  soil_moisture,
  ndvi,
  relative_humidity,
  surface_pressure_hpa,
  nighttime_lights,
  slope,
  distance_to_water_m,
  human_modification,
  landcover_class,
  ecoregion_id,
  biome_id,
  soil_ph,
  soil_organic_carbon,
  worldclim_bio01,
  worldclim_bio12
);

SET @featured_created_by = (
  SELECT user_id
  FROM app_user
  WHERE is_active = 1
  ORDER BY (role = 'admin') DESC, user_id ASC
  LIMIT 1
);

-- Idempotent: alte Featured-Records, deren Medien und deren reservierte
-- Locations/Snapshots entfernen. Featured-Locations liegen im reservierten
-- ID-Bereich >= 1000000000 (GBIF nutzt kleinere IDs -> keine Kollision).
DELETE md FROM beetle_record_media md
  JOIN beetle_record_core r ON r.record_id = md.record_id
 WHERE r.dataset_name = 'featured-beetles.js';
DELETE FROM beetle_record_core WHERE dataset_name = 'featured-beetles.js';
DELETE FROM climate_snapshot WHERE location_id >= 1000000000;
DELETE FROM location WHERE location_id >= 1000000000;

-- 1) Fehlende Arten anlegen (dedupe per scientific_name -> "eine Art einmal gespeichert").
SET @species_base := (SELECT COALESCE(MAX(beetle_id), 0) FROM beetle_species);
INSERT INTO beetle_species (beetle_id, taxon_id, family, genus, specific_epithet, scientific_name, scientific_name_authorship)
SELECT
  @species_base + ROW_NUMBER() OVER (ORDER BY d.scientific_name),
  NULL, d.family, d.genus, d.specific_epithet, d.scientific_name, NULL
FROM (
  SELECT s.scientific_name AS scientific_name,
         MIN(s.family) AS family,
         MIN(NULLIF(s.genus, '')) AS genus,
         MIN(NULLIF(s.specific_epithet, '')) AS specific_epithet
  FROM featured_beetle_record_stage s
  WHERE s.scientific_name IS NOT NULL AND s.scientific_name <> ''
    AND s.scientific_name NOT IN (
      SELECT scientific_name FROM beetle_species WHERE scientific_name IS NOT NULL
    )
  GROUP BY s.scientific_name
) d;

-- 2) Orte je Featured-Record (reservierte, deterministische IDs) mit statischer Umwelt.
INSERT INTO location (
  location_id, latitude, longitude, coordinate_uncertainty, country, region, city,
  verbatim_locality, elevation, slope, landcover_class, soil_ph, soil_organic_carbon,
  worldclim_bio01, worldclim_bio12, distance_to_water_m, ecoregion_id, biome_id, human_modification
)
SELECT
  1000000000 + s.stage_id, s.latitude, s.longitude, NULLIF(s.coordinate_uncertainty, ''),
  NULLIF(s.country, ''), NULLIF(s.region, ''), NULLIF(s.city, ''), NULLIF(s.verbatim_locality, ''),
  s.elevation, s.slope, s.landcover_class, s.soil_ph, s.soil_organic_carbon,
  s.worldclim_bio01, s.worldclim_bio12, s.distance_to_water_m, s.ecoregion_id, s.biome_id, s.human_modification
FROM featured_beetle_record_stage s
WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL;

-- 3) Dynamische Umwelt als climate_snapshot je Featured-Ort (auf gueltige Bereiche begrenzt).
INSERT INTO climate_snapshot (
  location_id, snapshot_date, avg_temperature, precipitation, soil_moisture, ndvi,
  relative_humidity, surface_pressure_hpa, nighttime_lights
)
SELECT
  1000000000 + s.stage_id, '2020-01-01', s.temperature, s.precipitation,
  CASE WHEN s.soil_moisture BETWEEN 0 AND 1 THEN s.soil_moisture ELSE NULL END,
  CASE WHEN s.ndvi BETWEEN -1 AND 1 THEN s.ndvi ELSE NULL END,
  CASE WHEN s.relative_humidity BETWEEN 0 AND 100 THEN s.relative_humidity ELSE NULL END,
  s.surface_pressure_hpa,
  CASE WHEN s.nighttime_lights IS NOT NULL AND s.nighttime_lights >= 0 THEN s.nighttime_lights ELSE NULL END
FROM featured_beetle_record_stage s
WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL;

-- 4) beetle_record_core: verweist auf Art (per Name) + reservierten Ort.
INSERT INTO beetle_record_core (
  record_id, beetle_id, location_id, event_date, verbatim_event_date, basis_of_record,
  dataset_name, institution_code, notes, status, created_by
)
SELECT
  ROW_NUMBER() OVER (ORDER BY s.scientific_name),
  sp.beetle_id, 1000000000 + s.stage_id, NULLIF(s.event_date, ''), NULLIF(s.verbatim_event_date, ''),
  NULLIF(s.basis_of_record, ''), NULLIF(s.dataset_name, ''), NULLIF(s.institution_code, ''),
  NULLIF(s.notes, ''), 'active', @featured_created_by
FROM featured_beetle_record_stage s
JOIN (
  SELECT scientific_name, MIN(beetle_id) AS beetle_id
  FROM beetle_species WHERE scientific_name IS NOT NULL
  GROUP BY scientific_name
) sp ON sp.scientific_name = s.scientific_name
WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
  AND @featured_created_by IS NOT NULL;

-- 5) Medien je Featured-Record (Zuordnung ueber die reservierte location_id).
INSERT INTO beetle_record_media (
  record_id, image_available, image_url, media_references, media_creator,
  media_publisher, media_rights_holder, media_license
)
SELECT
  r.record_id, s.image_available, NULLIF(s.image_url, ''), NULLIF(s.media_references, ''),
  NULLIF(s.media_creator, ''), NULLIF(s.media_publisher, ''), NULLIF(s.media_rights_holder, ''),
  NULLIF(s.media_license, '')
FROM featured_beetle_record_stage s
JOIN beetle_record_core r
  ON r.location_id = 1000000000 + s.stage_id
 AND r.dataset_name = 'featured-beetles.js'
WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL;

SET FOREIGN_KEY_CHECKS = 1;

SELECT @featured_created_by AS featured_created_by_user_id;
SELECT COUNT(*) AS featured_stage_rows FROM featured_beetle_record_stage;
SELECT COUNT(*) AS featured_inserted_rows FROM beetle_record_core WHERE dataset_name = 'featured-beetles.js';
