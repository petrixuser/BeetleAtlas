USE beetle_db;

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
    FOREIGN KEY (record_id) REFERENCES beetle_record(record_id),
  CONSTRAINT fk_beetle_record_audit_actor
    FOREIGN KEY (actor_user_id) REFERENCES app_user(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS beetle_record (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  gbif_id BIGINT NULL,
  taxon_id VARCHAR(128) NULL,
  scientific_name VARCHAR(512) NOT NULL,
  scientific_name_authorship VARCHAR(512) NULL,
  family VARCHAR(255) NOT NULL,
  genus VARCHAR(255) NULL,
  specific_epithet VARCHAR(255) NULL,
  recorded_by VARCHAR(512) NULL,
  catalogue_number VARCHAR(255) NULL,
  identification_id VARCHAR(255) NULL,
  identified_by VARCHAR(512) NULL,
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
  country VARCHAR(255) NULL,
  region VARCHAR(255) NULL,
  city VARCHAR(255) NULL,
  verbatim_locality TEXT NULL,
  location VARCHAR(1024) NULL,
  notes TEXT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_by BIGINT NOT NULL,
  updated_by BIGINT NULL,
  deleted_by BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (record_id),
  KEY idx_beetle_record_status (status),
  KEY idx_beetle_record_name (scientific_name),
  KEY idx_beetle_record_country (country),
  KEY idx_beetle_record_taxon_id (taxon_id),
  CONSTRAINT chk_beetle_record_status CHECK (status IN ('active', 'deleted')),
  CONSTRAINT chk_beetle_record_lat_lng CHECK ((latitude IS NULL OR latitude BETWEEN -90 AND 90) AND (longitude IS NULL OR longitude BETWEEN -180 AND 180)),
  CONSTRAINT chk_beetle_record_image_available CHECK (image_available IS NULL OR image_available IN (0, 1)),
  CONSTRAINT chk_beetle_record_gbif_id_positive CHECK (gbif_id IS NULL OR gbif_id > 0),
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
  CONSTRAINT chk_beetle_record_lat_lng_pair CHECK (
    (latitude IS NULL AND longitude IS NULL)
    OR (latitude IS NOT NULL AND longitude IS NOT NULL)
  ),
  CONSTRAINT chk_beetle_record_image_flag_url CHECK (
    image_available IS NULL
    OR (image_available = 0 AND (image_url IS NULL OR TRIM(image_url) = ''))
    OR (image_available = 1 AND image_url IS NOT NULL AND TRIM(image_url) <> '')
  ),
  CONSTRAINT fk_beetle_record_created_by FOREIGN KEY (created_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_updated_by FOREIGN KEY (updated_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_deleted_by FOREIGN KEY (deleted_by) REFERENCES app_user(user_id)
) ENGINE=InnoDB;

ALTER TABLE beetle_record
  ADD COLUMN gbif_id BIGINT NULL AFTER record_id,
  ADD COLUMN taxon_id VARCHAR(128) NULL AFTER gbif_id,
  ADD COLUMN scientific_name_authorship VARCHAR(512) NULL AFTER scientific_name,
  ADD COLUMN recorded_by VARCHAR(512) NULL AFTER specific_epithet,
  ADD COLUMN catalogue_number VARCHAR(255) NULL AFTER recorded_by,
  ADD COLUMN identification_id VARCHAR(255) NULL AFTER catalogue_number,
  ADD COLUMN identified_by VARCHAR(512) NULL AFTER identification_id,
  ADD COLUMN event_date VARCHAR(128) NULL AFTER identified_by,
  ADD COLUMN verbatim_event_date VARCHAR(255) NULL AFTER event_date,
  ADD COLUMN basis_of_record VARCHAR(128) NULL AFTER verbatim_event_date,
  ADD COLUMN dataset_name VARCHAR(512) NULL AFTER basis_of_record,
  ADD COLUMN institution_code VARCHAR(255) NULL AFTER dataset_name,
  ADD COLUMN image_available TINYINT(1) NULL AFTER institution_code,
  ADD COLUMN image_url TEXT NULL AFTER image_available,
  ADD COLUMN media_references TEXT NULL AFTER image_url,
  ADD COLUMN media_creator VARCHAR(512) NULL AFTER media_references,
  ADD COLUMN media_publisher VARCHAR(512) NULL AFTER media_creator,
  ADD COLUMN media_rights_holder VARCHAR(512) NULL AFTER media_publisher,
  ADD COLUMN media_license VARCHAR(512) NULL AFTER media_rights_holder,
  ADD COLUMN latitude DECIMAL(9,6) NULL AFTER media_license,
  ADD COLUMN longitude DECIMAL(9,6) NULL AFTER latitude,
  ADD COLUMN coordinate_uncertainty VARCHAR(128) NULL AFTER longitude,
  ADD COLUMN region VARCHAR(255) NULL AFTER country,
  ADD COLUMN city VARCHAR(255) NULL AFTER region,
  ADD COLUMN verbatim_locality TEXT NULL AFTER city;

SET @idx_gbif_sql = IF(
  EXISTS (
    SELECT 1
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'beetle_record'
      AND index_name = 'idx_beetle_record_gbif_id'
  ),
  'SELECT "idx_beetle_record_gbif_id already exists"',
  'CREATE INDEX idx_beetle_record_gbif_id ON beetle_record(gbif_id)'
);
PREPARE idx_gbif_stmt FROM @idx_gbif_sql;
EXECUTE idx_gbif_stmt;
DEALLOCATE PREPARE idx_gbif_stmt;

SET @idx_taxon_sql = IF(
  EXISTS (
    SELECT 1
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'beetle_record'
      AND index_name = 'idx_beetle_record_taxon_id'
  ),
  'SELECT "idx_beetle_record_taxon_id already exists"',
  'CREATE INDEX idx_beetle_record_taxon_id ON beetle_record(taxon_id)'
);
PREPARE idx_taxon_stmt FROM @idx_taxon_sql;
EXECUTE idx_taxon_stmt;
DEALLOCATE PREPARE idx_taxon_stmt;

SET @uq_gbif_sql = IF(
  EXISTS (
    SELECT 1
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'beetle_record'
      AND index_name = 'uq_beetle_record_gbif_id'
  ),
  'SELECT "uq_beetle_record_gbif_id already exists"',
  'CREATE UNIQUE INDEX uq_beetle_record_gbif_id ON beetle_record(gbif_id)'
);
PREPARE uq_gbif_stmt FROM @uq_gbif_sql;
EXECUTE uq_gbif_stmt;
DEALLOCATE PREPARE uq_gbif_stmt;

SET @chk_lat_lng_sql = IF(
  EXISTS (
    SELECT 1
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = 'beetle_record'
      AND constraint_name = 'chk_beetle_record_lat_lng'
  ),
  'SELECT "chk_beetle_record_lat_lng already exists"',
  'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_lat_lng CHECK ((latitude IS NULL OR latitude BETWEEN -90 AND 90) AND (longitude IS NULL OR longitude BETWEEN -180 AND 180))'
);
PREPARE chk_lat_lng_stmt FROM @chk_lat_lng_sql;
EXECUTE chk_lat_lng_stmt;
DEALLOCATE PREPARE chk_lat_lng_stmt;

SET @chk_img_sql = IF(
  EXISTS (
    SELECT 1
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = 'beetle_record'
      AND constraint_name = 'chk_beetle_record_image_available'
  ),
  'SELECT "chk_beetle_record_image_available already exists"',
  'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_image_available CHECK (image_available IS NULL OR image_available IN (0, 1))'
);
PREPARE chk_img_stmt FROM @chk_img_sql;
EXECUTE chk_img_stmt;
DEALLOCATE PREPARE chk_img_stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'beetle_record'
    AND constraint_name = 'chk_beetle_record_gbif_id_positive'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM beetle_record
  WHERE gbif_id IS NOT NULL
    AND gbif_id <= 0
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_beetle_record_gbif_id_positive already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_beetle_record_gbif_id_positive due to invalid existing rows"',
    'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_gbif_id_positive CHECK (gbif_id IS NULL OR gbif_id > 0)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'beetle_record'
    AND constraint_name = 'chk_beetle_record_basis_of_record'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM beetle_record
  WHERE basis_of_record IS NOT NULL
    AND basis_of_record NOT IN (
      'MATERIAL_CITATION',
      'HUMAN_OBSERVATION',
      'MACHINE_OBSERVATION',
      'PRESERVED_SPECIMEN',
      'FOSSIL_SPECIMEN',
      'LIVING_SPECIMEN',
      'MATERIAL_SAMPLE',
      'OCCURRENCE'
    )
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_beetle_record_basis_of_record already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_beetle_record_basis_of_record due to invalid existing rows"',
    'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_basis_of_record CHECK (basis_of_record IS NULL OR basis_of_record IN (''MATERIAL_CITATION'',''HUMAN_OBSERVATION'',''MACHINE_OBSERVATION'',''PRESERVED_SPECIMEN'',''FOSSIL_SPECIMEN'',''LIVING_SPECIMEN'',''MATERIAL_SAMPLE'',''OCCURRENCE''))'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'beetle_record'
    AND constraint_name = 'chk_beetle_record_lat_lng_pair'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM beetle_record
  WHERE (latitude IS NULL AND longitude IS NOT NULL)
     OR (latitude IS NOT NULL AND longitude IS NULL)
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_beetle_record_lat_lng_pair already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_beetle_record_lat_lng_pair due to invalid existing rows"',
    'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_lat_lng_pair CHECK ((latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL))'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE table_schema = DATABASE()
    AND table_name = 'beetle_record'
    AND constraint_name = 'chk_beetle_record_image_flag_url'
    AND constraint_type = 'CHECK'
);
SET @has_invalid := (
  SELECT COUNT(*)
  FROM beetle_record
  WHERE NOT (
    image_available IS NULL
    OR (image_available = 0 AND (image_url IS NULL OR TRIM(image_url) = ''))
    OR (image_available = 1 AND image_url IS NOT NULL AND TRIM(image_url) <> '')
  )
);
SET @sql := IF(
  @constraint_exists > 0,
  'SELECT "chk_beetle_record_image_flag_url already exists"',
  IF(
    @has_invalid > 0,
    'SELECT "Skipping chk_beetle_record_image_flag_url due to invalid existing rows"',
    'ALTER TABLE beetle_record ADD CONSTRAINT chk_beetle_record_image_flag_url CHECK (image_available IS NULL OR (image_available = 0 AND (image_url IS NULL OR TRIM(image_url) = '''')) OR (image_available = 1 AND image_url IS NOT NULL AND TRIM(image_url) <> ''''))'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT
  column_name
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'beetle_record'
  AND column_name IN (
    'gbif_id',
    'taxon_id',
    'scientific_name_authorship',
    'recorded_by',
    'catalogue_number',
    'identification_id',
    'identified_by',
    'event_date',
    'verbatim_event_date',
    'basis_of_record',
    'dataset_name',
    'institution_code',
    'image_available',
    'image_url',
    'media_references',
    'media_creator',
    'media_publisher',
    'media_rights_holder',
    'media_license',
    'latitude',
    'longitude',
    'coordinate_uncertainty',
    'region',
    'city',
    'verbatim_locality'
  )
ORDER BY column_name;
