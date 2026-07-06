USE beetle_db;

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
