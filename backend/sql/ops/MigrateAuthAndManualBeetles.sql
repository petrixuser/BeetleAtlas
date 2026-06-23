USE beetle_db;

CREATE TABLE IF NOT EXISTS app_user (
  user_id BIGINT NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_app_user_email (email),
  CONSTRAINT chk_app_user_role CHECK (role IN ('researcher', 'admin', 'viewer')),
  CONSTRAINT chk_app_user_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS beetle_record (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  scientific_name VARCHAR(512) NOT NULL,
  family VARCHAR(255) NOT NULL,
  genus VARCHAR(255) NULL,
  specific_epithet VARCHAR(255) NULL,
  country VARCHAR(255) NULL,
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
  CONSTRAINT chk_beetle_record_status CHECK (status IN ('active', 'deleted')),
  CONSTRAINT fk_beetle_record_created_by FOREIGN KEY (created_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_updated_by FOREIGN KEY (updated_by) REFERENCES app_user(user_id),
  CONSTRAINT fk_beetle_record_deleted_by FOREIGN KEY (deleted_by) REFERENCES app_user(user_id)
) ENGINE=InnoDB;

SELECT
  table_name,
  table_rows
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name IN ('app_user', 'beetle_record')
ORDER BY table_name;
