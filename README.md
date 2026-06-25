# BeetleAtlas

Frontend for the **Latin Americas Beetle Atlas** — a map-based research tool for finding and exploring beetle species across Latin America.

Live: [kafer.server-work.de](https://kafer.server-work.de)

---

## Deployment Architecture

```
GitHub Push (main)
  → GitHub Actions
    → Docker Build (nginx:alpine)
    → Push to ghcr.io/petrixuser/beetleatlas:latest
    → Portainer Webhook
      → NAS pulls latest image
        → Nginx Proxy Manager routes kafer.server-work.de → BeetleAtlas:80
```

---

## Image

```
ghcr.io/petrixuser/beetleatlas:latest
ghcr.io/petrixuser/beetleatlas:sha-<commit>   # for rollback
```

---

## Portainer Stack

Use `docker-compose.prod.yml` in this repository as the stack definition
(full stack: frontend + backend + MySQL). Deploy it as a Portainer **Git
repository** stack so the repo's SQL/CSV seed data is available on first start.

| Setting          | Value                                   |
|------------------|-----------------------------------------|
| Service name     | BeetleAtlas                             |
| Container name   | BeetleAtlas                             |
| Docker network   | npm_proxy (external)                    |
| Internal port    | 80                                      |

### Required environment variables in Portainer

| Variable      | Description                        |
|---------------|------------------------------------|
| `GMAPS_KEY`   | Google Maps JavaScript API Key     |
| `API_BASE_URL`| Backend URL (empty = demo mode)    |

### Optional: E-Mail-Verifikation per SMTP

| Variable | Beschreibung |
|---|---|
| `EMAIL_VERIFICATION_SEND_EMAIL` | `true` aktiviert SMTP-Versand (Default: `false`) |
| `EMAIL_VERIFICATION_BASE_URL` | Basis-URL fuer Verifikationslink (z. B. `https://kafer.server-work.de`) |
| `EMAIL_VERIFICATION_TTL_SECONDS` | Gueltigkeit des Verifikationstokens in Sekunden |
| `SMTP_HOST` | SMTP-Server Hostname |
| `SMTP_PORT` | SMTP-Port (z. B. `587` STARTTLS oder `465` SSL) |
| `SMTP_USERNAME` | SMTP-Benutzername (optional) |
| `SMTP_PASSWORD` | SMTP-Passwort (optional, falls Login noetig) |
| `SMTP_FROM_EMAIL` | Absenderadresse |
| `SMTP_USE_STARTTLS` | `true` fuer STARTTLS |
| `SMTP_USE_SSL` | `true` fuer SMTPS |

---

## Nginx Proxy Manager

| Setting          | Value        |
|------------------|--------------|
| Domain           | kafer.server-work.de |
| Scheme           | http         |
| Forward Hostname | BeetleAtlas  |
| Forward Port     | 80           |

---

## GitHub Secrets

| Secret                  | Set by               |
|-------------------------|----------------------|
| `PORTAINER_WEBHOOK_URL` | Manual (see below)   |

`GITHUB_TOKEN` is provided automatically by GitHub Actions for GHCR access.

---

## Manual Setup Steps

### 1. Portainer — Create Stack

1. Open Portainer → Stacks → Add Stack → **Git repository**
2. Name: `BeetleAtlas`, repo `https://github.com/petrixuser/BeetleAtlas`, compose path `docker-compose.prod.yml`
3. Add environment variables (`GMAPS_KEY`, `API_BASE_URL`, `FRONTEND_ORIGINS`)
4. Deploy the stack

### 2. Portainer — Get Webhook URL

1. Open the BeetleAtlas stack → Webhooks
2. Enable webhook
3. Copy the URL

### 3. GitHub — Add Secret

1. Go to repository Settings → Secrets and variables → Actions
2. Add secret: `PORTAINER_WEBHOOK_URL` = (webhook URL from step 2)

### 4. Nginx Proxy Manager — Add Proxy Host

1. Open NPM → Proxy Hosts → Add Proxy Host
2. Domain: `kafer.server-work.de`
3. Scheme: `http`, Forward Hostname: `BeetleAtlas`, Port: `80`
4. Enable SSL (Let's Encrypt)

---

## Rollback

```bash
# In Portainer: change image tag to a specific SHA commit
ghcr.io/petrixuser/beetleatlas:sha-<commit>
```

---

## Local Development

```bash
cd frontend
python3 -m http.server 4175
# open http://localhost:4175
```

Requires `frontend/config/config.local.js` with your `window.GMAPS_KEY`.

---

## Data Sources

| Layer       | Source                                      | License     |
|-------------|---------------------------------------------|-------------|
| Elevation   | OpenTopoMap tiles                           | CC-BY-SA    |
| Climate     | Beck et al. (2023) Köppen-Geiger 1991–2020  | CC-BY 4.0   |
| Vegetation  | WWF Terrestrial Ecoregions                  | Non-commercial |
| Countries   | Custom GeoJSON                              | —           |

---

## Produkt-Roadmap

Filterkarten erweitern (ph / temp /Niederschlag)

- Dschungel-Hintergrund verbessern
  - UX-Feinschliff, aber mit Fokus auf Performance und Lesbarkeit
- Jungle-Sounds (ausschaltbar)
  - optionales Feature, nicht als Default
  - mit klarem Audio-Toggle und gespeichertem Zustand in `localStorage`

-Länder sollen auch map punkte nach auswahl filtern.
-Stöber modus (Random einträge)

- code aufräumen