USE beetle_db;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND column_name = 'event_date_parsed'
    ),
    'SELECT "event_date_parsed already exists"',
    'ALTER TABLE observation ADD COLUMN event_date_parsed DATE NULL AFTER event_date'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE observation
SET event_date_parsed = CASE
  WHEN event_date IS NULL OR TRIM(event_date) = '' THEN NULL
  WHEN event_date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(event_date, '%Y-%m-%d')
  ELSE NULL
END
WHERE event_date_parsed IS NULL;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'observation'
        AND index_name = 'idx_observation_event_date_parsed'
    ),
    'SELECT "idx_observation_event_date_parsed already exists"',
    'CREATE INDEX idx_observation_event_date_parsed ON observation (event_date_parsed)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT
  COUNT(*) AS total_rows,
  SUM(CASE WHEN event_date_parsed IS NOT NULL THEN 1 ELSE 0 END) AS parsed_rows,
  SUM(CASE WHEN event_date_parsed IS NULL THEN 1 ELSE 0 END) AS unparsed_rows
FROM observation;
