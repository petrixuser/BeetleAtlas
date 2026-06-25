#!/usr/bin/env sh
set -eu

DB_CONTAINER="${DB_CONTAINER:-beetle-db}"
DB_NAME="${DB_NAME:-beetle_db}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [ -z "$DB_PASSWORD" ]; then
  echo "DB_PASSWORD must be set."
  exit 1
fi

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

apply_versioned_migration "20260623_01_auth_and_write_consolidated" "consolidated auth and manual beetle write migrations" "ops/MigrateAuthAndWrite.sql"
apply_versioned_migration "20260623_02_read_model_and_quality_consolidated" "consolidated read-model, index, and quality migrations" "ops/MigrateReadModelAndQuality.sql"

echo "Done. Applied migrations registry:"
mysql_query_scalar "SELECT CONCAT(version, ' | ', COALESCE(description, ''), ' | ', applied_at) FROM schema_migrations ORDER BY applied_at, version;"
