USE beetle_db;

-- 1) observation.event_date_parsed column + backfill + index
SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND column_name = 'event_date_parsed'
    ),
    'SELECT "event_date_parsed already exists"',
    'ALTER TABLE observation ADD COLUMN event_date_parsed DATE NULL AFTER event_date'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE observation
SET event_date_parsed = CASE
  WHEN event_date IS NULL OR TRIM(event_date) = '' THEN NULL
  WHEN event_date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(event_date, '%Y-%m-%d')
  ELSE NULL
END
WHERE event_date_parsed IS NULL;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND index_name = 'idx_observation_event_date_parsed'
    ),
    'SELECT "idx_observation_event_date_parsed already exists"',
    'CREATE INDEX idx_observation_event_date_parsed ON observation (event_date_parsed)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) deterministic media pagination index
SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'media'
        AND index_name = 'idx_media_gbif_media_id'
    ),
    'SELECT "idx_media_gbif_media_id already exists"',
    'CREATE INDEX idx_media_gbif_media_id ON media (gbif_id, media_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3) quality report history table
SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = DATABASE()
        AND table_name = 'quality_report_history'
    ),
    'SELECT "quality_report_history already exists"',
    'CREATE TABLE quality_report_history (
      quality_report_id BIGINT NOT NULL AUTO_INCREMENT,
      generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      source_label VARCHAR(128) NULL,
      observation_count BIGINT NOT NULL,
      location_count BIGINT NOT NULL,
      climate_snapshot_count BIGINT NOT NULL,
      observation_null_rates_json JSON NOT NULL,
      location_null_rates_json JSON NOT NULL,
      climate_snapshot_null_rates_json JSON NOT NULL,
      ee_coverage_json JSON NOT NULL,
      PRIMARY KEY (quality_report_id),
      KEY idx_quality_report_generated_at (generated_at),
      KEY idx_quality_report_source (source_label)
    ) ENGINE=InnoDB'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4) domain checks with legacy-data guards
SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'location'
    AND constraint_name = 'chk_location_lat_lng'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM location
  WHERE latitude < -90 OR latitude > 90
     OR longitude < -180 OR longitude > 180
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_location_lat_lng already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_location_lat_lng due to invalid existing rows"',
    'ALTER TABLE location ADD CONSTRAINT chk_location_lat_lng CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'observation'
    AND constraint_name = 'chk_observation_image_available'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM observation
  WHERE image_available NOT IN (0, 1)
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_observation_image_available already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_observation_image_available due to invalid existing rows"',
    'ALTER TABLE observation ADD CONSTRAINT chk_observation_image_available CHECK (image_available IN (0, 1))'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_relative_humidity'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM climate_snapshot
  WHERE relative_humidity IS NOT NULL
    AND (relative_humidity < 0 OR relative_humidity > 100)
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_relative_humidity already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_climate_relative_humidity due to invalid existing rows"',
    'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_relative_humidity CHECK (relative_humidity IS NULL OR relative_humidity BETWEEN 0 AND 100)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_ndvi'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM climate_snapshot
  WHERE ndvi IS NOT NULL
    AND (ndvi < -1 OR ndvi > 1)
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_ndvi already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_climate_ndvi due to invalid existing rows"',
    'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_ndvi CHECK (ndvi IS NULL OR ndvi BETWEEN -1 AND 1)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_soil_moisture'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM climate_snapshot
  WHERE soil_moisture IS NOT NULL
    AND (soil_moisture < 0 OR soil_moisture > 1)
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_soil_moisture already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_climate_soil_moisture due to invalid existing rows"',
    'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_soil_moisture CHECK (soil_moisture IS NULL OR soil_moisture BETWEEN 0 AND 1)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_nighttime_lights'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM climate_snapshot
  WHERE nighttime_lights IS NOT NULL
    AND nighttime_lights < 0
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_nighttime_lights already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_climate_nighttime_lights due to invalid existing rows"',
    'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_nighttime_lights CHECK (nighttime_lights IS NULL OR nighttime_lights >= 0)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5) normalization fallback for legacy climate values and strict check enforcement
UPDATE climate_snapshot
SET relative_humidity = NULL
WHERE relative_humidity IS NOT NULL
  AND (relative_humidity < 0 OR relative_humidity > 100);

UPDATE climate_snapshot
SET nighttime_lights = NULL
WHERE nighttime_lights IS NOT NULL
  AND nighttime_lights < 0;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_relative_humidity'
    AND constraint_type = 'CHECK'
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_relative_humidity already exists"',
  'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_relative_humidity CHECK (relative_humidity IS NULL OR relative_humidity BETWEEN 0 AND 100)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'climate_snapshot'
    AND constraint_name = 'chk_climate_nighttime_lights'
    AND constraint_type = 'CHECK'
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_climate_nighttime_lights already exists"',
  'ALTER TABLE climate_snapshot ADD CONSTRAINT chk_climate_nighttime_lights CHECK (nighttime_lights IS NULL OR nighttime_lights >= 0)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT
  table_name,
  constraint_name,
  constraint_type
FROM information_schema.table_constraints
WHERE table_schema = DATABASE()
  AND constraint_type = 'CHECK'
  AND table_name IN ('location', 'observation', 'climate_snapshot')
ORDER BY table_name, constraint_name;
