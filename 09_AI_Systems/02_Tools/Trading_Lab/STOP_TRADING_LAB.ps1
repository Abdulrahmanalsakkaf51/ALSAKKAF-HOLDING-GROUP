# Stops only the Trading Lab listener/process on the local loopback port.
# Refuses to stop a process it cannot confirm is the Trading Lab, to avoid
# terminating an unrelated process that happens to hold the same port.
#
# Usage:
#   .\STOP_TRADING_LAB.ps1
#   .\STOP_TRADING_LAB.ps1 -Port 8876

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "No Trading Lab listener found on 127.0.0.1:$Port. Nothing to stop."
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
    Write-Host ("Stopping Trading Lab process {0} ({1}) on port {2}..." -f $targetProcessId, $process.Name, $Port)
    Stop-Process -Id $targetProcessId -Force -Confirm:$false
    $stoppedAny = $true
}

if ($stoppedAny) {
    Write-Host "Trading Lab stopped."
} else {
    Write-Warning "A listener exists on port $Port but no process could be confirmed as the Trading Lab. Nothing was stopped."
    exit 1
}
