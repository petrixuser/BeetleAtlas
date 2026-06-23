-- Consolidated read-model/quality migrations


-- BEGIN backend/sql/ops/MigrateDataQualityAndHistory.sql

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


-- END backend/sql/ops/MigrateDataQualityAndHistory.sql


-- BEGIN backend/sql/ops/MigrateMapPointReadModel.sql

USE beetle_db;

CREATE TABLE IF NOT EXISTS map_point_read (
  entity_id VARCHAR(64) NOT NULL,
  source_type VARCHAR(16) NOT NULL,
  record_id BIGINT NULL,
  gbif_id BIGINT NULL,
  observed_at VARCHAR(128) NULL,
  species_name VARCHAR(512) NOT NULL,
  family VARCHAR(255) NULL,
  location VARCHAR(1024) NULL,
  country VARCHAR(255) NULL,
  lat DECIMAL(9,6) NOT NULL,
  lng DECIMAL(9,6) NOT NULL,
  elevation DOUBLE NULL,
  climate VARCHAR(32) NOT NULL,
  vegetation VARCHAR(32) NOT NULL,
  elevation_group VARCHAR(32) NOT NULL,
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (entity_id),
  KEY idx_mpr_bbox_lng_lat (lng, lat),
  KEY idx_mpr_country_bbox (country, lng, lat),
  KEY idx_mpr_climate_bbox (climate, lng, lat),
  KEY idx_mpr_vegetation_bbox (vegetation, lng, lat),
  KEY idx_mpr_elevation_group_bbox (elevation_group, lng, lat),
  KEY idx_mpr_filters_bbox (climate, vegetation, elevation_group, country, lng, lat),
  KEY idx_mpr_observed_at (observed_at),
  KEY idx_mpr_source_record (source_type, record_id)
) ENGINE=InnoDB;

DROP PROCEDURE IF EXISTS refresh_map_point_read;
DELIMITER $$
CREATE PROCEDURE refresh_map_point_read()
BEGIN
  TRUNCATE TABLE map_point_read;

  INSERT INTO map_point_read (
    entity_id,
    source_type,
    record_id,
    gbif_id,
    observed_at,
    species_name,
    family,
    location,
    country,
    lat,
    lng,
    elevation,
    climate,
    vegetation,
    elevation_group,
    refreshed_at
  )
  SELECT
    CONCAT('occ-', o.gbif_id) AS entity_id,
    'observation' AS source_type,
    NULL AS record_id,
    o.gbif_id,
    o.event_date AS observed_at,
    bs.scientific_name AS species_name,
    bs.family,
    COALESCE(
      NULLIF(TRIM(l.verbatim_locality), ''),
      NULLIF(TRIM(CONCAT_WS(', ', l.city, l.region, l.country)), ''),
      NULLIF(TRIM(CONCAT_WS(', ', l.region, l.country)), ''),
      NULLIF(TRIM(l.country), ''),
      'Unbekannt'
    ) AS location,
    l.country,
    CAST(l.latitude AS DECIMAL(9,6)) AS lat,
    CAST(l.longitude AS DECIMAL(9,6)) AS lng,
    l.elevation,
    CASE
      WHEN (
        CASE
          WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
          WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
          ELSE l.worldclim_bio01
        END
      ) IS NULL
      AND (l.worldclim_bio12 IS NULL OR l.worldclim_bio12 = -9999) THEN 'unknown'
      WHEN (
        CASE
          WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
          WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
          ELSE l.worldclim_bio01
        END
      ) < 0 THEN 'E'
      WHEN l.worldclim_bio12 IS NOT NULL AND l.worldclim_bio12 <> -9999 AND l.worldclim_bio12 < 500 THEN 'B'
      WHEN (
        CASE
          WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
          WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
          ELSE l.worldclim_bio01
        END
      ) >= 18 THEN 'A'
      WHEN (
        CASE
          WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
          WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
          ELSE l.worldclim_bio01
        END
      ) < 10 THEN 'D'
      ELSE 'C'
    END AS climate,
    CASE
      WHEN l.biome_id IN (1, 2, 3, 4, 5, 6) THEN 'tree_cover'
      WHEN l.biome_id IN (7, 8, 10) THEN 'grassland'
      WHEN l.biome_id = 9 THEN 'wetland'
      WHEN l.biome_id = 11 THEN 'moss_lichen'
      WHEN l.biome_id = 12 THEN 'shrubland'
      WHEN l.biome_id = 13 THEN 'bare_sparse'
      WHEN l.biome_id = 14 THEN 'mangroves'
      WHEN l.landcover_class = 10 THEN 'tree_cover'
      WHEN l.landcover_class = 20 THEN 'shrubland'
      WHEN l.landcover_class = 30 THEN 'grassland'
      WHEN l.landcover_class = 40 THEN 'cropland'
      WHEN l.landcover_class = 50 THEN 'built_up'
      WHEN l.landcover_class = 60 THEN 'bare_sparse'
      WHEN l.landcover_class = 70 THEN 'snow_ice'
      WHEN l.landcover_class = 80 THEN 'water'
      WHEN l.landcover_class = 90 THEN 'wetland'
      WHEN l.landcover_class = 95 THEN 'mangroves'
      WHEN l.landcover_class = 100 THEN 'moss_lichen'
      ELSE 'unknown'
    END AS vegetation,
    CASE
      WHEN l.elevation IS NULL THEN '0_100'
      WHEN l.elevation < 100 THEN '0_100'
      WHEN l.elevation < 500 THEN '100_500'
      WHEN l.elevation < 1000 THEN '500_1000'
      WHEN l.elevation < 2000 THEN '1000_2000'
      WHEN l.elevation < 3000 THEN '2000_3000'
      WHEN l.elevation < 4500 THEN '3000_4500'
      ELSE '4500_plus'
    END AS elevation_group,
    NOW() AS refreshed_at
  FROM observation o
  JOIN location l ON l.location_id = o.location_id
  JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
  WHERE l.latitude IS NOT NULL
    AND l.longitude IS NOT NULL

  UNION ALL

  SELECT
    CONCAT('rec-', br.record_id) AS entity_id,
    'manual' AS source_type,
    br.record_id,
    br.gbif_id,
    br.event_date AS observed_at,
    br.scientific_name AS species_name,
    br.family,
    COALESCE(
      NULLIF(TRIM(br.location), ''),
      NULLIF(TRIM(br.verbatim_locality), ''),
      NULLIF(TRIM(CONCAT_WS(', ', br.city, br.region, br.country)), ''),
      NULLIF(TRIM(CONCAT_WS(', ', br.region, br.country)), ''),
      NULLIF(TRIM(br.country), ''),
      'Unbekannt'
    ) AS location,
    br.country,
    CAST(br.latitude AS DECIMAL(9,6)) AS lat,
    CAST(br.longitude AS DECIMAL(9,6)) AS lng,
    br.elevation,
    CASE
      WHEN COALESCE(br.temperature, br.worldclim_bio01) IS NULL
      AND COALESCE(br.precipitation, br.worldclim_bio12) IS NULL THEN 'unknown'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) < 0 THEN 'E'
      WHEN COALESCE(br.precipitation, br.worldclim_bio12) IS NOT NULL
           AND COALESCE(br.precipitation, br.worldclim_bio12) < 500 THEN 'B'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) >= 18 THEN 'A'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) < 10 THEN 'D'
      ELSE 'C'
    END AS climate,
    CASE
      WHEN br.biome_id IN (1, 2, 3, 4, 5, 6) THEN 'tree_cover'
      WHEN br.biome_id IN (7, 8, 10) THEN 'grassland'
      WHEN br.biome_id = 9 THEN 'wetland'
      WHEN br.biome_id = 11 THEN 'moss_lichen'
      WHEN br.biome_id = 12 THEN 'shrubland'
      WHEN br.biome_id = 13 THEN 'bare_sparse'
      WHEN br.biome_id = 14 THEN 'mangroves'
      WHEN br.landcover_class = 10 THEN 'tree_cover'
      WHEN br.landcover_class = 20 THEN 'shrubland'
      WHEN br.landcover_class = 30 THEN 'grassland'
      WHEN br.landcover_class = 40 THEN 'cropland'
      WHEN br.landcover_class = 50 THEN 'built_up'
      WHEN br.landcover_class = 60 THEN 'bare_sparse'
      WHEN br.landcover_class = 70 THEN 'snow_ice'
      WHEN br.landcover_class = 80 THEN 'water'
      WHEN br.landcover_class = 90 THEN 'wetland'
      WHEN br.landcover_class = 95 THEN 'mangroves'
      WHEN br.landcover_class = 100 THEN 'moss_lichen'
      ELSE 'unknown'
    END AS vegetation,
    CASE
      WHEN br.elevation IS NULL THEN '0_100'
      WHEN br.elevation < 100 THEN '0_100'
      WHEN br.elevation < 500 THEN '100_500'
      WHEN br.elevation < 1000 THEN '500_1000'
      WHEN br.elevation < 2000 THEN '1000_2000'
      WHEN br.elevation < 3000 THEN '2000_3000'
      WHEN br.elevation < 4500 THEN '3000_4500'
      ELSE '4500_plus'
    END AS elevation_group,
    NOW() AS refreshed_at
  FROM beetle_record br
  WHERE br.status = 'active'
    AND br.latitude IS NOT NULL
    AND br.longitude IS NOT NULL;
END$$
DELIMITER ;

CALL refresh_map_point_read();


-- END backend/sql/ops/MigrateMapPointReadModel.sql


-- BEGIN backend/sql/ops/AddMapPointReadListIndexes.sql

USE beetle_db;

-- Additional indexes for compact /api/beetles list queries on map_point_read.
-- Focus: filter columns + stable pagination order by entity_id.

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_country_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_country_entity ON map_point_read (country, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_climate_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_climate_entity ON map_point_read (climate, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_vegetation_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_vegetation_entity ON map_point_read (vegetation, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_elevation_group_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_elevation_group_entity ON map_point_read (elevation_group, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_observed_at_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_observed_at_entity ON map_point_read (observed_at, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'map_point_read'
        AND index_name = 'idx_mpr_list_filters_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_mpr_list_filters_entity ON map_point_read (country, climate, vegetation, elevation_group, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


-- END backend/sql/ops/AddMapPointReadListIndexes.sql


-- BEGIN backend/sql/ops/MigrateBeetleListReadModel.sql

USE beetle_db;

-- Materialized read model for fast /api/beetles compact list responses.
CREATE TABLE IF NOT EXISTS beetle_list_read (
  entity_id VARCHAR(64) NOT NULL,
  gbif_id BIGINT NULL,
  observed_at VARCHAR(128) NULL,
  observed_year SMALLINT NULL,
  name VARCHAR(512) NOT NULL,
  family VARCHAR(255) NULL,
  country VARCHAR(255) NULL,
  location VARCHAR(1024) NULL,
  climate VARCHAR(32) NOT NULL,
  vegetation VARCHAR(32) NOT NULL,
  elevation DOUBLE NULL,
  elevation_group VARCHAR(32) NOT NULL,
  lat DECIMAL(9,6) NOT NULL,
  lng DECIMAL(9,6) NOT NULL,
  has_image TINYINT(1) NOT NULL DEFAULT 0,
  soil_ph_band VARCHAR(32) NOT NULL DEFAULT 'unknown',
  temperature_band VARCHAR(32) NOT NULL DEFAULT 'unknown',
  precipitation_band VARCHAR(32) NOT NULL DEFAULT 'unknown',
  event_date_quality VARCHAR(32) NOT NULL DEFAULT 'unknown',
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (entity_id),
  KEY idx_blr_observed_at_entity (observed_at, entity_id),
  KEY idx_blr_country_entity (country, entity_id),
  KEY idx_blr_climate_entity (climate, entity_id),
  KEY idx_blr_vegetation_entity (vegetation, entity_id),
  KEY idx_blr_elevation_group_entity (elevation_group, entity_id),
  KEY idx_blr_bbox_lng_lat (lng, lat),
  KEY idx_blr_has_image_entity (has_image, entity_id),
  KEY idx_blr_soil_ph_band_entity (soil_ph_band, entity_id),
  KEY idx_blr_temperature_band_entity (temperature_band, entity_id),
  KEY idx_blr_precipitation_band_entity (precipitation_band, entity_id),
  KEY idx_blr_event_date_quality_entity (event_date_quality, entity_id),
  KEY idx_blr_observed_year_entity (observed_year, entity_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS beetle_list_meta_read (
  metric_key VARCHAR(64) NOT NULL,
  metric_value BIGINT NOT NULL,
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (metric_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS beetle_list_filter_count_read (
  dim_name VARCHAR(64) NOT NULL,
  dim_value VARCHAR(128) NOT NULL,
  cnt BIGINT NOT NULL,
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (dim_name, dim_value)
) ENGINE=InnoDB;

TRUNCATE TABLE beetle_list_read;

INSERT INTO beetle_list_read (
  entity_id,
  gbif_id,
  observed_at,
  observed_year,
  name,
  family,
  country,
  location,
  climate,
  vegetation,
  elevation,
  elevation_group,
  lat,
  lng,
  has_image,
  soil_ph_band,
  temperature_band,
  precipitation_band,
  event_date_quality,
  refreshed_at
)
SELECT
  m.entity_id,
  m.gbif_id,
  m.observed_at,
  CASE
    WHEN m.observed_at IS NULL THEN NULL
    WHEN CHAR_LENGTH(m.observed_at) >= 4 THEN CAST(SUBSTRING(m.observed_at, 1, 4) AS UNSIGNED)
    ELSE NULL
  END AS observed_year,
  m.species_name,
  m.family,
  m.country,
  m.location,
  m.climate,
  m.vegetation,
  m.elevation,
  m.elevation_group,
  m.lat,
  m.lng,
  CASE
    WHEN EXISTS (
      SELECT 1
      FROM media md
      WHERE md.gbif_id = m.gbif_id
        AND md.image_url IS NOT NULL
        AND TRIM(md.image_url) <> ''
    ) THEN 1
    ELSE 0
  END AS has_image,
  CASE
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 5.5 THEN 'strongly_acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 6.5 THEN 'acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 7.5 THEN 'neutral'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 8.5 THEN 'alkaline'
    ELSE 'strongly_alkaline'
  END AS soil_ph_band,
  CASE
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 5 THEN 'cold'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 15 THEN 'mild'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 25 THEN 'warm'
    ELSE 'hot'
  END AS temperature_band,
  CASE
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) IS NULL THEN 'unknown'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 250 THEN 'arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 500 THEN 'semi_arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 1000 THEN 'sub_humid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 2000 THEN 'humid'
    ELSE 'per_humid'
  END AS precipitation_band,
  CASE
    WHEN m.observed_at IS NULL OR TRIM(m.observed_at) = '' THEN 'unknown'
    WHEN m.observed_at REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN 'vollstaendig'
    WHEN m.observed_at REGEXP '^[0-9]{4}-[0-9]{2}$' THEN 'jahr_monat'
    WHEN m.observed_at REGEXP '^[0-9]{4}$' THEN 'nur_jahr'
    ELSE 'frei_text'
  END AS event_date_quality,
  NOW()
FROM map_point_read m
LEFT JOIN observation o
  ON m.source_type = 'observation'
 AND o.gbif_id = m.gbif_id
LEFT JOIN location l
  ON l.location_id = o.location_id
LEFT JOIN beetle_record br
  ON m.source_type = 'manual'
 AND br.record_id = m.record_id;

REPLACE INTO beetle_list_meta_read(metric_key, metric_value, refreshed_at)
SELECT 'total_rows', COUNT(*), NOW() FROM beetle_list_read;

TRUNCATE TABLE beetle_list_filter_count_read;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'has_image', CAST(has_image AS CHAR), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY has_image;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'country', COALESCE(country, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY country;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'climate', COALESCE(climate, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY climate;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'vegetation', COALESCE(vegetation, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY vegetation;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'elevation_group', COALESCE(elevation_group, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY elevation_group;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'soil_ph_band', COALESCE(soil_ph_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY soil_ph_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'temperature_band', COALESCE(temperature_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY temperature_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'precipitation_band', COALESCE(precipitation_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY precipitation_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'event_date_quality', COALESCE(event_date_quality, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY event_date_quality;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'observed_year', CAST(observed_year AS CHAR), COUNT(*), NOW()
FROM beetle_list_read
WHERE observed_year IS NOT NULL
GROUP BY observed_year;


-- END backend/sql/ops/MigrateBeetleListReadModel.sql


-- BEGIN backend/sql/ops/MigrateBeetleListReadModelRetrofitBundle.sql

USE beetle_db;

-- Retrofit bundle for databases that already had beetle_list_read before the
-- consolidated MigrateBeetleListReadModel.sql existed.

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND column_name = 'has_image'
    ),
    'SELECT 1',
    'ALTER TABLE beetle_list_read ADD COLUMN has_image TINYINT(1) NOT NULL DEFAULT 0 AFTER lng'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND column_name = 'soil_ph_band'
    ),
    'SELECT 1',
    'ALTER TABLE beetle_list_read ADD COLUMN soil_ph_band VARCHAR(32) NOT NULL DEFAULT ''unknown'' AFTER has_image'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND column_name = 'temperature_band'
    ),
    'SELECT 1',
    'ALTER TABLE beetle_list_read ADD COLUMN temperature_band VARCHAR(32) NOT NULL DEFAULT ''unknown'' AFTER soil_ph_band'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND column_name = 'precipitation_band'
    ),
    'SELECT 1',
    'ALTER TABLE beetle_list_read ADD COLUMN precipitation_band VARCHAR(32) NOT NULL DEFAULT ''unknown'' AFTER temperature_band'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND column_name = 'event_date_quality'
    ),
    'SELECT 1',
    'ALTER TABLE beetle_list_read ADD COLUMN event_date_quality VARCHAR(32) NOT NULL DEFAULT ''unknown'' AFTER precipitation_band'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND index_name = 'idx_blr_has_image_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_blr_has_image_entity ON beetle_list_read (has_image, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND index_name = 'idx_blr_soil_ph_band_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_blr_soil_ph_band_entity ON beetle_list_read (soil_ph_band, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND index_name = 'idx_blr_temperature_band_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_blr_temperature_band_entity ON beetle_list_read (temperature_band, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND index_name = 'idx_blr_precipitation_band_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_blr_precipitation_band_entity ON beetle_list_read (precipitation_band, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'beetle_list_read'
        AND index_name = 'idx_blr_event_date_quality_entity'
    ),
    'SELECT 1',
    'CREATE INDEX idx_blr_event_date_quality_entity ON beetle_list_read (event_date_quality, entity_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE beetle_list_read b
LEFT JOIN observation o ON o.gbif_id = b.gbif_id
LEFT JOIN location l ON l.location_id = o.location_id
LEFT JOIN beetle_record br ON b.entity_id = CONCAT('rec-', br.record_id)
SET
  has_image = CASE
    WHEN EXISTS (
      SELECT 1
      FROM media m
      WHERE m.gbif_id = b.gbif_id
        AND m.image_url IS NOT NULL
        AND TRIM(m.image_url) <> ''
    ) THEN 1
    ELSE 0
  END,
  soil_ph_band = CASE
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 5.5 THEN 'strongly_acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 6.5 THEN 'acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 7.5 THEN 'neutral'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 8.5 THEN 'alkaline'
    ELSE 'strongly_alkaline'
  END,
  temperature_band = CASE
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 5 THEN 'cold'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 15 THEN 'mild'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 25 THEN 'warm'
    ELSE 'hot'
  END,
  precipitation_band = CASE
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) IS NULL THEN 'unknown'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 250 THEN 'arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 500 THEN 'semi_arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 1000 THEN 'sub_humid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 2000 THEN 'humid'
    ELSE 'per_humid'
  END,
  event_date_quality = CASE
    WHEN b.observed_at IS NULL OR TRIM(b.observed_at) = '' THEN 'unknown'
    WHEN b.observed_at REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN 'vollstaendig'
    WHEN b.observed_at REGEXP '^[0-9]{4}-[0-9]{2}$' THEN 'jahr_monat'
    WHEN b.observed_at REGEXP '^[0-9]{4}$' THEN 'nur_jahr'
    ELSE 'frei_text'
  END;

CREATE TABLE IF NOT EXISTS beetle_list_filter_count_read (
  dim_name VARCHAR(64) NOT NULL,
  dim_value VARCHAR(128) NOT NULL,
  cnt BIGINT NOT NULL,
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (dim_name, dim_value)
) ENGINE=InnoDB;

TRUNCATE TABLE beetle_list_filter_count_read;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'has_image', CAST(has_image AS CHAR), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY has_image;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'country', COALESCE(country, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY country;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'climate', COALESCE(climate, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY climate;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'vegetation', COALESCE(vegetation, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY vegetation;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'elevation_group', COALESCE(elevation_group, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY elevation_group;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'soil_ph_band', COALESCE(soil_ph_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY soil_ph_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'temperature_band', COALESCE(temperature_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY temperature_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'precipitation_band', COALESCE(precipitation_band, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY precipitation_band;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'event_date_quality', COALESCE(event_date_quality, 'unknown'), COUNT(*), NOW()
FROM beetle_list_read
GROUP BY event_date_quality;

INSERT INTO beetle_list_filter_count_read (dim_name, dim_value, cnt, refreshed_at)
SELECT 'observed_year', CAST(observed_year AS CHAR), COUNT(*), NOW()
FROM beetle_list_read
WHERE observed_year IS NOT NULL
GROUP BY observed_year;


-- END backend/sql/ops/MigrateBeetleListReadModelRetrofitBundle.sql



-- ============================================================================
-- Incremental single-record refresh of the precomputed read-models.
-- Added so manually created/edited beetles appear on the map and the compact
-- list IMMEDIATELY, without the multi-minute full TRUNCATE+rebuild. Reuses the
-- exact transform logic of refresh_map_point_read and the beetle_list_read
-- build, scoped to a single record. The write repository calls this after each
-- create/update/soft-delete. On soft-delete (status<>'active') the DELETEs run
-- and the INSERTs match nothing, so the record drops out of both read-models.
-- ============================================================================
DROP PROCEDURE IF EXISTS refresh_read_models_for_record;
DELIMITER $$
CREATE PROCEDURE refresh_read_models_for_record(IN pRecordId BIGINT)
BEGIN
  DECLARE vEntity VARCHAR(64);
  SET vEntity = CONCAT('rec-', pRecordId);

  -- map_point_read: replace this record's point (manual-source branch, scoped)
  DELETE FROM map_point_read WHERE entity_id = vEntity;
  INSERT INTO map_point_read (
    entity_id,
    source_type,
    record_id,
    gbif_id,
    observed_at,
    species_name,
    family,
    location,
    country,
    lat,
    lng,
    elevation,
    climate,
    vegetation,
    elevation_group,
    refreshed_at
  )
  SELECT
    CONCAT('rec-', br.record_id) AS entity_id,
    'manual' AS source_type,
    br.record_id,
    br.gbif_id,
    br.event_date AS observed_at,
    br.scientific_name AS species_name,
    br.family,
    COALESCE(
      NULLIF(TRIM(br.location), ''),
      NULLIF(TRIM(br.verbatim_locality), ''),
      NULLIF(TRIM(CONCAT_WS(', ', br.city, br.region, br.country)), ''),
      NULLIF(TRIM(CONCAT_WS(', ', br.region, br.country)), ''),
      NULLIF(TRIM(br.country), ''),
      'Unbekannt'
    ) AS location,
    br.country,
    CAST(br.latitude AS DECIMAL(9,6)) AS lat,
    CAST(br.longitude AS DECIMAL(9,6)) AS lng,
    br.elevation,
    CASE
      WHEN COALESCE(br.temperature, br.worldclim_bio01) IS NULL
      AND COALESCE(br.precipitation, br.worldclim_bio12) IS NULL THEN 'unknown'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) < 0 THEN 'E'
      WHEN COALESCE(br.precipitation, br.worldclim_bio12) IS NOT NULL
           AND COALESCE(br.precipitation, br.worldclim_bio12) < 500 THEN 'B'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) >= 18 THEN 'A'
      WHEN COALESCE(br.temperature, br.worldclim_bio01) < 10 THEN 'D'
      ELSE 'C'
    END AS climate,
    CASE
      WHEN br.biome_id IN (1, 2, 3, 4, 5, 6) THEN 'tree_cover'
      WHEN br.biome_id IN (7, 8, 10) THEN 'grassland'
      WHEN br.biome_id = 9 THEN 'wetland'
      WHEN br.biome_id = 11 THEN 'moss_lichen'
      WHEN br.biome_id = 12 THEN 'shrubland'
      WHEN br.biome_id = 13 THEN 'bare_sparse'
      WHEN br.biome_id = 14 THEN 'mangroves'
      WHEN br.landcover_class = 10 THEN 'tree_cover'
      WHEN br.landcover_class = 20 THEN 'shrubland'
      WHEN br.landcover_class = 30 THEN 'grassland'
      WHEN br.landcover_class = 40 THEN 'cropland'
      WHEN br.landcover_class = 50 THEN 'built_up'
      WHEN br.landcover_class = 60 THEN 'bare_sparse'
      WHEN br.landcover_class = 70 THEN 'snow_ice'
      WHEN br.landcover_class = 80 THEN 'water'
      WHEN br.landcover_class = 90 THEN 'wetland'
      WHEN br.landcover_class = 95 THEN 'mangroves'
      WHEN br.landcover_class = 100 THEN 'moss_lichen'
      ELSE 'unknown'
    END AS vegetation,
    CASE
      WHEN br.elevation IS NULL THEN '0_100'
      WHEN br.elevation < 100 THEN '0_100'
      WHEN br.elevation < 500 THEN '100_500'
      WHEN br.elevation < 1000 THEN '500_1000'
      WHEN br.elevation < 2000 THEN '1000_2000'
      WHEN br.elevation < 3000 THEN '2000_3000'
      WHEN br.elevation < 4500 THEN '3000_4500'
      ELSE '4500_plus'
    END AS elevation_group,
    NOW() AS refreshed_at
  FROM beetle_record br
  WHERE br.record_id = pRecordId
    AND br.status = 'active'
    AND br.latitude IS NOT NULL
    AND br.longitude IS NOT NULL;

  -- beetle_list_read: replace this record's compact row (sourced from map_point_read, scoped)
  DELETE FROM beetle_list_read WHERE entity_id = vEntity;
INSERT INTO beetle_list_read (
  entity_id,
  gbif_id,
  observed_at,
  observed_year,
  name,
  family,
  country,
  location,
  climate,
  vegetation,
  elevation,
  elevation_group,
  lat,
  lng,
  has_image,
  soil_ph_band,
  temperature_band,
  precipitation_band,
  event_date_quality,
  refreshed_at
)
SELECT
  m.entity_id,
  m.gbif_id,
  m.observed_at,
  CASE
    WHEN m.observed_at IS NULL THEN NULL
    WHEN CHAR_LENGTH(m.observed_at) >= 4 THEN CAST(SUBSTRING(m.observed_at, 1, 4) AS UNSIGNED)
    ELSE NULL
  END AS observed_year,
  m.species_name,
  m.family,
  m.country,
  m.location,
  m.climate,
  m.vegetation,
  m.elevation,
  m.elevation_group,
  m.lat,
  m.lng,
  CASE
    WHEN EXISTS (
      SELECT 1
      FROM media md
      WHERE md.gbif_id = m.gbif_id
        AND md.image_url IS NOT NULL
        AND TRIM(md.image_url) <> ''
    ) THEN 1
    ELSE 0
  END AS has_image,
  CASE
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 5.5 THEN 'strongly_acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) < 6.5 THEN 'acidic'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 7.5 THEN 'neutral'
    WHEN COALESCE(
      br.soil_ph,
      CASE
        WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
        WHEN l.soil_ph > 14 THEN l.soil_ph / 10
        ELSE l.soil_ph
      END
    ) <= 8.5 THEN 'alkaline'
    ELSE 'strongly_alkaline'
  END AS soil_ph_band,
  CASE
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) IS NULL THEN 'unknown'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 5 THEN 'cold'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 15 THEN 'mild'
    WHEN COALESCE(
      br.temperature,
      CASE
        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
        ELSE l.worldclim_bio01
      END
    ) < 25 THEN 'warm'
    ELSE 'hot'
  END AS temperature_band,
  CASE
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) IS NULL THEN 'unknown'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 250 THEN 'arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 500 THEN 'semi_arid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 1000 THEN 'sub_humid'
    WHEN COALESCE(br.precipitation, l.worldclim_bio12) < 2000 THEN 'humid'
    ELSE 'per_humid'
  END AS precipitation_band,
  CASE
    WHEN m.observed_at IS NULL OR TRIM(m.observed_at) = '' THEN 'unknown'
    WHEN m.observed_at REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN 'vollstaendig'
    WHEN m.observed_at REGEXP '^[0-9]{4}-[0-9]{2}$' THEN 'jahr_monat'
    WHEN m.observed_at REGEXP '^[0-9]{4}$' THEN 'nur_jahr'
    ELSE 'frei_text'
  END AS event_date_quality,
  NOW()
FROM map_point_read m
LEFT JOIN observation o
  ON m.source_type = 'observation'
 AND o.gbif_id = m.gbif_id
LEFT JOIN location l
  ON l.location_id = o.location_id
LEFT JOIN beetle_record br
  ON m.source_type = 'manual'
 AND br.record_id = m.record_id
WHERE m.entity_id = vEntity;
END$$
DELIMITER ;
