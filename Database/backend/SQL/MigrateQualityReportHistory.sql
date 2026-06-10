USE beetle_db;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = DATABASE()
        AND table_name = 'quality_report_history'
    ),
    'SELECT "quality_report_history already exists"',
    'CREATE TABLE quality_report_history (
      quality_report_id BIGINT NOT NULL AUTO_INCREMENT,
      generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      source_label VARCHAR(128) NULL,
      observation_count BIGINT NOT NULL,
      location_count BIGINT NOT NULL,
      climate_snapshot_count BIGINT NOT NULL,
      observation_null_rates_json JSON NOT NULL,
      location_null_rates_json JSON NOT NULL,
      climate_snapshot_null_rates_json JSON NOT NULL,
      ee_coverage_json JSON NOT NULL,
      PRIMARY KEY (quality_report_id),
      KEY idx_quality_report_generated_at (generated_at),
      KEY idx_quality_report_source (source_label)
    ) ENGINE=InnoDB'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT
  COUNT(*) AS history_rows,
  MIN(generated_at) AS first_snapshot_at,
  MAX(generated_at) AS latest_snapshot_at
FROM quality_report_history;
