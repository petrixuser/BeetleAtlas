# 🎤 BeetleAtlas lokal vorführen — Anleitung für den Vortrag

Diese lokale Version läuft **komplett auf deinem Laptop** und braucht den Server
(NAS/Portainer / kafer.server-work.de) **nicht**. Sie ist dein Sicherheitsnetz:
Falls die Live-Seite beim Vortrag streikt, zeigst du einfach die lokale.

Internet brauchst du trotzdem (WLAN/mobile Daten) – aber nur für die **Karte**
(Google Maps + Höhen-Kacheln). Alle Käfer-Daten kommen aus der lokalen Datenbank.

> **Die lokale Seite läuft auf:** http://localhost:8080
> **Nicht** die Live-Domain benutzen, wenn du die lokale Version zeigen willst.

---

## ✅ Voraussetzung (einmalig, schon erledigt)

- **Docker Desktop** ist installiert.
- Die Container-Images sind bereits gebaut und die Datenbank ist mit allen Daten
  befüllt (21.018 Arten, 417.581 Beobachtungen). Getestet und läuft.

---

## 🌙 Am Abend VOR dem Vortrag (1 Minute – wichtig!)

Damit am Vortragstag garantiert alles sofort läuft, einmal „warmlaufen" lassen:

1. **Docker Desktop** starten (Wal-Symbol oben in der Menüleiste abwarten, bis es ruhig ist).
2. Im Finder den Projektordner **Käferliebe** öffnen.
3. Doppelklick auf **`start-local.command`**.
4. Es öffnet sich ein Terminalfenster und nach kurzer Zeit der Browser auf
   http://localhost:8080. Prüfen: Karte da? Käfer-Punkte sichtbar? Suche/Filter ok?
5. Danach **`stop-local.command`** doppelklicken (oder offen lassen – egal).

> **Beim allerersten Start dauert es 3–5 Minuten** (Datenbank wird mit ~215 MB
> befüllt und Indizes werden aufgebaut). Das Terminal zeigt dabei
> `Container beetle-db Waiting` – das ist normal, **nicht abbrechen**. Danach
> startet alles in ~15 Sekunden. Die Daten bleiben gespeichert.

---

## 🎬 Am Vortragstag (3 Schritte)

1. **Docker Desktop starten** (falls nicht schon offen). Kurz warten, bis das
   Wal-Symbol in der Menüleiste „ruhig" ist.
2. Im Finder Doppelklick auf **`start-local.command`**.
3. Warten, bis sich der Browser automatisch auf **http://localhost:8080** öffnet.
   → **Fertig.** Das ist deine Demo. Terminalfenster einfach offen lassen.

**Nach dem Vortrag:** Doppelklick auf **`stop-local.command`** (oder Docker Desktop
beenden). Muss nicht sofort sein.

---

## 🆘 Fallback-Kaskade (wenn etwas klemmt)

**Stufe 1 – Lokale Version (Standard):** `start-local.command` → http://localhost:8080

**Stufe 2 – Manuell per Terminal** (falls der Doppelklick zickt):
Terminal öffnen, dann:
```bash
cd "/Users/perrystaedtke/Documents/New project/Käferliebe"
docker compose -f docker-compose.dev.yml up -d --no-build
```
Danach im Browser **http://localhost:8080** öffnen.

**Stufe 3 – Live-Seite:** Wenn der Server doch läuft: https://kafer.server-work.de

---

## 🔧 Troubleshooting (kurz & knapp)

| Problem | Lösung |
|---|---|
| **Karte bleibt grau** | Internet prüfen (WLAN/mobile Daten). Die Karte braucht Google Maps – Käfer-Daten kommen lokal, aber die Kartenkacheln aus dem Netz. |
| **„Docker läuft nicht"** | Docker Desktop manuell starten, Wal-Symbol abwarten, dann Skript erneut doppelklicken. |
| **Browser zeigt nichts / „kann nicht verbinden"** | 20–30 Sek. warten (Backend startet noch), Seite neu laden. Sonst Status prüfen: `docker compose -f docker-compose.dev.yml ps` |
| **Port 8080 belegt** | Andere App schließen, die Port 8080 nutzt. Oder: `stop-local.command`, kurz warten, `start-local.command`. |
| **Logs ansehen** | `docker compose -f docker-compose.dev.yml logs -f` |
| **Alles neu aufsetzen** (Notfall) | `docker compose -f docker-compose.dev.yml down` und dann `start-local.command` (baut bei Bedarf neu). |

---

## ℹ️ Technischer Hintergrund (für dich)

- Start/Stop laufen über **`docker-compose.dev.yml`** (4 Container: Frontend, Backend,
  MySQL mit eingebackenen Seed-Daten, Redis). Konfiguration/Secrets kommen aus **`.env`**.
- Das Frontend läuft auf Port **8080**, das Backend auf **8000**, die DB auf **3306** –
  alle nur lokal.
- **Wichtig beim Neu-Bauen:** Der Ordnername enthält ein „ä". Dadurch stürzt Dockers
  Standard-„Bake"-Build ab. Deshalb baut `start-local.command` die Images bei Bedarf
  **einzeln** mit `COMPOSE_BAKE=false` – das umgeht den Fehler. (Falls du je von Hand
  baust: nicht `docker compose build` für alles auf einmal, sondern pro Service und mit
  `COMPOSE_BAKE=false` davor.)
