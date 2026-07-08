#!/bin/bash
# ============================================================================
#  BeetleAtlas — LOKALE Version beenden
#  Im Finder doppelklicken. Fährt die lokalen Container sauber herunter.
#  Die Daten bleiben erhalten (Docker-Volume), der nächste Start ist schnell.
# ============================================================================
set -u
cd "$(dirname "$0")" || exit 1

COMPOSE="docker-compose.dev.yml"

echo "Beende lokale BeetleAtlas-Container ..."
docker compose -f "$COMPOSE" down

echo
echo "✅ Gestoppt. Die Daten bleiben gespeichert – beim nächsten Start geht es schnell."
echo "Drücke Enter zum Schließen."
read -r _
