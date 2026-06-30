-- One-off seed: create a TEST researcher account directly in app_user.
--
-- Why a migration (not a seed file): the baked init seeds in Dockerfile.db only
-- run on a FRESH (empty) MySQL volume. The live prod volume already has data, so
-- those never re-run. The backend's run_migrations.py runs on every start and
-- applies new, versioned migrations against the EXISTING volume -- so this is the
-- path that actually reaches the live DB on deploy (no manual NAS/Portainer step).
--
-- Email is stored lowercased because login lowercases the submitted email before
-- lookup (auth_controller.login_controller). role='researcher', is_active=1 so it
-- can log in immediately without the signup code or email verification.
--
-- NOTE: throwaway TEST account with a weak password -- delete after verifying the
-- git -> DB -> live mechanism works. Idempotent: re-running refreshes it in place.
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
