#!/usr/bin/env sh
set -eu

DB_CONTAINER="${DB_CONTAINER:-beetle-db}"
DB_NAME="${DB_NAME:-beetle_db}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-root123}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"

mysql_exec() {
  docker exec -i "$DB_CONTAINER" mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME"
}

mysql_query_scalar() {
  docker exec -i "$DB_CONTAINER" mysql -N -s -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$1"
}

run_sql_file() {
  sql_file="$1"
  echo "Applying SQL: $sql_file"
  mysql_exec < "$sql_file"
}

apply_versioned_migration() {
  version="$1"
  description="$2"
  filename="$3"
  sql_path="$SCRIPT_DIR/$filename"

  already_applied="$(mysql_query_scalar "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';")"
  if [ "$already_applied" -gt 0 ]; then
    echo "Skipping $version (already applied)"
    return
  fi

  run_sql_file "$sql_path"
  mysql_query_scalar "INSERT INTO schema_migrations(version, description) VALUES ('$version', '$description');" >/dev/null
  echo "Applied $version"
}

run_sql_file "$SCRIPT_DIR/MigrateSchemaMigrations.sql"

apply_versioned_migration "20260610_01_event_date_parsed" "event_date_parsed column and index" "MigrateObservationEventDateParsed.sql"
apply_versioned_migration "20260610_02_media_gbif_media_id_index" "media composite index for deterministic pagination" "MigrateMediaGbifMediaIdIndex.sql"
apply_versioned_migration "20260610_03_quality_report_history" "quality report history table" "MigrateQualityReportHistory.sql"
apply_versioned_migration "20260610_04_data_validation_checks" "domain checks for location, observation and climate snapshot" "MigrateDataValidationChecks.sql"
apply_versioned_migration "20260610_05_climate_validation_normalization" "normalize invalid climate values and enforce remaining checks" "MigrateClimateValidationNormalization.sql"

echo "Done. Applied migrations registry:"
mysql_query_scalar "SELECT CONCAT(version, ' | ', COALESCE(description, ''), ' | ', applied_at) FROM schema_migrations ORDER BY applied_at, version;"
