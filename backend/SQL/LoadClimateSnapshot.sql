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
  -- Normalize out-of-range values to NULL on insert so the CHECK constraints
  -- defined in DatabseShema.sql are satisfied on a fresh DB. The schema already
  -- creates climate_snapshot WITH these constraints, so the legacy approach of
  -- "load first, normalize + add constraints later" (see
  -- MigrateClimateValidationNormalization.sql) cannot run before the seed here.
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
