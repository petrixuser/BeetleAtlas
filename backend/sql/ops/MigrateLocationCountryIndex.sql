-- Performance index for /api/countries/{code}: the country-detail queries
-- (overview, top climates/vegetations/beetles) filter `location` by country.
-- Without this index those queries full-scan the observation/location join
-- (~417k rows) four times per request. The query WHERE was also made sargable
-- (l.country = :country_code) so this index is actually used.
--
-- Guarded via information_schema so it is safe to run multiple times (the
-- pymysql-based run_migrations runner executes this on existing volumes; on a
-- fresh image the index is created here at first backend start too).
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
