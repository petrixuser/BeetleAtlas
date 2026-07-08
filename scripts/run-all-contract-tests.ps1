# ============================================================================
#  Fuehrt die vollstaendige Auth-Policy-/Contract-Testsuite ueber den
#  Wrapper scripts/run-auth-policy-tests.ps1 aus (mit -FullSuite).
#  Parameter erlauben abweichenden Projektpfad, Python-Exe und Signup-Code
#  sowie optionalen Neuaufbau von Docker-Image und Datenbank.
#
#  Aufruf-Beispiel:
#    ./scripts/run-all-contract-tests.ps1 -RecreateDb
# ============================================================================
param(
    [string]$ProjectRoot = "c:/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new",
    [string]$PythonExe = "c:/Users/49173/Pictures/uni/Datenbanken/.venv/bin/python.exe",
    [string]$ResearcherSignupCode = "dev-researcher-code",
    [switch]$NoCacheBuild,
    [switch]$RecreateDb,
    [switch]$MinimalInit
)

$ErrorActionPreference = "Stop"

# Pfad zum eigentlichen Test-Runner-Skript zusammensetzen:
$runner = Join-Path $ProjectRoot "scripts/run-auth-policy-tests.ps1"
$args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", $runner,
    "-ProjectRoot", $ProjectRoot,
    "-PythonExe", $PythonExe,
    "-ResearcherSignupCode", $ResearcherSignupCode,
    "-FullSuite"
)

# Optionale Schalter nur bei Bedarf anhaengen:
if ($NoCacheBuild) { $args += "-NoCacheBuild" }
if ($RecreateDb) { $args += "-RecreateDb" }
if ($MinimalInit) { $args += "-MinimalInit" }

powershell @args
