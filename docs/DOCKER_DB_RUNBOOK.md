# Full Runbook: DB + Frontend + Backend

Dieses Runbook startet den kompletten Stack:
- MySQL (`beetle-mysql`)
- Frontend (`beetle-frontend`)
- Backend (`beetle-backend`)

## Kurzstart (Daily)

```bash
# 1) In den Repo-Ordner
cd /mnt/c/Users/49173/Downloads/BeetleAtlas-main/BeetleAtlas-main

# 2) MySQL starten (falls externer DB-Container genutzt wird)
docker start beetle-mysql

# 3) Frontend + Backend starten
docker compose -f docker/docker-compose.yml up --build -d

# 4) Status pruefen
docker ps
```

Danach erreichbar:
- Frontend: http://localhost:8080
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Ausfuehrlich

### 1) Voraussetzungen

- Docker Daemon laeuft.
- Repo ist lokal vorhanden.
- Falls eigener DB-Container genutzt wird: `beetle-mysql` existiert.

### 2) Datenbank starten oder erstellen

Falls `beetle-mysql` schon existiert:

```bash
docker start beetle-mysql
```

Falls nicht vorhanden (einmalig):

```bash
docker run -d --name beetle-mysql \
  --network host \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=beetle_db \
  -v beetle_mysql_data:/var/lib/mysql \
  mysql:8.0
```

DB-Check:

```bash
docker exec -it beetle-mysql mysql -uroot -proot123 -e "SHOW DATABASES;"
```

### 3) Frontend + Backend starten

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Logs pruefen:

```bash
docker compose -f docker/docker-compose.yml logs -f beetle-backend
```

### 4) Optional: DB initialisieren/importieren

Schema anwenden:

```bash
cat SQL/DatabseShema.sql | docker exec -i beetle-mysql mysql -uroot -proot123
```

GBIF CSV importieren:

```bash
docker exec -i beetle-mysql sh -lc "mkdir -p /var/lib/mysql-files"
docker cp csv/beetle_species.csv beetle-mysql:/var/lib/mysql-files/beetle_species.csv
docker cp csv/location.csv beetle-mysql:/var/lib/mysql-files/location.csv
docker cp csv/observation.csv beetle-mysql:/var/lib/mysql-files/observation.csv
docker cp csv/media.csv beetle-mysql:/var/lib/mysql-files/media.csv
cat SQL/LoadGBIFCSVToDB.sql | docker exec -i beetle-mysql mysql -uroot -proot123
```

Climate Snapshot importieren:

```bash
docker cp csv/climate_snapshot_import.csv beetle-mysql:/var/lib/mysql-files/climate_snapshot_import.csv
cat SQL/LoadClimateSnapshot.sql | docker exec -i beetle-mysql mysql -uroot -proot123
```

### 5) Health Checks

Backend Health:

```bash
curl http://localhost:8000/health
```

API Stats:

```bash
curl http://localhost:8000/stats/overview
```

### 6) Stoppen

Nur Frontend + Backend stoppen:

```bash
docker compose -f docker/docker-compose.yml down
```

DB ebenfalls stoppen:

```bash
docker stop beetle-mysql
```

## Haeufige Probleme

1. Docker daemon nicht erreichbar

```bash
sudo systemctl restart docker
docker ps
```

2. Backend startet, aber keine DB-Verbindung
- Pruefen ob `beetle-mysql` laeuft.
- Pruefen ob `DB_HOST`/`DB_PORT` in `.env` zu deiner Umgebung passen.

3. CSV-Import fehlschlaegt

```bash
docker exec -it beetle-mysql sh -lc "ls -lh /var/lib/mysql-files"
```
