-- ============================================================================
--  Ops-Migration: Performance-Index auf location(country)
--  Zweck fuer /api/countries/{code}: die Laenderdetail-Abfragen (Uebersicht,
--  Top-Klimazonen/-Vegetationen/-Kaefer) filtern `location` nach Land. Ohne
--  diesen Index scannen diese Abfragen den observation/location-Join
--  (~417k Zeilen) viermal pro Anfrage vollstaendig. Die WHERE-Bedingung wurde
--  ausserdem sargable gemacht (l.country = :country_code), damit dieser Index
--  tatsaechlich genutzt wird.
--
--  Rolle beim DB-Aufbau: Optimierungs-/Migrationsschritt nach dem Basis-Schema.
--  Ueber information_schema abgesichert und daher mehrfach ausfuehrbar (der
--  pymysql-basierte run_migrations-Runner fuehrt dies auf bestehenden Volumes
--  aus; auf einem frischen Image wird der Index hier beim ersten Backend-Start
--  angelegt).
-- ============================================================================
USE beetle_db;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'location'
        AND index_name = 'idx_location_country'
    ),
    'SELECT "idx_location_country already exists"',
    'CREATE INDEX idx_location_country ON location (country)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
