# Nachrichten zum Weiterleiten — Stand 2026-06-12

Diese zwei Nachrichten sind vorformuliert und koennen so verschickt werden.
Hintergrund/Details: siehe `docs/WORKLOG.md`, Abschnitt "HANDOFF / NAECHSTE SESSION".

---

## An Basti

Hey Basti, kurzer Stand: Ich hab dein Backend in den `main`-Branch integriert (liegt jetzt
unter `backend/`, Importpfade + Docker angepasst, laeuft lokal mit DB + Frontend ueber
`docker-compose.dev.yml`). Frontend ist jetzt komplett ans Backend angebunden — Liste,
Filter und Karte (`/api/map/points` mit Clustering) ziehen echte Daten. Die DE/EN-
Vokabular-Sache hab ich geloest: Daten nutzen deine englischen Codes, UI zeigt deutsche
Labels.

Ein Punkt nur zur Info, zwei muss ich noch mit dir klaeren:

1. **climate_snapshot-Seed (nur FYI, schon gefixt):** Auf einer frischen DB bracht der
   Climate-Seed ab (0 Zeilen) — `DatabseShema.sql` legt den
   `chk_climate_relative_humidity`-Constraint direkt beim CREATE TABLE an, aber deine
   `MigrateClimateValidationNormalization.sql` setzt voraus, dass erst normalisiert und der
   Constraint danach gesetzt wird. Ich hab's so geloest: `LoadClimateSnapshot.sql`
   normalisiert die Out-of-Range-Werte (soil_moisture, ndvi, relative_humidity,
   nighttime_lights) jetzt direkt beim INSERT auf NULL, damit der Seed die Constraints
   erfuellt. Dein Schema-Endzustand bleibt unveraendert, deine Migration wird damit zum
   No-op. Sag Bescheid, falls du es lieber anders haben willst (z. B. Werte korrigieren
   statt verwerfen) — laeuft aber lokal jetzt sauber durch.
2. **CSV-Daten (~215MB)** liegen aktuell im Git-Repo (GitHub meckert wegen Groesse). So
   lassen oder lieber DB-Dump statt CSVs fuer die Produktion?
3. **DB-Zugangsdaten** fuer die Produktion — wer legt die fest (kommen als
   Portainer-Secrets, nicht ins Repo)?

Voll dokumentiert im `docs/WORKLOG.md`.

---

## An den NAS-Kumpel (Server-Besitzer)

Hey, ich wuerde gerne das Kaefer-Projekt erweitern: Aktuell laeuft bei dir nur das statische
Frontend (nginx). Damit echte Daten angezeigt werden, muessten ein **Backend
(Python/FastAPI)** und eine **MySQL-Datenbank** dazukommen. Bevor ich da was anfasse, ein
paar Fragen:

1. **Ist das ok fuer dich** — eine dauerhaft laufende DB ist ressourcenintensiver als der
   jetzige statische Container.
2. **Speicher/RAM**: Die DB braucht grob 1-2GB Plattenplatz und ist beim Abfragen
   RAM-hungrig. Hat die NAS dafuer Reserven?
3. **Backups**: Soll das DB-Volume in deine Backups rein? Was passiert bei NAS-Neustart?
4. **Netzwerk**: Backend soll intern erreichbar sein (`npm_proxy`), evtl. als Subdomain
   `api.kafer.server-work.de` ueber den Nginx Proxy Manager — koenntest du das einrichten?

Kein Stress, das ist erstmal nur zum Abstimmen. Lokal laeuft schon alles.
