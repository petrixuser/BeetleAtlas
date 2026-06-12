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

Drei Punkte, die ich mit dir klaeren muss, bevor das produktiv geht:

1. **climate_snapshot bleibt beim Seed leer** — `DatabseShema.sql` legt den
   `chk_climate_relative_humidity`-Constraint direkt beim CREATE TABLE an, aber deine
   `MigrateClimateValidationNormalization.sql` setzt voraus, dass erst normalisiert und der
   Constraint danach gesetzt wird. Auf einer frischen DB bricht der Climate-Seed deshalb ab
   (0 Zeilen). Wie willst du das loesen — Constraint erst per Migration nach der
   Normalisierung?
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
