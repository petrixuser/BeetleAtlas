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
