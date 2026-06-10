USE beetle_db;

INSERT INTO quality_report_history (
  source_label,
  observation_count,
  location_count,
  climate_snapshot_count,
  observation_null_rates_json,
  location_null_rates_json,
  climate_snapshot_null_rates_json,
  ee_coverage_json
)
WITH
totals AS (
  SELECT
    (SELECT COUNT(*) FROM observation) AS observation_count,
    (SELECT COUNT(*) FROM location) AS location_count,
    (SELECT COUNT(*) FROM climate_snapshot) AS climate_snapshot_count
),
observation_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'event_date', 'missing', SUM(CASE WHEN event_date IS NULL OR TRIM(event_date) = '' THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'event_date_parsed', 'missing', SUM(CASE WHEN event_date_parsed IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'basis_of_record', 'missing', SUM(CASE WHEN basis_of_record IS NULL OR TRIM(basis_of_record) = '' THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'taxon_id', 'missing', SUM(CASE WHEN taxon_id IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'location_id', 'missing', SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'image_available', 'missing', SUM(CASE WHEN image_available IS NULL THEN 1 ELSE 0 END))
  ) AS payload
  FROM observation
),
location_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'latitude', 'missing', SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'longitude', 'missing', SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'elevation', 'missing', SUM(CASE WHEN elevation IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'coordinate_uncertainty', 'missing', SUM(CASE WHEN coordinate_uncertainty IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'worldclim_bio01', 'missing', SUM(CASE WHEN worldclim_bio01 IS NULL OR worldclim_bio01 = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'worldclim_bio12', 'missing', SUM(CASE WHEN worldclim_bio12 IS NULL OR worldclim_bio12 = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_ph', 'missing', SUM(CASE WHEN soil_ph IS NULL OR soil_ph = -9999 THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_organic_carbon', 'missing', SUM(CASE WHEN soil_organic_carbon IS NULL OR soil_organic_carbon = -9999 THEN 1 ELSE 0 END))
  ) AS payload
  FROM location
),
climate_nulls AS (
  SELECT JSON_ARRAY(
    JSON_OBJECT('field', 'avg_temperature', 'missing', SUM(CASE WHEN avg_temperature IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'precipitation', 'missing', SUM(CASE WHEN precipitation IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'soil_moisture', 'missing', SUM(CASE WHEN soil_moisture IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'ndvi', 'missing', SUM(CASE WHEN ndvi IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'relative_humidity', 'missing', SUM(CASE WHEN relative_humidity IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'surface_pressure_hpa', 'missing', SUM(CASE WHEN surface_pressure_hpa IS NULL THEN 1 ELSE 0 END)),
    JSON_OBJECT('field', 'nighttime_lights', 'missing', SUM(CASE WHEN nighttime_lights IS NULL THEN 1 ELSE 0 END))
  ) AS payload
  FROM climate_snapshot
),
ee_coverage AS (
  SELECT JSON_OBJECT(
    'withSnapshotMatch', SUM(
      CASE WHEN EXISTS (
        SELECT 1
        FROM climate_snapshot cs
        WHERE cs.location_id = o.location_id
          AND cs.snapshot_date <= COALESCE(
            o.event_date_parsed,
            STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
            DATE('9999-12-31')
          )
      ) THEN 1 ELSE 0 END
    ),
    'withoutSnapshotMatch', GREATEST(COUNT(*) - SUM(
      CASE WHEN EXISTS (
        SELECT 1
        FROM climate_snapshot cs
        WHERE cs.location_id = o.location_id
          AND cs.snapshot_date <= COALESCE(
            o.event_date_parsed,
            STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
            DATE('9999-12-31')
          )
      ) THEN 1 ELSE 0 END
    ), 0)
  ) AS payload
  FROM observation o
)
SELECT
  'seed_import',
  t.observation_count,
  t.location_count,
  t.climate_snapshot_count,
  onl.payload,
  lnl.payload,
  cnl.payload,
  ee.payload
FROM totals t
CROSS JOIN observation_nulls onl
CROSS JOIN location_nulls lnl
CROSS JOIN climate_nulls cnl
CROSS JOIN ee_coverage ee;

SELECT
  quality_report_id,
  generated_at,
  source_label,
  observation_count,
  location_count,
  climate_snapshot_count
FROM quality_report_history
ORDER BY quality_report_id DESC
LIMIT 1;
