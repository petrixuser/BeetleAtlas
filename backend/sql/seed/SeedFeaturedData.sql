USE beetle_db;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS featured_beetle_record_stage;
CREATE TABLE featured_beetle_record_stage (
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

-- Idempotent refresh for this dataset source.
DELETE FROM beetle_record
WHERE dataset_name = 'featured-beetles.js';

INSERT INTO beetle_record (
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
  worldclim_bio12,
  status,
  created_by
)
SELECT
  s.scientific_name,
  s.family,
  NULLIF(s.genus, ''),
  NULLIF(s.specific_epithet, ''),
  NULLIF(s.country, ''),
  NULLIF(s.location, ''),
  NULLIF(s.notes, ''),
  NULLIF(s.event_date, ''),
  NULLIF(s.verbatim_event_date, ''),
  NULLIF(s.basis_of_record, ''),
  NULLIF(s.dataset_name, ''),
  NULLIF(s.institution_code, ''),
  s.image_available,
  NULLIF(s.image_url, ''),
  NULLIF(s.media_references, ''),
  NULLIF(s.media_creator, ''),
  NULLIF(s.media_publisher, ''),
  NULLIF(s.media_rights_holder, ''),
  NULLIF(s.media_license, ''),
  s.latitude,
  s.longitude,
  NULLIF(s.coordinate_uncertainty, ''),
  NULLIF(s.region, ''),
  NULLIF(s.city, ''),
  NULLIF(s.verbatim_locality, ''),
  s.elevation,
  s.temperature,
  s.precipitation,
  s.soil_moisture,
  s.ndvi,
  s.relative_humidity,
  s.surface_pressure_hpa,
  CASE WHEN s.nighttime_lights IS NOT NULL AND s.nighttime_lights < 0 THEN NULL ELSE s.nighttime_lights END,
  s.slope,
  s.distance_to_water_m,
  s.human_modification,
  s.landcover_class,
  s.ecoregion_id,
  s.biome_id,
  s.soil_ph,
  s.soil_organic_carbon,
  s.worldclim_bio01,
  s.worldclim_bio12,
  'active',
  @featured_created_by
FROM featured_beetle_record_stage s
WHERE @featured_created_by IS NOT NULL;

SET FOREIGN_KEY_CHECKS = 1;

SELECT @featured_created_by AS featured_created_by_user_id;
SELECT COUNT(*) AS featured_stage_rows FROM featured_beetle_record_stage;
SELECT COUNT(*) AS featured_inserted_rows FROM beetle_record WHERE dataset_name = 'featured-beetles.js';
