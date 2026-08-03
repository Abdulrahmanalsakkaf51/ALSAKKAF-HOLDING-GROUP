# Starts the ALSAKKAF SCALPING demo-automation dashboard (TRL-R2-013 hotfix).
#
# This launcher NEVER enables DEMO_AUTO automatically -- ALSAKKAF SCALPING's
# product state and the operating mode always start this session as
# RESEARCH / ANALYZE_ONLY at most (never DEMO_AUTO). Starting DEMO_AUTO is a
# separate, explicit, local-operator dashboard/CLI action, permanently
# disabled in the dashboard itself pending a separately governed broker
# execution proof (contract Section 9).
#
# TRL-R2-013 correction: the R2-012 version of this script never requested
# any ModeService/product-state transition at all, so the dashboard always
# opened with operating mode OFF and product state OFF (the Founder's
# reported operational failure). This version requests RESEARCH, then
# ANALYZE_ONLY, through the existing governed CLI before starting the
# server, and reports the real MT5 terminal/account state truthfully.
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
$mt5Importable = ($LASTEXITCODE -eq 0)
if (-not $mt5Importable) {
    Write-Warning "The MetaTrader5 Python package is not importable. ALSAKKAF SCALPING will start with the demo-account safety gate BLOCKED (SCALPING_MT5_DEPENDENCY_MISSING) until it is installed and the terminal is running."
}

# TRL-R2-013 Section 4: a real, bounded, read-only recheck BEFORE requesting
# any mode/state transition, so the printed lines below are always true --
# never a stale "OK" derived from journal health or a hopeful assumption.
$terminalConnected = $false
$demoVerified = $false
if ($mt5Importable) {
    Write-Host "Checking local MT5 terminal connectivity (read-only: initialize/terminal_info/account_info/shutdown only)..."
    $recheckJson = & python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-recheck 2>$null
    if ($LASTEXITCODE -eq 0 -and $recheckJson) {
        try {
            $recheck = $recheckJson | ConvertFrom-Json
            $terminalConnected = [bool]$recheck.terminal.connected
            $demoVerified = [bool]$recheck.mt5_connected
        } catch {
            Write-Warning "Could not parse the scalping-recheck output; treating MT5 as not connected."
        }
    } else {
        Write-Warning "scalping-recheck did not complete; treating MT5 as not connected."
    }
}
Write-Host ("MT5 TERMINAL CONNECTED: {0}" -f ($(if ($terminalConnected) { "YES" } else { "NO" })))
Write-Host ("MT5 DEMO ACCOUNT VERIFIED: {0}" -f ($(if ($demoVerified) { "YES" } else { "NO" })))

# TRL-R2-013 Section 4: request RESEARCH, then ANALYZE_ONLY, through the
# existing governed ModeService/ScalpingService CLI -- never DEMO_AUTO.
# This is the exact root-cause fix: the R2-012 launcher never did this, so
# operating mode and product state always resolved to whatever was last
# persisted (typically OFF/OFF on a clean profile).
Write-Host "Requesting operating mode RESEARCH (governed ModeService transition)..."
python -B -W error -m trading_lab_app.mode_cli request-mode RESEARCH --reason "ALSAKKAF SCALPING R2-013 safe launch" | Out-Null
$researchRequested = ($LASTEXITCODE -eq 0)
if (-not $researchRequested) {
    Write-Warning "RESEARCH mode request was not accepted (it may already be RESEARCH, or a later mode). Continuing -- the dashboard will show the true resolved mode."
}

# TRL-R2-013 Founder shutdown correction, Section 4: recover a stale,
# latched EMERGENCY_STOP left over from a prior session BEFORE requesting
# ANALYZE_ONLY. Only acts when owned broker state is zero; fails closed
# (nothing reset, ANALYZE_ONLY not requested) and prints an explicit
# blocker otherwise -- never silently ignored.
Write-Host "Checking for a stale EMERGENCY_STOP latch from a prior session..."
$recoverJson = & python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-startup-recover 2>$null
$recoverAccepted = ($LASTEXITCODE -eq 0)
if ($recoverAccepted -and $recoverJson) {
    try {
        $recover = $recoverJson | ConvertFrom-Json
        if ($recover.outcome -eq "RECOVERED") {
            Write-Host "A stale EMERGENCY_STOP latch (zero owned orders/positions) was safely reset to OFF."
        }
    } catch {
        Write-Warning "Could not parse scalping-startup-recover output."
    }
} elseif (-not $recoverAccepted) {
    Write-Warning "BLOCKER: ALSAKKAF SCALPING is latched at EMERGENCY_STOP with owned broker state that could not be confirmed zero. ANALYZE_ONLY will NOT be requested. Run scalping-list-owned-orders / scalping-list-owned-positions and scalping-reconcile, resolve manually, then re-run this script."
}

if ($recoverAccepted) {
    Write-Host "Requesting ALSAKKAF SCALPING product state ANALYZE_ONLY (governed ScalpingService transition)..."
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-resume | Out-Null
    $analyzeOnlyRequested = ($LASTEXITCODE -eq 0)
    if (-not $analyzeOnlyRequested) {
        Write-Warning "ANALYZE_ONLY was not accepted (it may already be ANALYZE_ONLY/DEMO_AUTO/PAUSED). Continuing -- the dashboard will show the true resolved product state."
    }
} else {
    $analyzeOnlyRequested = $false
}

Write-Host "----------------------------------------------------------------"
Write-Host "OPERATING MODE REQUESTED: RESEARCH"
Write-Host ("PRODUCT STATE REQUESTED: {0}" -f ($(if ($analyzeOnlyRequested) { "ANALYZE_ONLY" } else { "NOT REQUESTED -- see blocker/warning above; check scalping-status" })))
Write-Host "BROKER EXECUTION: PROHIBITED (no order_check, no order_send, DEMO_AUTO not entered)"
Write-Host "LIVE MONEY: LOCKED (MT5 demo account only, hard-locked out of this checkpoint)"
Write-Host "----------------------------------------------------------------"
Write-Host "Starting ALSAKKAF SCALPING dashboard on 127.0.0.1:${Port}..."

$pythonArgs = @("-B", "-W", "error", $appDirectory, "--port", $Port, "--open-fragment", "alsakkaf-scalping")
if ($NoBrowser) { $pythonArgs += "--no-browser" }
python @pythonArgs
exit $LASTEXITCODE
