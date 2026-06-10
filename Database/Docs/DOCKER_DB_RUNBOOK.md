# Full Runbook: DB + Frontend + Backend

Dieses Runbook startet den kompletten Stack per Docker Compose:
- MySQL (`beetle-db`)
- Backend (`beetle-backend`)
- Frontend (`beetle-frontend`)

Die DB wird beim ersten Start automatisch mit Schema und Kernindizes initialisiert.

## Kurzstart

```bash
# 1) In den Projektordner
cd Database

# 2) Stack starten
docker compose -f docker/docker-compose.yml up --build -d

# 3) Status pruefen
docker compose -f docker/docker-compose.yml ps
```

Danach erreichbar:
- Frontend: http://localhost:8080
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Was automatisch passiert

1. `beetle-db` startet und fuehrt beim ersten Start aus:
- `backend/SQL/DatabseShema.sql`
- `backend/SQL/AddMapQueryIndexes.sql`

2. `beetle-backend` wartet aktiv auf die DB-Port-Erreichbarkeit.

3. Erst danach startet Uvicorn mit `Database.backend.DB.main:app`.

## Konfiguration (optional)

Die wichtigsten Variablen koennen ueber Environment gesetzt werden:

- `DB_PASSWORD` (Standard: `root123`)
- `DB_NAME` (Standard: `beetle_db`)
- `API_BASE_URL` fuer das Frontend (Standard: `http://localhost:8080`)
- `ENABLE_SLOW_QUERY_LOGGING` (Standard: `true`)
- `SLOW_QUERY_MS` (Standard: `300`)

Beispiel (PowerShell):

```powershell
$env:DB_PASSWORD="root123"
$env:SLOW_QUERY_MS="250"
docker compose -f Database/docker/docker-compose.yml up --build -d
```

## Logs / Checks

```bash
docker compose -f docker/docker-compose.yml logs -f beetle-db
docker compose -f docker/docker-compose.yml logs -f beetle-backend
```

```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats/overview
```

## Stoppen

```bash
docker compose -f docker/docker-compose.yml down
```

Mit Loeschen der DB-Daten (nur wenn wirklich gewollt):

```bash
docker compose -f docker/docker-compose.yml down -v
```

## WSL-Fallback bei kaputtem Bridge-Netz

Wenn Docker unter WSL mit `failed to register "bridge" driver` oder `iptables ... nat table does not exist` startet, kann der Stack temporaer ohne Bridge-Netz betrieben werden.

### 1) Daemon in den Fallback-Modus setzen

```bash
sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
	"iptables": false,
	"ip6tables": false,
	"bridge": "none",
	"ip-forward": false,
	"ip-masq": false
}
EOF

sudo systemctl daemon-reload
sudo systemctl reset-failed docker
sudo systemctl restart docker
docker network ls
```

Erwartung: nur `host` und `none` sind sichtbar.

### 2) DB + Backend im Host-Network starten

```bash
cd Database
docker compose -f Docker/docker-compose.hostnet-only.yml up -d --build beetle-db beetle-backend
docker compose -f Docker/docker-compose.hostnet-only.yml ps
curl http://127.0.0.1:8000/health
```

Hinweis: In diesem Modus wird nur DB + Backend ueber Host-Network gefahren.

### 3) Fallback wieder entfernen (wenn WSL-Netz gefixt ist)

```bash
sudo rm -f /etc/docker/daemon.json
sudo systemctl daemon-reload
sudo systemctl reset-failed docker
sudo systemctl restart docker
```

Danach wieder normal starten:

```bash
cd Database
docker compose -f Docker/docker-compose.yml up --build -d
```

## Optional: CSV-Import manuell

CSV-Imports (`LoadGBIFCSVToDB.sql`, `LoadClimateSnapshot.sql`) sind absichtlich **nicht** im Auto-Init,
damit der Start robust bleibt, auch wenn CSV-Dateien nicht gemountet sind.

Diese Imports bei Bedarf manuell ausfuehren, nachdem der Stack laeuft.

## Team-Migrationen (verbindlich)

Ab Sprint 6.5 laufen nachtraegliche Schema-Aenderungen ueber versionierte Migrationen mit Registry-Tabelle.

- Registry-Tabelle: `schema_migrations`
- Initiale Registry-Definition: `Backend/SQL/MigrateSchemaMigrations.sql`
- Runner-Skript: `Backend/SQL/run_migrations.sh`

### Ausfuehren (WSL/Linux)

```bash
cd Database/Backend/SQL
chmod +x run_migrations.sh
./run_migrations.sh
```

Standardparameter des Runners:
- Container: `beetle-db`
- DB: `beetle_db`
- User: `root`

Optional ueberschreiben:

```bash
DB_CONTAINER=beetle-db DB_NAME=beetle_db DB_USER=root DB_PASSWORD=root123 ./run_migrations.sh
```

### Enthaltene Migrationen (Sprint 6.5)

1. `MigrateObservationEventDateParsed.sql`
2. `MigrateMediaGbifMediaIdIndex.sql`
3. `MigrateQualityReportHistory.sql`
4. `MigrateDataValidationChecks.sql`
5. `MigrateClimateValidationNormalization.sql`

Die Migration `MigrateDataValidationChecks.sql` fuegt nur dann CHECK-Constraints hinzu,
wenn keine widerspruechlichen Bestandsdaten vorhanden sind (guarded apply).
