USE beetle_db;

-- One-time SQL seed alternative for admin bootstrap.
-- Usage:
-- 1) Register/login once with a normal account (so password_hash already exists).
-- 2) Set desired admin email below and run this script once.

SET @admin_email := 'admin.contract@example.local';

UPDATE app_user
SET role = 'admin',
    is_active = 1
WHERE email = @admin_email;

SELECT
  user_id,
  email,
  role,
  is_active,
  created_at
FROM app_user
WHERE email = @admin_email
LIMIT 1;
