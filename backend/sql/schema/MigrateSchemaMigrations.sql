-- ============================================================================
--  Schema: Migrations-Journal (schema_migrations)
--  Zweck: haelt fest, welche Ops-/Migrations-Skripte bereits eingespielt wurden
--  (Version + Beschreibung + Zeitpunkt), damit der Migrations-Runner sie nicht
--  erneut ausfuehrt.
--  Rolle beim DB-Aufbau: Buchhaltungstabelle fuer die Migrationssteuerung.
--  Idempotent/mehrfach ausfuehrbar: nutzt CREATE TABLE IF NOT EXISTS; die
--  abschliessende Abfrage listet nur den aktuellen Stand auf.
-- ============================================================================

USE beetle_db;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(64) NOT NULL,
  description VARCHAR(255) NULL,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (version)
) ENGINE=InnoDB;

SELECT version, description, applied_at
FROM schema_migrations
ORDER BY applied_at DESC, version DESC;
