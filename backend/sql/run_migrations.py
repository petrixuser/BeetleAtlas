import os
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT


SCRIPT_DIR = Path(__file__).resolve().parent

MIGRATIONS: list[tuple[str, str, str]] = [
    (
        "20260623_01_auth_and_write_consolidated",
        "consolidated auth and manual beetle write migrations",
        "ops/MigrateAuthAndWrite.sql",
    ),
    (
        "20260623_02_read_model_and_quality_consolidated",
        "consolidated read-model, index, and quality migrations",
        "ops/MigrateReadModelAndQuality.sql",
    ),
]


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable {name}.")
    return value


def _connect() -> pymysql.connections.Connection:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = _required_env("DB_USER")
    password = _required_env("DB_PASSWORD")
    database = os.getenv("DB_NAME", "beetle_db")

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def _read_sql(relative_path: str) -> str:
    sql_path = SCRIPT_DIR / relative_path
    return sql_path.read_text(encoding="utf-8")


def _execute_sql_script(cursor: pymysql.cursors.Cursor, sql_text: str) -> None:
    cursor.execute(sql_text)
    while cursor.nextset():
        pass


def _apply_schema_migrations_table(cursor: pymysql.cursors.Cursor) -> None:
    print("Applying SQL: schema/MigrateSchemaMigrations.sql")
    _execute_sql_script(cursor, _read_sql("schema/MigrateSchemaMigrations.sql"))


def _is_migration_applied(cursor: pymysql.cursors.Cursor, version: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE version = %s",
        (version,),
    )
    row = cursor.fetchone()
    return bool(row and int(row[0]) > 0)


def _record_migration(cursor: pymysql.cursors.Cursor, version: str, description: str) -> None:
    cursor.execute(
        "INSERT INTO schema_migrations(version, description) VALUES (%s, %s)",
        (version, description),
    )


def run() -> None:
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            _apply_schema_migrations_table(cursor)

            for version, description, relative_sql_path in MIGRATIONS:
                if _is_migration_applied(cursor, version):
                    print(f"Skipping {version} (already applied)")
                    continue

                print(f"Applying SQL: {relative_sql_path}")
                _execute_sql_script(cursor, _read_sql(relative_sql_path))
                _record_migration(cursor, version, description)
                print(f"Applied {version}")

            conn.commit()

            print("Done. Applied migrations registry:")
            cursor.execute(
                "SELECT version, COALESCE(description, ''), applied_at "
                "FROM schema_migrations ORDER BY applied_at, version"
            )
            for version, description, applied_at in cursor.fetchall():
                print(f"{version} | {description} | {applied_at}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
