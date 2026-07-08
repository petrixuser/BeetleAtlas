-- ============================================================================
--  Ops: Zusammengefasste Migrationen als "angewendet" markieren
--  Zweck: traegt die im DB-Image (initdb) bereits eingebackenen konsolidierten
--  Migrationen in schema_migrations ein, damit der Migrations-Runner sie nicht
--  erneut ausfuehrt.
--  Rolle beim DB-Aufbau: Buchhaltungsschritt fuer die Migrationssteuerung.
--  Idempotent/mehrfach ausfuehrbar: INSERT IGNORE fuegt vorhandene Versionen
--  nicht erneut ein.
-- ============================================================================

USE beetle_db;


INSERT IGNORE INTO schema_migrations (version, description) VALUES
  ('20260623_02_read_model_and_quality_consolidated', 'consolidated read-model, index, and quality migrations');

SELECT version, description, applied_at
FROM schema_migrations
ORDER BY applied_at DESC, version DESC;
