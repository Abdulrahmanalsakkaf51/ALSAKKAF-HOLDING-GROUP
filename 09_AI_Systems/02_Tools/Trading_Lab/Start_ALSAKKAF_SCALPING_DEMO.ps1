# Starts the ALSAKKAF SCALPING demo-automation dashboard (TRL-R2-012).
#
# This launcher NEVER enables DEMO_AUTO automatically -- the ALSAKKAF
# SCALPING product state always starts OFF, and the operating mode always
# starts OFF, regardless of any prior session. Starting DEMO_AUTO is a
# separate, explicit, local-operator dashboard/CLI action taken only after
# every demo-account safety gate has been reviewed.
#
# Usage:
#   .\Start_ALSAKKAF_SCALPING_DEMO.ps1
#   .\Start_ALSAKKAF_SCALPING_DEMO.ps1 -Port 8876 -NoBrowser

param(
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$appDirectory = Join-Path $PSScriptRoot "trading_lab_app"
if (-not (Test-Path $appDirectory)) {
    Write-Error "Could not find trading_lab_app under $PSScriptRoot"
    exit 1
}

$existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Error "Port $Port already has a listener. Refusing to start a duplicate server. Run Stop_ALSAKKAF_SCALPING_DEMO.ps1 first, or pass -Port with a free port."
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Error "Python was not found on PATH. Install Python and re-run this script."
    exit 1
}

$mt5Check = & python -B -W error -c "import importlib.util; import sys; sys.exit(0 if importlib.util.find_spec('MetaTrader5') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "The MetaTrader5 Python package is not importable. ALSAKKAF SCALPING will start with the demo-account safety gate BLOCKED (SCALPING_MT5_DEPENDENCY_MISSING) until it is installed and the terminal is running."
} else {
    Write-Host "MetaTrader5 package import check: OK"
}

Write-Host "Starting ALSAKKAF SCALPING dashboard on 127.0.0.1:$Port (product state: OFF, operating mode: OFF)..."
Write-Host "DEMO ACCOUNT ONLY -- LIVE MONEY AUTOMATION IS HARD-LOCKED OUT -- NO CREDENTIAL IS EVER READ BY THIS SCRIPT"

$pythonArgs = @("-B", "-W", "error", $appDirectory, "--port", $Port)
if ($NoBrowser) { $pythonArgs += "--no-browser" }
python @pythonArgs
exit $LASTEXITCODE
