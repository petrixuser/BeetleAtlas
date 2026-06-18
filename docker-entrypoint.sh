#!/bin/sh
set -e

# Inject runtime config so secrets never bake into the image.
# Set GMAPS_KEY and optionally API_BASE_URL as container environment variables.
CONFIG=/usr/share/nginx/html/config.local.js

printf 'window.GMAPS_KEY = "%s";\n' "${GMAPS_KEY:-}"       > "$CONFIG"
printf 'window.API_BASE_URL = "%s";\n' "${API_BASE_URL:-}" >> "$CONFIG"

exec nginx -g 'daemon off;'
