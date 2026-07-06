-- Consolidated core seed

USE beetle_db;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE media;
TRUNCATE TABLE observation;
TRUNCATE TABLE location;
TRUNCATE TABLE beetle_species;

LOAD DATA INFILE '/var/lib/mysql-files/beetle_species.csv'
INTO TABLE beetle_species
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(beetle_id, taxon_id, family, genus, specific_epithet, scientific_name, scientific_name_authorship);

LOAD DATA INFILE '/var/lib/mysql-files/location.csv'
INTO TABLE location
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(location_id, latitude, longitude, coordinate_uncertainty, country, region, city, verbatim_locality,
 elevation, slope, landcover_class, soil_ph, soil_organic_carbon, worldclim_bio01, worldclim_bio12,
 distance_to_water_m, ecoregion_id, biome_id, human_modification);

LOAD DATA INFILE '/var/lib/mysql-files/observation.csv'
INTO TABLE observation
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(gbif_id, recorded_by, catalogue_number, identification_id, identified_by,
 beetle_id, taxon_id, location_id, @event_date, verbatim_event_date, basis_of_record,
 dataset_name, institution_code, image_available)
SET
 event_date = @event_date,
 event_date_parsed = CASE
	 WHEN @event_date IS NULL OR TRIM(@event_date) = '' THEN NULL
	 WHEN @event_date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(@event_date, '%Y-%m-%d')
	 ELSE NULL
 END;

LOAD DATA INFILE '/var/lib/mysql-files/media.csv'
INTO TABLE media
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(media_id, gbif_id, image_url, `references`, creator, publisher, rights_holder, license);

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'beetle_species' AS table_name, COUNT(*) AS rows_count FROM beetle_species
UNION ALL SELECT 'location', COUNT(*) FROM location
UNION ALL SELECT 'observation', COUNT(*) FROM observation
UNION ALL SELECT 'media', COUNT(*) FROM media;


USE beetle_db;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS climate_snapshot_stage;
CREATE TABLE climate_snapshot_stage (
  location_id INT NOT NULL,
  snapshot_date DATE NOT NULL,
  avg_temperature FLOAT NULL,
  precipitation FLOAT NULL,
  soil_moisture FLOAT NULL,
  ndvi FLOAT NULL,
  relative_humidity FLOAT NULL,
  surface_pressure_hpa FLOAT NULL,
  nighttime_lights FLOAT NULL,
  KEY idx_css_loc_date (location_id, snapshot_date)
) ENGINE=InnoDB;

LOAD DATA INFILE '/var/lib/mysql-files/climate_snapshot_import.csv'
INTO TABLE climate_snapshot_stage
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(location_id, @snapshot_date, avg_temperature, precipitation, soil_moisture, ndvi, relative_humidity, surface_pressure_hpa, nighttime_lights)
SET snapshot_date = STR_TO_DATE(@snapshot_date, '%Y-%m-%d');

INSERT INTO climate_snapshot (
  location_id,
  snapshot_date,
  avg_temperature,
  precipitation,
  soil_moisture,
  ndvi,
  relative_humidity,
  surface_pressure_hpa,
  nighttime_lights
)
SELECT
  s.location_id,
  s.snapshot_date,
  s.avg_temperature,
  s.precipitation,
  CASE WHEN s.soil_moisture BETWEEN 0 AND 1 THEN s.soil_moisture ELSE NULL END AS soil_moisture,
  CASE WHEN s.ndvi BETWEEN -1 AND 1 THEN s.ndvi ELSE NULL END AS ndvi,
  CASE WHEN s.relative_humidity BETWEEN 0 AND 100 THEN s.relative_humidity ELSE NULL END AS relative_humidity,
  s.surface_pressure_hpa,
  CASE WHEN s.nighttime_lights >= 0 THEN s.nighttime_lights ELSE NULL END AS nighttime_lights
FROM climate_snapshot_stage s
INNER JOIN location l ON l.location_id = s.location_id
ON DUPLICATE KEY UPDATE
  avg_temperature = VALUES(avg_temperature),
  precipitation = VALUES(precipitation),
  soil_moisture = VALUES(soil_moisture),
  ndvi = VALUES(ndvi),
  relative_humidity = VALUES(relative_humidity),
  surface_pressure_hpa = VALUES(surface_pressure_hpa),
  nighttime_lights = VALUES(nighttime_lights);

SET FOREIGN_KEY_CHECKS = 1;

SELECT COUNT(*) AS climate_rows FROM climate_snapshot;
SELECT COUNT(*) AS climate_stage_rows FROM climate_snapshot_stage;


USE beetle_db;

INSERT INTO quality_report_history (
  source_label,
  observation_count,
  location_count,
  climate_snapshot_count,
  observation_null_rates_json,
  location_null_rates_json,
  climate_snapshot_null_rates_json,
  ee_coverage_json
)
WITH
totals AS (
  SELECT
    (SELECT COUNT(*) FROM observation) AS observation_count,
    (SELECT COUNT(*) FROM location) AS location_count,
    (SELECT COUNT(*) FROM climate_snapshot) AS climate_snapshot_count
),
observation_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'event_date', 'missing', SUM(CASE WHEN event_date IS NULL OR TRIM(event_date) = '' THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'event_date_parsed', 'missing', SUM(CASE WHEN event_date_parsed IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'basis_of_record', 'missing', SUM(CASE WHEN basis_of_record IS NULL OR TRIM(basis_of_record) = '' THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'taxon_id', 'missing', SUM(CASE WHEN taxon_id IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'location_id', 'missing', SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'image_available', 'missing', SUM(CASE WHEN image_available IS NULL THEN 1 ELSE 0 END))
  ) AS payload
  FROM observation
),
location_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'latitude', 'missing', SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'longitude', 'missing', SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'elevation', 'missing', SUM(CASE WHEN elevation IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'coordinate_uncertainty', 'missing', SUM(CASE WHEN coordinate_uncertainty IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'worldclim_bio01', 'missing', SUM(CASE WHEN worldclim_bio01 IS NULL OR worldclim_bio01 = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'worldclim_bio12', 'missing', SUM(CASE WHEN worldclim_bio12 IS NULL OR worldclim_bio12 = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_ph', 'missing', SUM(CASE WHEN soil_ph IS NULL OR soil_ph = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_organic_carbon', 'missing', SUM(CASE WHEN soil_organic_carbon IS NULL OR soil_organic_carbon = -9999 THEN 1 ELSE 0 END))
  ) AS payload
  FROM location
),
climate_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'avg_temperature', 'missing', SUM(CASE WHEN avg_temperature IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'precipitation', 'missing', SUM(CASE WHEN precipitation IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_moisture', 'missing', SUM(CASE WHEN soil_moisture IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'ndvi', 'missing', SUM(CASE WHEN ndvi IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'relative_humidity', 'missing', SUM(CASE WHEN relative_humidity IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'surface_pressure_hpa', 'missing', SUM(CASE WHEN surface_pressure_hpa IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'nighttime_lights', 'missing', SUM(CASE WHEN nighttime_lights IS NULL THEN 1 ELSE 0 END))
  ) AS payload
  FROM climate_snapshot
),
ee_coverage AS (
  SELECT JSON_OBJECT(
    'withSnapshotMatch', SUM(
      CASE WHEN EXISTS (
        SELECT 1
        FROM climate_snapshot cs
        WHERE cs.location_id = o.location_id
          AND cs.snapshot_date <= COALESCE(
            o.event_date_parsed,
            IF(LENGTH(o.event_date) >= 10, STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'), NULL),
            DATE('9999-12-31')
          )
      ) THEN 1 ELSE 0 END
    ),
    'withoutSnapshotMatch', GREATEST(COUNT(*) - SUM(
      CASE WHEN EXISTS (
        SELECT 1
        FROM climate_snapshot cs
        WHERE cs.location_id = o.location_id
          AND cs.snapshot_date <= COALESCE(
            o.event_date_parsed,
            IF(LENGTH(o.event_date) >= 10, STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'), NULL),
            DATE('9999-12-31')
          )
      ) THEN 1 ELSE 0 END
    ), 0)
  ) AS payload
  FROM observation o
)
SELECT
  'seed_import',
  t.observation_count,
  t.location_count,
  t.climate_snapshot_count,
  onl.payload,
  lnl.payload,
  cnl.payload,
  ee.payload
FROM totals t
CROSS JOIN observation_nulls onl
CROSS JOIN location_nulls lnl
CROSS JOIN climate_nulls cnl
CROSS JOIN ee_coverage ee;

SELECT
  quality_report_id,
  generated_at,
  source_label,
  observation_count,
  location_count,
  climate_snapshot_count
FROM quality_report_history
ORDER BY quality_report_id DESC
LIMIT 1;


-- END backend/sql/seed/RecordQualityReportSnapshot.sql

