# Starts the ALSAKKAF Trading Lab dashboard with the forward paper engine
# DISABLED (the default). No paper storage is constructed and no paper
# network or filesystem operation occurs. PAPER ONLY remains visible.
#
# Usage:
#   .\START_TRADING_LAB_DISABLED.ps1
#   .\START_TRADING_LAB_DISABLED.ps1 -Port 8876 -NoBrowser

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

$pythonArgs = @("-B", "-W", "error", $appDirectory, "--port", $Port)
if ($NoBrowser) { $pythonArgs += "--no-browser" }

Write-Host "Starting ALSAKKAF Trading Lab (forward paper engine DISABLED) on 127.0.0.1:$Port ..."
python @pythonArgs
exit $LASTEXITCODE
