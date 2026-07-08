-- ============================================================================
--  Ops: Performance-Indizes fuer kartenbezogene Backend-Abfragen
--  Rolle beim DB-Aufbau: Optimierungs-/Migrationsschritt nach dem Basis-Schema.
--  Mehrfach ausfuehrbar: jedes CREATE ist ueber information_schema abgesichert.
-- ============================================================================

USE beetle_db;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'location'
        AND index_name = 'idx_location_lat_lng'
    ),
    'SELECT "idx_location_lat_lng already exists"',
    'CREATE INDEX idx_location_lat_lng ON location (latitude, longitude)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND index_name = 'idx_observation_location_gbif'
    ),
    'SELECT "idx_observation_location_gbif already exists"',
    'CREATE INDEX idx_observation_location_gbif ON observation (location_id, gbif_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'climate_snapshot'
        AND index_name = 'idx_climate_snapshot_location_date'
    ),
    'SELECT "idx_climate_snapshot_location_date already exists"',
    'CREATE INDEX idx_climate_snapshot_location_date ON climate_snapshot (location_id, snapshot_date)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND index_name = 'idx_observation_location_beetle'
    ),
    'SELECT "idx_observation_location_beetle already exists"',
    'CREATE INDEX idx_observation_location_beetle ON observation (location_id, beetle_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'location'
        AND index_name = 'idx_location_lon_lat'
    ),
    'SELECT "idx_location_lon_lat already exists"',
    'CREATE INDEX idx_location_lon_lat ON location (longitude, latitude)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'media'
        AND index_name = 'idx_media_gbif_license'
    ),
    'SELECT "idx_media_gbif_license already exists"',
    'CREATE INDEX idx_media_gbif_license ON media (gbif_id, license)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
