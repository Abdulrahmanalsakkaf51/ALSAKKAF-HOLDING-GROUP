# Stops the ALSAKKAF SCALPING demo-automation dashboard (TRL-R2-012).
#
# Requests a governed pause first (falling back to emergency stop if pause
# is rejected, e.g. because DEMO_AUTO is already active), then stops only
# the confirmed owned local process, leaves no lock file, and exposes no
# credential. Refuses to stop a process it cannot confirm is the Trading
# Lab, mirroring STOP_TRADING_LAB.ps1 exactly.
#
# Usage:
#   .\Stop_ALSAKKAF_SCALPING_DEMO.ps1
#   .\Stop_ALSAKKAF_SCALPING_DEMO.ps1 -Port 8876

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$appDirectory = Join-Path $PSScriptRoot "trading_lab_app"

Write-Host "Requesting a governed pause..."
python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-pause 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Pause was not accepted (product state may already be OFF/PAUSED). Requesting emergency stop as a fallback..."
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-emergency-stop 2>$null | Out-Null
}

$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "No listener found on 127.0.0.1:$Port. Nothing to stop."
    exit 0
}

$stoppedAny = $false
foreach ($connection in $connections) {
    $targetProcessId = $connection.OwningProcess
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $targetProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Write-Warning "Could not inspect process $targetProcessId owning port $Port. Skipping."
        continue
    }
    if ($process.CommandLine -notmatch "trading_lab_app") {
        Write-Warning ("Process {0} on port {1} does not look like the Trading Lab (command line: {2}). Skipping to avoid stopping an unrelated process." -f $targetProcessId, $Port, $process.CommandLine)
        continue
    }
    Write-Host ("Stopping ALSAKKAF SCALPING dashboard process {0} ({1}) on port {2}..." -f $targetProcessId, $process.Name, $Port)
    Stop-Process -Id $targetProcessId -Force -Confirm:$false
    $stoppedAny = $true
}

if ($stoppedAny) {
    Write-Host "ALSAKKAF SCALPING dashboard stopped."
} else {
    Write-Warning "A listener exists on port $Port but no process could be confirmed as the Trading Lab. Nothing was stopped."
    exit 1
}
