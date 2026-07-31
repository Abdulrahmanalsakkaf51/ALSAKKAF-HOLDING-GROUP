# Starts the ALSAKKAF Trading Lab dashboard with the committed SYNTHETIC
# DEMONSTRATION fixture loaded into an in-memory paper engine. This is NOT
# live market data, never touches production paper storage, and makes no
# broker order or external network call.
#
# Usage:
#   .\START_TRADING_LAB_DEMO.ps1
#   .\START_TRADING_LAB_DEMO.ps1 -Port 8876 -NoBrowser

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

$pythonArgs = @("-B", "-W", "error", $appDirectory, "--port", $Port, "--enable-forward-paper-demo")
if ($NoBrowser) { $pythonArgs += "--no-browser" }

Write-Host "Starting ALSAKKAF Trading Lab (SYNTHETIC DEMONSTRATION MODE) on 127.0.0.1:$Port ..."
Write-Host "SYNTHETIC DEMONSTRATION -- NOT LIVE MARKET DATA -- NO BROKER ORDERS"
python @pythonArgs
exit $LASTEXITCODE
