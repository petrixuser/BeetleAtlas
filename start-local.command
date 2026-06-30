#!/bin/bash
# ============================================================================
#  BeetleAtlas — LOKALE Backup-Version starten (für den Vortrag)
#  Einfach im Finder doppelklicken. Startet den kompletten Stack auf dem Laptop,
#  völlig unabhängig vom Server, und öffnet den Browser auf http://localhost:8080
# ============================================================================
set -u

# Immer aus dem Projektordner heraus arbeiten (Ordner, in dem dieses Skript liegt)
cd "$(dirname "$0")" || { echo "Projektordner nicht gefunden."; exit 1; }

COMPOSE="docker-compose.dev.yml"
URL="http://localhost:8080"

echo "============================================================"
echo "  BeetleAtlas – lokale Version wird gestartet"
echo "============================================================"

# ---- 1) Docker Desktop sicherstellen --------------------------------------
if ! docker info >/dev/null 2>&1; then
  echo "Docker läuft noch nicht – starte Docker Desktop ..."
  open -a Docker 2>/dev/null
  printf "Warte auf Docker"
  for i in $(seq 1 60); do
    if docker info >/dev/null 2>&1; then echo " – bereit."; break; fi
    printf "."
    sleep 2
  done
  if ! docker info >/dev/null 2>&1; then
    echo
    echo "FEHLER: Docker Desktop ist nicht bereit. Bitte manuell starten und erneut versuchen."
    echo "Drücke Enter zum Schließen."; read -r _; exit 1
  fi
fi

# ---- 2) Stack starten (vorgebaute Images nutzen, KEIN Rebuild) ------------
echo "Starte Container ..."
echo "(Beim ALLERERSTEN Start wird die Datenbank befüllt – das kann 3–5 Minuten"
echo " dauern. Bitte Geduld, das Fenster nicht schließen. Spätere Starts: ~15 Sek.)"
if ! docker compose -f "$COMPOSE" up -d --no-build 2>/tmp/beetle_up_err.log; then
  echo "Images fehlen oder sind unvollständig – baue sie jetzt (einmalig, dauert ein paar Minuten)."
  # WICHTIG: Services EINZELN bauen mit COMPOSE_BAKE=false.
  # Grund: Der Ordnername enthält ein "ä" (nicht-ASCII), womit der Docker-Bake-
  # Build-Pfad abstürzt. Einzel-Builds ohne Bake umgehen das zuverlässig.
  for svc in beetle-db beetle-backend beetle-frontend; do
    echo ">> baue $svc ..."
    COMPOSE_BAKE=false docker compose -f "$COMPOSE" build "$svc" || {
      echo "FEHLER beim Bauen von $svc."; echo "Drücke Enter zum Schließen."; read -r _; exit 1; }
  done
  docker compose -f "$COMPOSE" up -d --no-build || {
    echo "FEHLER beim Start."; echo "Drücke Enter zum Schließen."; read -r _; exit 1; }
fi

# ---- 3) Auf DB-Gesundheit warten (erster Start seedet die Daten) ----------
printf "Warte auf Datenbank (beim allerersten Start dauert das ~1 Min.)"
for i in $(seq 1 60); do
  h="$(docker inspect --format '{{.State.Health.Status}}' beetle-db 2>/dev/null)"
  if [ "$h" = "healthy" ]; then echo " – bereit."; break; fi
  printf "."
  sleep 3
done

# Backend/Frontend starten erst, wenn die DB gesund ist – nochmal sicherstellen:
docker compose -f "$COMPOSE" up -d --no-build >/dev/null 2>&1

# ---- 4) Auf Frontend warten ----------------------------------------------
printf "Warte auf Webseite"
for i in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$URL" 2>/dev/null)"
  if [ "$code" = "200" ]; then echo " – bereit."; break; fi
  printf "."
  sleep 2
done

# ---- 5) Status zeigen + Browser öffnen ------------------------------------
echo
echo "------------------------------------------------------------"
docker compose -f "$COMPOSE" ps
echo "------------------------------------------------------------"
echo
echo "  ✅ Lokale Version läuft:  $URL"
echo "     (läuft komplett auf diesem Laptop – der Server wird NICHT gebraucht)"
echo
echo "  Zum Beenden nach dem Vortrag: stop-local.command doppelklicken."
echo "------------------------------------------------------------"

open "$URL"

echo
echo "Dieses Fenster kann offen bleiben. Drücke Enter zum Schließen."
read -r _
