-- ============================================================================
--  Ops-Migration/Seed: TEST-Forscherkonto direkt in app_user anlegen
-- ============================================================================
USE beetle_db;

INSERT INTO app_user (email, password_hash, role, is_active)
VALUES (
  'testforscherdb2026@gmail.com',
  '$2b$12$cAHTKB.3GEqrKxs0g1.nY.QlNasFaLyluWWuhlmp8gkiswlRFAoJW',
  'researcher',
  1
)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  role = 'researcher',
  is_active = 1;
