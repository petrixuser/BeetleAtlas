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

run_sql_file "$SCRIPT_DIR/schema/MigrateSchemaMigrations.sql"

apply_versioned_migration "20260610_01_data_quality_and_history_bundle" "bundle: parsed event date, media index, quality history, validation checks, climate normalization" "ops/MigrateDataQualityAndHistory.sql"
apply_versioned_migration "20260617_01_auth_manual_beetles" "users and manual beetle records tables for RBAC write flows" "ops/MigrateAuthAndManualBeetles.sql"
apply_versioned_migration "20260617_02_auth_refresh_tokens" "refresh token persistence and rotation metadata" "ops/MigrateAuthRefreshTokens.sql"
apply_versioned_migration "20260617_03_beetle_write_bundle" "audit table + GBIF write fields for manual beetle records (excluding EE climate fields)" "ops/MigrateBeetleWrite.sql"

echo "Done. Applied migrations registry:"
mysql_query_scalar "SELECT CONCAT(version, ' | ', COALESCE(description, ''), ' | ', applied_at) FROM schema_migrations ORDER BY applied_at, version;"
