USE beetle_db;

-- System owner account for seeded / curated data (currently the featured beetles).
--
-- Why this exists: beetle_record.created_by is NOT NULL with an FK to app_user,
-- but the featured-data seed (SeedFeaturedData.sql) runs at DB init — before any
-- real admin is bootstrapped via the admin-bootstrap endpoint. Without an existing
-- active user the seed's owner lookup (SELECT ... WHERE is_active = 1) returns NULL
-- and every featured row is dropped (featured_inserted_rows = 0). This account gives
-- those rows a valid owner.
--
-- This is NOT a login account: password_hash is a bcrypt hash of an unknown random
-- string, so verify_password() can never succeed for it. role = 'viewer' (least
-- privilege); is_active = 1 only so the featured seed's owner lookup can find it.
-- Idempotent: re-running leaves an existing account untouched.
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
