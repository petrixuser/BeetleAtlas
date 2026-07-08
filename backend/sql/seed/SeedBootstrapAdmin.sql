-- ============================================================================
--  Seed: Admin-Konto anlegen oder hochstufen (Bootstrap)
--  Zweck: legt einen Admin-Benutzer an bzw. setzt fuer ein bestehendes Konto
--  das Passwort und die Rolle 'admin'.
--  Rolle beim DB-Aufbau: einmaliger Seed-Schritt fuer die Auth-Tabellen.
--  Idempotent/mehrfach ausfuehrbar: ON DUPLICATE KEY UPDATE setzt denselben
--  Zielzustand erneut.
-- ============================================================================

USE beetle_db;


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
