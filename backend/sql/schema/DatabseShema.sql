CREATE DATABASE IF NOT EXISTS beetle_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE beetle_db;

CREATE TABLE IF NOT EXISTS beetle_species (
  beetle_id INT NOT NULL,
  taxon_id VARCHAR(128) NULL,
  family VARCHAR(255) NULL,
  genus VARCHAR(255) NULL,
  specific_epithet VARCHAR(255) NULL,
  scientific_name VARCHAR(512) NULL,
  scientific_name_authorship VARCHAR(512) NULL,
  PRIMARY KEY (beetle_id),
  KEY idx_species_taxon_id (taxon_id),
  KEY idx_species_scientific_name (scientific_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS location (
  location_id INT NOT NULL,
  latitude DECIMAL(9,6) NOT NULL,
  longitude DECIMAL(9,6) NOT NULL,
  coordinate_uncertainty VARCHAR(128) NULL,
  country VARCHAR(255) NULL,
  region VARCHAR(255) NULL,
  city VARCHAR(255) NULL,
  verbatim_locality TEXT NULL,
  elevation FLOAT NULL,
  slope FLOAT NULL,
  landcover_class INT NULL,
  soil_ph FLOAT NULL,
  soil_organic_carbon FLOAT NULL,
  worldclim_bio01 FLOAT NULL,
  worldclim_bio12 FLOAT NULL,
  distance_to_water_m FLOAT NULL,
  ecoregion_id INT NULL,
  biome_id INT NULL,
  human_modification FLOAT NULL,
  PRIMARY KEY (location_id),
  KEY idx_location_lat_lon (latitude, longitude),
  CONSTRAINT chk_location_lat_lng CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS observation (
  gbif_id BIGINT NOT NULL,
  recorded_by VARCHAR(512) NULL,
  catalogue_number VARCHAR(255) NULL,
  identification_id VARCHAR(255) NULL,
  identified_by VARCHAR(512) NULL,
  beetle_id INT NOT NULL,
  taxon_id VARCHAR(128) NULL,
  location_id INT NOT NULL,
  event_date VARCHAR(128) NULL,
  event_date_parsed DATE NULL,
  verbatim_event_date VARCHAR(255) NULL,
  basis_of_record VARCHAR(128) NULL,
  dataset_name VARCHAR(512) NULL,
  institution_code VARCHAR(255) NULL,
  image_available TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (gbif_id),
  KEY idx_observation_beetle_id (beetle_id),
  KEY idx_observation_location_id (location_id),
  KEY idx_observation_event_date (event_date),
  KEY idx_observation_event_date_parsed (event_date_parsed),
  CONSTRAINT chk_observation_image_available CHECK (image_available IN (0, 1)),
  CONSTRAINT fk_observation_species
    FOREIGN KEY (beetle_id) REFERENCES beetle_species (beetle_id),
  CONSTRAINT fk_observation_location
    FOREIGN KEY (location_id) REFERENCES location (location_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS media (
  media_id INT NOT NULL,
  gbif_id BIGINT NOT NULL,
  image_url TEXT NOT NULL,
  `references` TEXT NULL,
  creator VARCHAR(512) NULL,
  publisher VARCHAR(512) NULL,
  rights_holder VARCHAR(512) NULL,
  license VARCHAR(512) NULL,
  PRIMARY KEY (media_id),
  KEY idx_media_gbif_id (gbif_id),
  KEY idx_media_gbif_media_id (gbif_id, media_id),
  CONSTRAINT fk_media_observation
    FOREIGN KEY (gbif_id) REFERENCES observation (gbif_id)
) ENGINE=InnoDB;

-- Final climate table to load Earth Engine exported results (monthly or yearly).
CREATE TABLE IF NOT EXISTS climate_snapshot (
  climate_id BIGINT NOT NULL AUTO_INCREMENT,
  location_id INT NOT NULL,
  snapshot_date DATE NOT NULL,
  avg_temperature FLOAT NULL,
  precipitation FLOAT NULL,
  soil_moisture FLOAT NULL,
  ndvi FLOAT NULL,
  relative_humidity FLOAT NULL,
  surface_pressure_hpa FLOAT NULL,
  nighttime_lights FLOAT NULL,
  PRIMARY KEY (climate_id),
  UNIQUE KEY uq_climate_loc_date (location_id, snapshot_date),
  KEY idx_climate_location (location_id),
  CONSTRAINT chk_climate_relative_humidity CHECK (relative_humidity IS NULL OR relative_humidity BETWEEN 0 AND 100),
  CONSTRAINT chk_climate_ndvi CHECK (ndvi IS NULL OR ndvi BETWEEN -1 AND 1),
  CONSTRAINT chk_climate_soil_moisture CHECK (soil_moisture IS NULL OR soil_moisture BETWEEN 0 AND 1),
  CONSTRAINT chk_climate_nighttime_lights CHECK (nighttime_lights IS NULL OR nighttime_lights >= 0),
  CONSTRAINT fk_climate_location
    FOREIGN KEY (location_id) REFERENCES location (location_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS quality_report_history (
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
) ENGINE=InnoDB;
