"""Wendet die versionierten SQL-Migrationen auf die Datenbank an.

Das Skript verbindet sich mit der MySQL-/MariaDB-Datenbank, legt bei Bedarf den
DB-Benutzer der Anwendung an, stellt die Tabelle schema_migrations sicher und
fuehrt anschliessend alle noch nicht angewandten Migrationen aus der Liste
MIGRATIONS in Reihenfolge aus. Bereits angewandte Migrationen werden anhand von
schema_migrations uebersprungen. Alle Aenderungen laufen in einer Transaktion:
Bei einem Fehler wird ein Rollback ausgefuehrt.
"""

import os
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT


SCRIPT_DIR = Path(__file__).resolve().parent

MIGRATIONS: list[tuple[str, str, str]] = [
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
    (
        "20260713_05_add_list_read_metrics",
        "add temperature/precipitation/soil_ph columns to beetle_list_read and backfill",
        "ops/AddListReadMetrics.sql",
    ),

]


def _required_env(name: str) -> str:
    """Liest eine Pflicht-Umgebungsvariable; wirft einen Fehler, wenn sie fehlt."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable {name}.")
    return value


def _migration_credentials() -> tuple[str, str]:
    """Liefert das (user, password), das zum AUSFUEHREN DER MIGRATIONEN genutzt wird.
    """
    migration_user = os.getenv("DB_MIGRATION_USER", "").strip()
    migration_password = os.getenv("DB_MIGRATION_PASSWORD", "")
    if migration_user:
        return migration_user, migration_password
    return _required_env("DB_USER"), _required_env("DB_PASSWORD")


def _connect() -> pymysql.connections.Connection:
    """Baut die Datenbankverbindung aus den Umgebungsvariablen auf."""
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
    """Stellt sicher, dass der DB-Benutzer der Anwendung mit minimalen Rechten existiert."""
    migration_user = os.getenv("DB_MIGRATION_USER", "").strip()
    app_user = os.getenv("DB_USER", "").strip()
    app_password = os.getenv("DB_PASSWORD", "")
    if not migration_user or not app_user:
        return  # bereits als App-Benutzer verbunden (dev/frisch) - nichts zu tun
    if app_user.lower() == migration_user.lower():
        return  # App nutzt den privilegierten Benutzer direkt - kein separater Benutzer noetig

    db_name = os.getenv("DB_NAME", "beetle_db")
    if not all(ch.isalnum() or ch == "_" for ch in db_name):
        raise RuntimeError(f"Refusing to grant on unsafe DB_NAME: {db_name!r}")

    print(f"Ensuring application DB user '{app_user}' exists with scoped grants...")
    cursor.execute("CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
    cursor.execute("ALTER USER %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
    cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@'%%'", (app_user,))
    cursor.execute("FLUSH PRIVILEGES")


def _read_sql(relative_path: str) -> str:
    """Liest ein SQL-Skript vom angegebenen relativen Pfad (relativ zu dieser Datei)."""
    sql_path = SCRIPT_DIR / relative_path

    return sql_path.read_text(encoding="utf-8-sig")


def _split_sql_statements(sql_text: str) -> list[str]:
    """Teilt ein SQL-Skript in einzelne Statements auf und beachtet dabei
    `DELIMITER`-Direktiven. pymysql kann `DELIMITER`/`CREATE PROCEDURE ... $$`
    Bloecke nicht als einen Block ausfuehren (DELIMITER ist eine clientseitige
    Direktive, kein Server-SQL). Daher bilden wir das Verhalten der mysql-CLI
    nach: Wir verfolgen den aktiven Delimiter und geben jedes Mal ein Statement
    aus, wenn eine Zeile damit endet. Statements, die nur aus
    Kommentaren/Leerzeichen bestehen, werden uebersprungen.
    """
    statements: list[str] = []
    delimiter = ";"
    buffer: list[str] = []

    def _flush() -> None:
        """Haengt den gepufferten Statement-Text an die Ergebnisliste an (ausser reine Kommentare)."""
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
    """Fuehrt alle Statements eines SQL-Skripts nacheinander aus."""
    for statement in _split_sql_statements(sql_text):
        cursor.execute(statement)
        while cursor.nextset():
            pass


def _apply_schema_migrations_table(cursor: pymysql.cursors.Cursor) -> None:
    """Legt die Tabelle schema_migrations an (falls noch nicht vorhanden)."""
    print("Applying SQL: schema/MigrateSchemaMigrations.sql")
    _execute_sql_script(cursor, _read_sql("schema/MigrateSchemaMigrations.sql"))


def _is_migration_applied(cursor: pymysql.cursors.Cursor, version: str) -> bool:
    """Prueft, ob eine Migration mit der angegebenen Version bereits angewandt wurde."""
    cursor.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE version = %s",
        (version,),
    )
    row = cursor.fetchone()
    return bool(row and int(row[0]) > 0)


def _record_migration(cursor: pymysql.cursors.Cursor, version: str, description: str) -> None:
    """Traegt eine angewandte Migration in schema_migrations ein."""
    cursor.execute(
        "INSERT INTO schema_migrations(version, description) VALUES (%s, %s)",
        (version, description),
    )


def run() -> None:
    """Fuehrt alle ausstehenden Migrationen in Reihenfolge aus und gibt das Registry aus."""
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
