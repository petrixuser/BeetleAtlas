-- ============================================================================
--  Schema: Authentifizierung / Benutzerkonten
--    app_user                 -> Konten (researcher/admin/viewer)
--    app_refresh_token        -> Refresh-Token-Rotation
--    app_pending_registration -> E-Mail-Verifizierung (noch nicht bestaetigt)
--  Rolle beim DB-Aufbau: Schema-Schritt fuer Login/Rollen (nach Core).
--  Idempotent/mehrfach ausfuehrbar: nutzt CREATE TABLE IF NOT EXISTS.
-- ============================================================================

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

CREATE TABLE IF NOT EXISTS app_refresh_token (
  refresh_token_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  token_hash CHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME NULL,
  replaced_by_token_id BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (refresh_token_id),
  UNIQUE KEY uq_app_refresh_token_hash (token_hash),
  KEY idx_app_refresh_token_user_active (user_id, revoked_at, expires_at),
  KEY idx_app_refresh_token_expires_at (expires_at),
  CONSTRAINT fk_app_refresh_token_user
    FOREIGN KEY (user_id) REFERENCES app_user(user_id),
  CONSTRAINT fk_app_refresh_token_replaced_by
    FOREIGN KEY (replaced_by_token_id) REFERENCES app_refresh_token(refresh_token_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS app_pending_registration (
  pending_registration_id BIGINT NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL,
  verification_token_hash CHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL,
  consumed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (pending_registration_id),
  UNIQUE KEY uq_app_pending_registration_email (email),
  UNIQUE KEY uq_app_pending_registration_token_hash (verification_token_hash),
  KEY idx_app_pending_registration_expires_at (expires_at),
  CONSTRAINT chk_app_pending_registration_role CHECK (role IN ('researcher', 'admin', 'viewer'))
) ENGINE=InnoDB;
