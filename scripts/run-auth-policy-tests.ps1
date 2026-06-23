param(
    [string]$ProjectRoot = "c:/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new",
    [string]$PythonExe = "c:/Users/49173/Pictures/uni/Datenbanken/.venv/bin/python.exe",
    [string]$ResearcherSignupCode = "dev-researcher-code",
    [switch]$NoCacheBuild,
    [switch]$RecreateDb,
    [switch]$MinimalInit,
    [switch]$FullSuite
)

$ErrorActionPreference = "Stop"

function Invoke-Wsl {
    param([string]$Command)
    wsl -d Ubuntu -- bash -lc $Command
}

Set-Location $ProjectRoot

$bridgeCountRaw = Invoke-Wsl "docker network ls --format '{{.Name}}' | grep -x bridge | wc -l"
$bridgeCount = [int]($bridgeCountRaw.Trim())

if ($bridgeCount -gt 0) {
    Write-Host "MODE=compose"
    Invoke-Wsl "cd /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new; docker compose -f docker-compose.dev.yml up -d beetle-db beetle-redis beetle-backend"
} else {
    Write-Host "MODE=host-fallback"
    Invoke-Wsl "docker rm -f beetle-backend beetle-db beetle-redis >/dev/null 2>&1 || true"

    if ($RecreateDb) {
        Invoke-Wsl "docker volume rm beetle_db_data >/dev/null 2>&1 || true"
    }

    if ($MinimalInit) {
        Invoke-Wsl "docker run -d --name beetle-db --network host -e MYSQL_ROOT_PASSWORD=root123 -e MYSQL_DATABASE=beetle_db -v beetle_db_data:/var/lib/mysql -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/schema/DatabseShema.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/ops/AddMapQueryIndexes.sql:/docker-entrypoint-initdb.d/02_indexes.sql:ro mysql:8.0 --default-authentication-plugin=mysql_native_password"
    } else {
        Invoke-Wsl "docker run -d --name beetle-db --network host -e MYSQL_ROOT_PASSWORD=root123 -e MYSQL_DATABASE=beetle_db -v beetle_db_data:/var/lib/mysql -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/schema/DatabseShema.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/ops/AddMapQueryIndexes.sql:/docker-entrypoint-initdb.d/02_indexes.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/seed/LoadGBIFCSVToDB.sql:/docker-entrypoint-initdb.d/03_seed_gbif.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/seed/LoadClimateSnapshot.sql:/docker-entrypoint-initdb.d/04_seed_climate.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/seed/RecordQualityReportSnapshot.sql:/docker-entrypoint-initdb.d/05_quality_snapshot.sql:ro -v /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/Data:/var/lib/mysql-files mysql:8.0 --default-authentication-plugin=mysql_native_password"
    }
    Invoke-Wsl "docker run -d --name beetle-redis --network host redis:7-alpine"

    if ($NoCacheBuild) {
        Invoke-Wsl "cd /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new; docker build --no-cache --network host -t beetle-backend-local -f backend/docker/Dockerfile ."
    } else {
        Invoke-Wsl "cd /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new; docker build --network host -t beetle-backend-local -f backend/docker/Dockerfile ."
    }

    Invoke-Wsl "docker run -d --name beetle-backend --network host -e DB_HOST=127.0.0.1 -e DB_PORT=3306 -e DB_USER=root -e DB_PASSWORD=root123 -e DB_NAME=beetle_db -e API_HOST=0.0.0.0 -e API_PORT=8000 -e API_APP_MODULE=backend.core.main:app -e FRONTEND_ORIGINS=http://localhost:8080 -e ALLOW_ADMIN_BOOTSTRAP=true -e ADMIN_BOOTSTRAP_TOKEN=dev-bootstrap-token -e RESEARCHER_SIGNUP_CODE=$ResearcherSignupCode -e JWT_SECRET=dev-jwt-secret -e JWT_ALGORITHM=HS256 -e JWT_ACCESS_TTL_MINUTES=30 -e JWT_REFRESH_TTL_DAYS=14 -e AUTH_REFRESH_MAX_REQUESTS=30 -e AUTH_REFRESH_WINDOW_SECONDS=60 -e REDIS_URL=redis://127.0.0.1:6379/0 beetle-backend-local"
}

$healthy = $false
for ($i = 0; $i -lt 180; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $healthy) {
    throw "Backend health check did not become ready on http://127.0.0.1:8000/health"
}

# Ensure auth tables exist in freshly initialized databases before contract tests.
Invoke-Wsl "docker exec -i beetle-db mysql -uroot -proot123 beetle_db < /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/schema/MigrateSchemaMigrations.sql"
Invoke-Wsl "docker exec -i beetle-db mysql -uroot -proot123 beetle_db < /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/ops/MigrateAuthAndManualBeetles.sql"
Invoke-Wsl "docker exec -i beetle-db mysql -uroot -proot123 beetle_db < /mnt/c/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new/backend/SQL/ops/MigrateAuthRefreshTokens.sql"

$env:API_RESEARCHER_SIGNUP_CODE = $ResearcherSignupCode
if ($FullSuite) {
    & $PythonExe -m pytest backend/tests/test_api_contract.py backend/tests/test_api_error_contract.py backend/tests/test_api_rbac_contract.py -q -vv
} else {
    & $PythonExe -m pytest backend/tests/test_api_error_contract.py -k "register_defaults_to_viewer_role_contract or researcher_register_requires_valid_signup_code_contract" -q -vv
}
