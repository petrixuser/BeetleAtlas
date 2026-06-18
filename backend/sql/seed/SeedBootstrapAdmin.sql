USE beetle_db;

-- One-time SQL seed to create or promote an admin account.
-- IMPORTANT: Generate a bcrypt hash first (e.g. via backend.core.auth.hash_password)
-- and set it below before running this script.

SET @admin_email := 'admin@example.local';
SET @admin_password_hash := '$2b$12$REPLACE_WITH_BCRYPT_HASH';

INSERT INTO app_user (email, password_hash, role, is_active)
VALUES (@admin_email, @admin_password_hash, 'admin', 1)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  role = 'admin',
  is_active = 1;

SELECT
  user_id,
  email,
  role,
  is_active,
  created_at
FROM app_user
WHERE email = @admin_email
LIMIT 1;
