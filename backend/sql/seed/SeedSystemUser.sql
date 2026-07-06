USE beetle_db;

INSERT INTO app_user (email, password_hash, role, is_active)
VALUES (
  'system@beetlebox.internal',
  '$2b$12$WFtW6I2iaX1N41m0pE8dj.JH1tV4wRjeP4uMA90.D2i5G2gub7JqK',
  'viewer',
  1
)
ON DUPLICATE KEY UPDATE email = email;

SELECT user_id, email, role, is_active
FROM app_user
WHERE email = 'system@beetlebox.internal'
LIMIT 1;
