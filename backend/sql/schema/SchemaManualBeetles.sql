-- ============================================================================
--  Schema: Manuell eingetragene Kaefer (nutzt den Core wieder)
--  Ein manueller Kaefer verweist wie eine GBIF-Beobachtung auf:
--    beetle_species (Art)              -> beetle_id
--    location (Ort + statische Umwelt) -> location_id
--  Dynamische Umwelt kommt aus climate_snapshot (per location_id).
--  Eigene Tabellen bleiben: beetle_record_media, beetle_record_audit.
--
--  Basistabelle heisst beetle_record_core; die flache Kompatibilitaets-View
--  beetle_record (unten) fuehrt Kern + Art + Ort + neuester Snapshot + Medien
--  wieder zu den alten Spaltennamen zusammen, damit die Lese-Queries und
--  Read-Model-Refreshes UNVERAENDERT bleiben. Schreibzugriffe gehen direkt auf
--  die Basistabellen (nicht ueber die View).
--
--  Rolle beim DB-Aufbau: Schema-Schritt fuer die manuelle Erfassung (nach
--  Core/Auth). Die Normalisierung trennt bewusst Kern (beetle_record_core),
--  Medien (beetle_record_media, 1:N) und Historie (beetle_record_audit), damit
--  jede Information nur einmal gespeichert wird; die View beetle_record fuehrt
--  alles wieder flach zusammen.
--  Idempotent/mehrfach ausfuehrbar: CREATE TABLE IF NOT EXISTS und
--  CREATE OR REPLACE VIEW.
-- ============================================================================

USE beetle_db;

CREATE TABLE IF NOT EXISTS beetle_record_core (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  beetle_id INT NOT NULL,
  location_id INT NULL,
  gbif_id BIGINT NULL,
  recorded_by VARCHAR(512) NULL,
  catalogue_number VARCHAR(255) NULL,
  identification_id VARCHAR(255) NULL,
  identified_by VARCHAR(512) NULL,
  event_date VARCHAR(128) NULL,
  verbatim_event_date VARCHAR(255) NULL,
  basis_of_record VARCHAR(128) NULL,
  dataset_name VARCHAR(512) NULL,
  institution_code VARCHAR(255) NULL,
  notes TEXT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_by BIGINT NOT NULL,
  updated_by BIGINT NULL,
  deleted_by BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uq_beetle_record_gbif_id (gbif_id),
  KEY idx_beetle_record_status (status),
  KEY idx_beetle_record_beetle_id (beetle_id),
  KEY idx_beetle_record_location_id (location_id),
  KEY idx_beetle_record_dataset (dataset_name),
  CONSTRAINT chk_beetle_record_status CHECK (status IN ('active', 'deleted')),
  CONSTRAINT chk_beetle_record_basis_of_record CHECK (
    basis_of_record IS NULL OR basis_of_record IN (
      'MATERIAL_CITATION',
      'HUMAN_OBSERVATION',
      'MACHINE_OBSERVATION',
      'PRESERVED_SPECIMEN',
      'FOSSIL_SPECIMEN',
      'LIVING_SPECIMEN',
      'MATERIAL_SAMPLE',
      'OCCURRENCE'
    )
  ),
  CONSTRAINT fk_beetle_record_species
    FOREIGN KEY (beetle_id) REFERENCES beetle_species(beetle_id),
  CONSTRAINT fk_beetle_record_location
    FOREIGN KEY (location_id) REFERENCES location(location_id),
  CONSTRAINT fk_beetle_record_created_by FOREIGN KEY (created_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_updated_by FOREIGN KEY (updated_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_deleted_by FOREIGN KEY (deleted_by) REFERENCES app_user(user_id)
) ENGINE=InnoDB;

-- Medien zu einem manuellen Kaefer (1:N, gespiegelt an der Core-Tabelle media).
CREATE TABLE IF NOT EXISTS beetle_record_media (
  media_id BIGINT NOT NULL AUTO_INCREMENT,
  record_id BIGINT NOT NULL,
  image_available TINYINT(1) NULL,
  image_url TEXT NULL,
  media_references TEXT NULL,
  media_creator VARCHAR(512) NULL,
  media_publisher VARCHAR(512) NULL,
  media_rights_holder VARCHAR(512) NULL,
  media_license VARCHAR(512) NULL,
  PRIMARY KEY (media_id),
  KEY idx_beetle_record_media_record_id (record_id),
  CONSTRAINT chk_beetle_record_media_image_available CHECK (image_available IS NULL OR image_available IN (0, 1)),
  CONSTRAINT chk_beetle_record_media_image_flag_url CHECK (
    image_available IS NULL
    OR (image_available = 0 AND (image_url IS NULL OR TRIM(image_url) = ''))
    OR (image_available = 1 AND image_url IS NOT NULL AND TRIM(image_url) <> '')
  ),
  CONSTRAINT fk_beetle_record_media_record
    FOREIGN KEY (record_id) REFERENCES beetle_record_core(record_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Aenderungshistorie fuer manuelle Kaefer.
CREATE TABLE IF NOT EXISTS beetle_record_audit (
  audit_id BIGINT NOT NULL AUTO_INCREMENT,
  record_id BIGINT NOT NULL,
  action VARCHAR(16) NOT NULL,
  actor_user_id BIGINT NOT NULL,
  old_values LONGTEXT NULL,
  new_values LONGTEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (audit_id),
  KEY idx_beetle_record_audit_record_id (record_id),
  KEY idx_beetle_record_audit_actor_user_id (actor_user_id),
  KEY idx_beetle_record_audit_created_at (created_at),
  CONSTRAINT chk_beetle_record_audit_action CHECK (action IN ('create', 'update', 'delete')),
  CONSTRAINT fk_beetle_record_audit_record
    FOREIGN KEY (record_id) REFERENCES beetle_record_core(record_id),
  CONSTRAINT fk_beetle_record_audit_actor
    FOREIGN KEY (actor_user_id) REFERENCES app_user(user_id)
) ENGINE=InnoDB;

-- Kompatibilitaets-View beetle_record: fuehrt Kern + Art + Ort + neuester
-- climate_snapshot + Medien flach zusammen (gleiche Spaltennamen wie die fruehere
-- Tabelle). Damit lesen alle bestehenden Queries/Read-Model-Refreshes manuelle
-- Kaefer unveraendert. Schreibzugriffe gehen NICHT ueber diese View.
CREATE OR REPLACE VIEW beetle_record AS
SELECT
  r.record_id,
  r.gbif_id,
  r.beetle_id,
  r.location_id,
  sp.taxon_id,
  sp.scientific_name,
  sp.scientific_name_authorship,
  sp.family,
  sp.genus,
  sp.specific_epithet,
  r.recorded_by,
  r.catalogue_number,
  r.identification_id,
  r.identified_by,
  r.event_date,
  r.verbatim_event_date,
  r.basis_of_record,
  r.dataset_name,
  r.institution_code,
  r.notes,
  r.status,
  r.created_by,
  r.updated_by,
  r.deleted_by,
  r.created_at,
  r.updated_at,
  r.deleted_at,
  l.latitude,
  l.longitude,
  l.coordinate_uncertainty,
  l.country,
  l.region,
  l.city,
  l.verbatim_locality,
  COALESCE(NULLIF(l.verbatim_locality, ''), NULLIF(CONCAT_WS(', ', l.city, l.region, l.country), '')) AS location,
  l.elevation,
  l.slope,
  l.landcover_class,
  l.soil_ph,
  l.soil_organic_carbon,
  l.worldclim_bio01,
  l.worldclim_bio12,
  l.distance_to_water_m,
  l.ecoregion_id,
  l.biome_id,
  l.human_modification,
  l.koppen_code,
  l.vegetation_zone,
  l.country_derived,
  cs.avg_temperature AS temperature,
  cs.precipitation,
  cs.soil_moisture,
  cs.ndvi,
  cs.relative_humidity,
  cs.surface_pressure_hpa,
  cs.nighttime_lights,
  m.image_available,
  m.image_url,
  m.media_references,
  m.media_creator,
  m.media_publisher,
  m.media_rights_holder,
  m.media_license
FROM beetle_record_core r
JOIN beetle_species sp ON sp.beetle_id = r.beetle_id
LEFT JOIN location l ON l.location_id = r.location_id
LEFT JOIN climate_snapshot cs
  ON cs.location_id = r.location_id
 AND cs.snapshot_date = (
      SELECT MAX(cs2.snapshot_date)
      FROM climate_snapshot cs2
      WHERE cs2.location_id = r.location_id
    )
LEFT JOIN beetle_record_media m
  ON m.record_id = r.record_id
 AND m.media_id = (
      SELECT MIN(m2.media_id)
      FROM beetle_record_media m2
      WHERE m2.record_id = r.record_id
    );
