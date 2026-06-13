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

Wir betreiben das Ganze auf der NAS/dem Server von einem Kumpel (ueber Portainer, wie
gehabt) — also Frontend + Backend + DB live ueber die echte URL, danach wird es nicht
weiter dauerhaft betrieben. Da es ein Uni-Projekt ist, halte ich die offenen Punkte
bewusst simpel — alles nur zur Info, nichts, was dich blockiert:

1. **climate_snapshot-Seed (FYI, schon gefixt):** Auf einer frischen DB brach der
   Climate-Seed ab (0 Zeilen) — `DatabseShema.sql` legt den
   `chk_climate_relative_humidity`-Constraint direkt beim CREATE TABLE an, aber deine
   `MigrateClimateValidationNormalization.sql` setzt voraus, dass erst normalisiert und der
   Constraint danach gesetzt wird. Ich hab's so geloest: `LoadClimateSnapshot.sql`
   normalisiert die Out-of-Range-Werte (soil_moisture, ndvi, relative_humidity,
   nighttime_lights) jetzt direkt beim INSERT auf NULL, damit der Seed die Constraints
   erfuellt. Dein Schema-Endzustand bleibt unveraendert, deine Migration wird damit zum
   No-op. Sag Bescheid, falls du es lieber anders haben willst (z. B. Werte korrigieren
   statt verwerfen) — laeuft aber lokal jetzt sauber durch.
2. **CSV-Daten (~215MB) bleiben im Repo (FYI):** GitHub meckert zwar wegen der Groesse,
   aber fuer ein Uni-Projekt reicht das. Kein DB-Dump/Auslagern — zu viel Aufwand. Auf
   der NAS importieren wir die Daten ueber die Init-Skripte in die DB (wie in der
   Dev-Compose). Falls spaeter mal sauberer gewuenscht, holen wir das nach.
3. **DB-Zugangsdaten bleiben simpel (FYI):** `root123` bleibt, kein Produktions-Secrets-
   Setup. Unbedenklich, weil die DB auf der NAS nur im internen Docker-Netz laeuft und
   nicht aus dem Internet erreichbar ist (nur Frontend + API gehen ueber den Proxy nach
   aussen). Auch das aendern wir, falls noetig.

Voll dokumentiert im `docs/WORKLOG.md`.

---

## An den NAS-Kumpel (Server-Besitzer)

Hey, ich moechte das Kaefer-Projekt erweitern: Aktuell laeuft bei dir nur das statische
Frontend (nginx). Damit echte Daten angezeigt werden, kommen ein **Backend
(Python/FastAPI)** und eine **MySQL-Datenbank** dazu. Ich hab alles vorbereitet (Images
bauen automatisch via GitHub Actions nach GHCR, Compose liegt im Repo als
`docker-compose.prod.yml`). Was ich von dir braeuchte:

1. **Ressourcen ok?** Eine dauerhaft laufende DB ist schwerer als der statische Container:
   grob **1-2 GB Plattenplatz**, und beim Abfragen **RAM-hungrig**. Sag mir, wie viel **RAM**
   die NAS frei hat und ob die Daten auf **SSD oder HDD** liegen — davon haengt ab, wie
   schnell die Karte laedt (aktuell 10-40s pro Abfrage auf einer schwachen Test-VM).
2. **Backups**: Soll das DB-Volume (`beetle_db_data`) in deine Backups? Was passiert bei
   NAS-Neustart (Volume bleibt erhalten, DB muss nur wieder starten).
3. **Stack in Portainer**: Am einfachsten als **Git-Repository-Stack** anlegen (Repo
   `https://github.com/petrixuser/BeetleAtlas`, Compose-Pfad `docker-compose.prod.yml`).
   Dann zieht Portainer das Repo inkl. der Seed-Daten selbst. Folgende **Environment-
   Variablen** im Stack setzen:
   - `GMAPS_KEY` = (derselbe Google-Maps-Key wie bisher)
   - `API_BASE_URL` = `https://api.kafer.server-work.de`
   - `FRONTEND_ORIGINS` = `https://kafer.server-work.de`
   - (`DB_PASSWORD` optional — Default `root123` reicht, die DB ist nur intern erreichbar)
4. **Netzwerk / Nginx Proxy Manager**: Bitte zwei Routen einrichten:
   - `kafer.server-work.de` → `beetle-frontend:80` (wie bisher, nur evtl. Containername neu)
   - **neu:** `api.kafer.server-work.de` → `beetle-backend:8000`
   Die DB wird NICHT nach aussen veroeffentlicht, laeuft nur im internen Docker-Netz.

Beim allerersten Start importiert die DB die Daten selbst (~417k Datensaetze, dauert ein
paar Minuten) — danach liegt alles im Volume und der Start ist schnell. Kein Stress, sag
einfach, was an Ressourcen geht, dann stimmen wir den Rest ab.
