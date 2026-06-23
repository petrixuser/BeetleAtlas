USE beetle_db;

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

SELECT
  table_name,
  table_rows
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name = 'app_refresh_token'
LIMIT 1;
