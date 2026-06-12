#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-beetle-db}"
DB_PORT="${DB_PORT:-3306}"
APP_MODULE="${API_APP_MODULE:-backend.App.core.main:app}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"

wait_for_db() {
  echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
  i=0
  until python - "$DB_HOST" "$DB_PORT" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket()
sock.settimeout(2)
try:
    sock.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
  do
    i=$((i + 1))
    if [ "$i" -ge 60 ]; then
      echo "Database not reachable after 60 attempts"
      exit 1
    fi
    sleep 2
  done
  echo "Database is reachable."
}

wait_for_db

echo "Starting API ${APP_MODULE} on ${API_HOST}:${API_PORT}"
exec uvicorn "$APP_MODULE" --host "$API_HOST" --port "$API_PORT"
