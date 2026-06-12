import os
import logging
import time
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, event


load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root123")
DB_NAME = os.getenv("DB_NAME", "beetle_db")
SLOW_QUERY_MS = int(os.getenv("SLOW_QUERY_MS", "300"))
ENABLE_SLOW_QUERY_LOGGING = os.getenv("ENABLE_SLOW_QUERY_LOGGING", "true").lower() == "true"

logger = logging.getLogger("beetle.backend.db")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(_, cursor, statement, parameters, context, executemany):
    del cursor, statement, parameters, executemany
    context._query_start_time = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(_, cursor, statement, parameters, context, executemany):
    del cursor, parameters, executemany
    if not ENABLE_SLOW_QUERY_LOGGING:
        return

    started = getattr(context, "_query_start_time", None)
    if started is None:
        return

    elapsed_ms = (time.perf_counter() - started) * 1000
    if elapsed_ms >= SLOW_QUERY_MS:
        compact_sql = " ".join(statement.split())
        truncated_sql = compact_sql[:500]
        logger.warning(
            "Slow query detected: %.1f ms (threshold=%d ms) sql=%s",
            elapsed_ms,
            SLOW_QUERY_MS,
            truncated_sql,
        )


@contextmanager
def get_connection():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
