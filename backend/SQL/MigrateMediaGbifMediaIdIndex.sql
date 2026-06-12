USE beetle_db;

SET @sql := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'media'
        AND index_name = 'idx_media_gbif_media_id'
    ),
    'SELECT "idx_media_gbif_media_id already exists"',
    'CREATE INDEX idx_media_gbif_media_id ON media (gbif_id, media_id)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT
  table_name,
  index_name,
  GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ', ') AS index_columns
FROM information_schema.statistics
WHERE table_schema = DATABASE()
  AND table_name = 'media'
  AND index_name IN ('idx_media_gbif_id', 'idx_media_gbif_media_id')
GROUP BY table_name, index_name
ORDER BY index_name;
