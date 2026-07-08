-- ============================================================================
--  Seed: Vorberechnete Klima-/Vegetationszonen pro Fundort
--  Zweck: laedt koppen_code, vegetation_zone und country_derived je location
--  aus einer CSV in eine Zwischentabelle und aktualisiert damit location.
--  Rolle beim DB-Aufbau: reichert die bereits geladenen location-Zeilen um die
--  abgeleiteten Zonen an (nach SeedCoreData).
--  Idempotent/mehrfach ausfuehrbar: die Zwischentabelle wird per TRUNCATE neu
--  befuellt und danach wieder verworfen; das UPDATE ueberschreibt die Werte.
-- ============================================================================

USE beetle_db;

SET SESSION sql_mode = '';

CREATE TABLE IF NOT EXISTS _location_zones_seed (
  location_id INT PRIMARY KEY,
  koppen_code VARCHAR(8) NULL,
  vegetation_zone VARCHAR(80) NULL,
  country_derived VARCHAR(255) NULL
) ENGINE=InnoDB;

TRUNCATE TABLE _location_zones_seed;

LOAD DATA INFILE '/var/lib/mysql-files/location_zones.csv'
INTO TABLE _location_zones_seed
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(location_id, @kc, @vz, @cd)
SET koppen_code = NULLIF(@kc, ''),
    vegetation_zone = NULLIF(@vz, ''),
    country_derived = NULLIF(@cd, '');

UPDATE location l
JOIN _location_zones_seed z ON z.location_id = l.location_id
SET l.koppen_code = z.koppen_code,
    l.vegetation_zone = z.vegetation_zone,
    l.country_derived = z.country_derived;

DROP TABLE _location_zones_seed;
