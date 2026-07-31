# Reports whether the Trading Lab dashboard is running and, if so, its
# health, version, and paper-engine mode (disabled / enabled / synthetic
# demonstration). Read-only; makes no mutation call.
#
# Usage:
#   .\GET_TRADING_LAB_STATUS.ps1
#   .\GET_TRADING_LAB_STATUS.ps1 -Port 8876

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "Trading Lab: NOT RUNNING (no listener on 127.0.0.1:$Port)"
    exit 0
}

Write-Host "Trading Lab: LISTENING on 127.0.0.1:$Port"

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 5
    Write-Host ("Application: {0} {1}" -f $health.application, $health.version)
} catch {
    Write-Warning "Listener is up but /api/health did not respond: $($_.Exception.Message)"
    exit 0
}

try {
    $account = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/paper-account" -TimeoutSec 5
    if (-not $account.enabled) {
        Write-Host "Paper engine: DISABLED"
    } elseif ($account.synthetic_demonstration_values) {
        Write-Host "Paper engine: SYNTHETIC DEMONSTRATION MODE (not live market data)"
    } else {
        Write-Host "Paper engine: ENABLED (local research timeline)"
    }
    if ($account.enabled) {
        Write-Host ("  Open positions: {0}  Completed trades: {1}  Risk halt: {2}" -f `
            $account.open_position_count, $account.completed_paper_trade_count, $account.risk_halt)
    }
} catch {
    Write-Warning "Could not read /api/paper-account: $($_.Exception.Message)"
}
