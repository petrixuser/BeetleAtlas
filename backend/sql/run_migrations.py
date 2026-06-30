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
    (
        "20260625_03_location_country_index",
        "index location.country for fast country-detail queries",
        "ops/MigrateLocationCountryIndex.sql",
    ),
    (
        "20260630_04_seed_test_researcher",
        "seed throwaway test researcher account (delete after verifying)",
        "ops/MigrateSeedTestResearcher.sql",
    ),
]


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable {name}.")
    return value


def _migration_credentials() -> tuple[str, str]:
    """Return the (user, password) used to RUN MIGRATIONS.

    Migrations are DDL (CREATE TABLE/PROCEDURE, ALTER, ...) and must run as a
    privileged DB account. The application's runtime user (DB_USER) is often a
    least-privilege account that lacks CREATE/CREATE ROUTINE — running migrations
    as it fails (e.g. "CREATE command denied"). So prefer dedicated migration
    credentials when provided, and only fall back to the app user otherwise (dev
    convenience). In production set DB_MIGRATION_USER=root and
    DB_MIGRATION_PASSWORD to the existing root password.
    """
    migration_user = os.getenv("DB_MIGRATION_USER", "").strip()
    migration_password = os.getenv("DB_MIGRATION_PASSWORD", "")
    if migration_user:
        return migration_user, migration_password
    return _required_env("DB_USER"), _required_env("DB_PASSWORD")


def _connect() -> pymysql.connections.Connection:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user, password = _migration_credentials()
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


def _maybe_bootstrap_app_user(cursor: pymysql.cursors.Cursor) -> None:
    """Ensure the least-privilege application DB user exists.

    The app code refuses to run as root (see backend/core/db.py) and connects as
    a dedicated user (DB_USER, e.g. beetle_app). On a FRESH volume MySQL creates
    that user from MYSQL_USER/MYSQL_PASSWORD, but on an EXISTING (in-place
    upgraded) volume it does not — and no SQL script creates it either, so the
    backend would fail to connect. When migrations run as a privileged user
    (DB_MIGRATION_USER set), create/refresh the app user here, idempotently,
    using the very same credentials the app will use (so they always match).
    Scope is a single schema (no global/admin rights) — non-root, as intended.
    """
    migration_user = os.getenv("DB_MIGRATION_USER", "").strip()
    app_user = os.getenv("DB_USER", "").strip()
    app_password = os.getenv("DB_PASSWORD", "")
    if not migration_user or not app_user:
        return  # connected as the app user already (dev/fresh) — nothing to do
    if app_user.lower() == migration_user.lower():
        return  # app uses the privileged user directly — no separate user needed

    db_name = os.getenv("DB_NAME", "beetle_db")
    if not all(ch.isalnum() or ch == "_" for ch in db_name):
        raise RuntimeError(f"Refusing to grant on unsafe DB_NAME: {db_name!r}")

    print(f"Ensuring application DB user '{app_user}' exists with scoped grants...")
    cursor.execute("CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
    cursor.execute("ALTER USER %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
    cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@'%%'", (app_user,))
    cursor.execute("FLUSH PRIVILEGES")


def _read_sql(relative_path: str) -> str:
    sql_path = SCRIPT_DIR / relative_path
    # utf-8-sig strips a leading BOM if present. The mysql CLI tolerates a BOM
    # (so initdb works), but pymysql passes it through as invalid SQL syntax.
    return sql_path.read_text(encoding="utf-8-sig")


def _split_sql_statements(sql_text: str) -> list[str]:
    """Split a SQL script into individual statements, honouring `DELIMITER`
    directives. pymysql cannot execute `DELIMITER`/`CREATE PROCEDURE ... $$`
    blocks as one blob (DELIMITER is a client-side directive, not server SQL),
    so we replicate the mysql CLI behaviour: track the active delimiter and emit
    one statement each time a line ends with it. Statements that are only
    comments/whitespace are skipped.
    """
    statements: list[str] = []
    delimiter = ";"
    buffer: list[str] = []

    def _flush() -> None:
        stmt = "\n".join(buffer).strip()
        if stmt and any(
            line.strip() and not line.strip().startswith("--")
            for line in stmt.splitlines()
        ):
            statements.append(stmt)
        buffer.clear()

    for raw_line in sql_text.splitlines():
        stripped = raw_line.strip()
        if stripped.upper().startswith("DELIMITER"):
            _flush()
            parts = stripped.split(None, 1)
            delimiter = parts[1].strip() if len(parts) > 1 else ";"
            continue

        buffer.append(raw_line)
        if raw_line.rstrip().endswith(delimiter):
            joined = "\n".join(buffer).rstrip()
            joined = joined[: -len(delimiter)].rstrip()
            buffer.clear()
            if joined.strip() and any(
                line.strip() and not line.strip().startswith("--")
                for line in joined.splitlines()
            ):
                statements.append(joined)

    _flush()
    return statements


def _execute_sql_script(cursor: pymysql.cursors.Cursor, sql_text: str) -> None:
    for statement in _split_sql_statements(sql_text):
        cursor.execute(statement)
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
            _maybe_bootstrap_app_user(cursor)
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
