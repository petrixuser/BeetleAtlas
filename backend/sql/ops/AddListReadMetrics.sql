-- Ergaenzt beetle_list_read um die vorberechneten Zahlenwerte Temperatur,

SET SESSION sql_mode = '';

SET @has_temp := (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'beetle_list_read' AND column_name = 'temperature'
);
SET @sql := IF(@has_temp = 0,
  'ALTER TABLE beetle_list_read ADD COLUMN temperature DOUBLE NULL AFTER elevation',
  'SELECT "temperature exists"');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @has_prec := (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'beetle_list_read' AND column_name = 'precipitation'
);
SET @sql := IF(@has_prec = 0,
  'ALTER TABLE beetle_list_read ADD COLUMN precipitation DOUBLE NULL AFTER temperature',
  'SELECT "precipitation exists"');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @has_ph := (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'beetle_list_read' AND column_name = 'soil_ph'
);
SET @sql := IF(@has_ph = 0,
  'ALTER TABLE beetle_list_read ADD COLUMN soil_ph DOUBLE NULL AFTER precipitation',
  'SELECT "soil_ph exists"');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

UPDATE beetle_list_read e
JOIN map_point_read m
  ON m.entity_id = e.entity_id AND m.source_type = 'observation'
JOIN observation o ON o.gbif_id = m.gbif_id
JOIN location l ON l.location_id = o.location_id
LEFT JOIN climate_snapshot lc
  ON lc.location_id = l.location_id
 AND lc.snapshot_date = (
      SELECT MAX(cs2.snapshot_date)
      FROM climate_snapshot cs2
      WHERE cs2.location_id = l.location_id
        AND cs2.snapshot_date <= COALESCE(
              o.event_date_parsed,
              STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
              DATE('9999-12-31')
            )
    )
SET
  e.temperature = COALESCE(
    lc.avg_temperature,
    CASE
      WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
      WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
      ELSE l.worldclim_bio01
    END
  ),
  e.precipitation = COALESCE(lc.precipitation, l.worldclim_bio12),
  e.soil_ph = CASE
      WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
      WHEN l.soil_ph > 14 THEN l.soil_ph / 10
      ELSE l.soil_ph
    END;

-- 3) Manuelle Zeilen: aus beetle_record (wie die Detailabfrage fuer 'manual') --
UPDATE beetle_list_read e
JOIN map_point_read m
  ON m.entity_id = e.entity_id AND m.source_type = 'manual'
JOIN beetle_record br ON br.record_id = m.record_id
SET
  e.temperature = COALESCE(
    br.temperature,
    CASE
      WHEN br.worldclim_bio01 IS NULL OR br.worldclim_bio01 = -9999 THEN NULL
      WHEN br.worldclim_bio01 > 80 THEN br.worldclim_bio01 / 10
      ELSE br.worldclim_bio01
    END
  ),
  e.precipitation = COALESCE(br.precipitation, br.worldclim_bio12),
  e.soil_ph = CASE
      WHEN br.soil_ph IS NULL OR br.soil_ph = -9999 THEN NULL
      WHEN br.soil_ph > 14 THEN br.soil_ph / 10
      ELSE br.soil_ph
    END;
