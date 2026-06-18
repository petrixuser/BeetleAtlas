param(
    [string]$ProjectRoot = "c:/Users/49173/Pictures/uni/Datenbanken/BeetleAtlas-main-new",
    [string]$PythonExe = "c:/Users/49173/Pictures/uni/Datenbanken/.venv/bin/python.exe",
    [string]$ResearcherSignupCode = "dev-researcher-code",
    [switch]$NoCacheBuild,
    [switch]$RecreateDb,
    [switch]$MinimalInit
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $ProjectRoot "scripts/run-auth-policy-tests.ps1"
$args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", $runner,
    "-ProjectRoot", $ProjectRoot,
    "-PythonExe", $PythonExe,
    "-ResearcherSignupCode", $ResearcherSignupCode,
    "-FullSuite"
)

if ($NoCacheBuild) { $args += "-NoCacheBuild" }
if ($RecreateDb) { $args += "-RecreateDb" }
if ($MinimalInit) { $args += "-MinimalInit" }

powershell @args
