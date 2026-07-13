-- ============================================================================
--  Seed: Bestehenden Benutzer zum Admin hochstufen
--  Zweck: setzt fuer ein bereits existierendes Konto (per E-Mail) die Rolle auf
--  'admin' und aktiviert es.
--  Rolle beim DB-Aufbau: optionaler Seed-/Wartungsschritt fuer die Auth-Tabellen.
--  Idempotent/mehrfach ausfuehrbar: das UPDATE setzt denselben Zielzustand,
--  ein erneuter Lauf aendert nichts weiter.
-- ============================================================================

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
