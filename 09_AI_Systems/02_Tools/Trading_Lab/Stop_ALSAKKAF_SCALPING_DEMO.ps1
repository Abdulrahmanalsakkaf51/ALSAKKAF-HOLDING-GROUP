# Stops the ALSAKKAF SCALPING demo-automation dashboard (TRL-R2-013
# Founder shutdown correction).
#
# TRL-R2-013 correction (this pass): the prior version of this script
# always called scalping-pause first, then fell back to scalping-emergency-
# stop on any pause rejection. The R2-012 transition table never allows
# ANALYZE_ONLY -> PAUSED at all (PAUSED is reachable only from DEMO_AUTO/
# PAUSED itself), so pause deterministically failed from exactly the state
# the launcher establishes (ANALYZE_ONLY), and every ordinary shutdown
# latched an unnecessary EMERGENCY_STOP -- the Founder-observed defect.
# This version calls the new deterministic, state-aware, idempotent
# scalping-stop command (ScalpingService.graceful_stop()), which never
# uses EMERGENCY_STOP as a generic fallback and never attempts a bare
# EMERGENCY_STOP -> OFF transition (only the governed emergency-reset path
# may do that, and only when owned broker state is confirmed zero).
#
# Stops read-only monitoring, requests the deterministic product-state
# stop, requests operating mode OFF, stops only the confirmed owned local
# process, then verifies final OFF/OFF before reporting success -- never
# prints "stopped" on an unverified or partial shutdown. Leaves no lock
# file, exposes no credential. Refuses to stop a process it cannot confirm
# is the Trading Lab, mirroring STOP_TRADING_LAB.ps1 exactly. Never
# deletes the journal or saved configuration.
#
# Usage:
#   .\Stop_ALSAKKAF_SCALPING_DEMO.ps1
#   .\Stop_ALSAKKAF_SCALPING_DEMO.ps1 -Port 8876

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$appDirectory = Join-Path $PSScriptRoot "trading_lab_app"

Write-Host "Stopping read-only monitoring (if running)..."
python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-monitoring-stop 2>$null | Out-Null

Write-Host "Requesting a deterministic, state-aware ALSAKKAF SCALPING product-state stop..."
$stopJson = & python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-stop 2>$null
$stopAccepted = ($LASTEXITCODE -eq 0)
if ($stopAccepted -and $stopJson) {
    try {
        $stopResult = $stopJson | ConvertFrom-Json
        Write-Host ("Product-state stop outcome: {0} (product_state={1})" -f $stopResult.outcome, $stopResult.product_state)
    } catch {
        Write-Warning "Could not parse scalping-stop output."
    }
} else {
    Write-Warning "BLOCKER: scalping-stop was rejected -- ALSAKKAF SCALPING likely has owned broker state (pending orders/positions) that must be resolved manually (scalping-list-owned-orders / scalping-list-owned-positions / scalping-reconcile) before the product state can safely reach OFF. Continuing with operating-mode/process shutdown, but final verification below will reflect the true unresolved state."
}

Write-Host "Requesting operating mode OFF..."
python -B -W error -m trading_lab_app.mode_cli request-mode OFF --reason "ALSAKKAF SCALPING stop" 2>$null | Out-Null

$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
$processStopped = $true
if ($connections) {
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
    $processStopped = $stoppedAny
    if (-not $stoppedAny) {
        Write-Warning "A listener exists on port $Port but no process could be confirmed as the Trading Lab. Nothing was stopped."
    }
} else {
    Write-Host "No listener found on 127.0.0.1:$Port. Nothing to stop at the process level."
}

# TRL-R2-013 Section 3: verify final OFF/OFF before reporting success --
# never print the success line on a partial or unverified shutdown.
Write-Host "Verifying final state..."
$finalProductState = $null
$statusJson = & python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-status 2>$null
if ($LASTEXITCODE -eq 0 -and $statusJson) {
    try { $finalProductState = ($statusJson | ConvertFrom-Json).product_state } catch {}
}
$finalOperatingMode = $null
$modeJson = & python -B -W error -m trading_lab_app.mode_cli show-mode 2>$null
if ($LASTEXITCODE -eq 0 -and $modeJson) {
    try { $finalOperatingMode = ($modeJson | ConvertFrom-Json).current_mode } catch {}
}
Write-Host ("Final product state: {0}" -f $finalProductState)
Write-Host ("Final operating mode: {0}" -f $finalOperatingMode)

if ($finalProductState -eq "OFF" -and $finalOperatingMode -eq "OFF" -and $processStopped) {
    Write-Host "ALSAKKAF SCALPING dashboard stopped."
    exit 0
} else {
    Write-Warning "ALSAKKAF SCALPING did NOT reach a fully verified OFF/OFF shutdown. Review the warnings above (owned broker state, an unrecognized process, or a stale listener) before relaunching."
    exit 1
}
