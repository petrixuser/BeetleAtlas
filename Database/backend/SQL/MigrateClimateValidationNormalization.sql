USE beetle_db;

-- Guard cleanup: normalize out-of-range legacy values before adding strict checks.
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
  SUM(CASE WHEN relative_humidity IS NOT NULL AND (relative_humidity < 0 OR relative_humidity > 100) THEN 1 ELSE 0 END) AS invalid_relative_humidity,
  SUM(CASE WHEN nighttime_lights IS NOT NULL AND nighttime_lights < 0 THEN 1 ELSE 0 END) AS invalid_nighttime_lights
FROM climate_snapshot;
