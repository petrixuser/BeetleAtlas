USE beetle_db;

-- Marks the two consolidated migrations (baked into the DB image during initdb)
-- as already applied, so the backend's run_migrations.py SKIPS them on startup
-- instead of re-executing their DELIMITER / CREATE PROCEDURE blocks (which the
-- pymysql-based runner cannot execute). The versions/descriptions MUST stay in
-- sync with the MIGRATIONS list in backend/sql/run_migrations.py.
INSERT IGNORE INTO schema_migrations (version, description) VALUES
  ('20260623_01_auth_and_write_consolidated', 'consolidated auth and manual beetle write migrations'),
  ('20260623_02_read_model_and_quality_consolidated', 'consolidated read-model, index, and quality migrations');

SELECT version, description, applied_at
FROM schema_migrations
ORDER BY applied_at DESC, version DESC;
