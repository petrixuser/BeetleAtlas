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

Use the `docker-compose.yml` in this repository as the stack definition.

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

1. Open Portainer → Stacks → Add Stack
2. Name: `BeetleAtlas`
3. Paste contents of `docker-compose.yml`
4. Add environment variable `GMAPS_KEY` with your Google Maps API key
5. Deploy the stack

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

Requires `frontend/config.local.js` with your `window.GMAPS_KEY`.

---

## Data Sources

| Layer       | Source                                      | License     |
|-------------|---------------------------------------------|-------------|
| Elevation   | OpenTopoMap tiles                           | CC-BY-SA    |
| Climate     | Beck et al. (2023) Köppen-Geiger 1991–2020  | CC-BY 4.0   |
| Vegetation  | WWF Terrestrial Ecoregions                  | Non-commercial |
| Countries   | Custom GeoJSON                              | —           |
