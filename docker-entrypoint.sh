#!/bin/sh
# Container-Startskript des Frontends (nginx): injiziert die Laufzeit-Konfiguration
# und startet danach nginx im Vordergrund.
set -e

# Laufzeit-Konfiguration injizieren, damit Secrets nie ins Image gebacken werden.
# GMAPS_KEY und optional API_BASE_URL als Container-Umgebungsvariablen setzen.
CONFIG_DIR=/usr/share/nginx/html/config
CONFIG=$CONFIG_DIR/config.local.js

mkdir -p "$CONFIG_DIR"

printf 'window.GMAPS_KEY = "%s";\n' "${GMAPS_KEY:-}"       > "$CONFIG"
printf 'window.API_BASE_URL = "%s";\n' "${API_BASE_URL:-}" >> "$CONFIG"

exec nginx -g 'daemon off;'
