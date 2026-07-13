-- ============================================================================
--  Schema: Read-Model-Tabellen (vorberechnet fuer Karte & Liste)
--    map_point_read, beetle_list_read, beetle_list_meta_read,
--    beetle_list_filter_count_read
--  Rolle beim DB-Aufbau: Schema-Schritt fuer die Lese-/Abfrage-Optimierung
--  (nach Core/Auth). Legt nur die leeren Tabellenstrukturen an.
--  Befuellt/aktualisiert werden diese Tabellen durch die Prozeduren und
--  Rebuild-Schritte in ops/ReadModelProcedures.sql.
--  Idempotent/mehrfach ausfuehrbar: nutzt CREATE TABLE IF NOT EXISTS.
-- ============================================================================

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
  koppen_code VARCHAR(8) NULL,
  vegetation_zone VARCHAR(80) NULL,
  elevation_group VARCHAR(32) NOT NULL,
  refreshed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (entity_id),
  KEY idx_mpr_bbox_lng_lat (lng, lat),
  KEY idx_mpr_country_bbox (country, lng, lat),
  KEY idx_mpr_climate_bbox (climate, lng, lat),
  KEY idx_mpr_vegetation_bbox (vegetation, lng, lat),
  KEY idx_mpr_koppen_bbox (koppen_code, lng, lat),
  KEY idx_mpr_vegzone_bbox (vegetation_zone, lng, lat),
  KEY idx_mpr_elevation_group_bbox (elevation_group, lng, lat),
  KEY idx_mpr_filters_bbox (climate, vegetation, elevation_group, country, lng, lat),
  KEY idx_mpr_observed_at (observed_at),
  KEY idx_mpr_source_record (source_type, record_id)
) ENGINE=InnoDB;

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
  koppen_code VARCHAR(8) NULL,
  vegetation_zone VARCHAR(80) NULL,
  elevation DOUBLE NULL,
  elevation_group VARCHAR(32) NOT NULL,
  lat DECIMAL(9,6) NOT NULL,
  lng DECIMAL(9,6) NOT NULL,
  has_image TINYINT(1) NOT NULL DEFAULT 0,
  temperature DOUBLE NULL,
  precipitation DOUBLE NULL,
  soil_ph DOUBLE NULL,
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
  KEY idx_blr_koppen_entity (koppen_code, entity_id),
  KEY idx_blr_vegzone_entity (vegetation_zone, entity_id),
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
