<#
  RUN_ATLAS_COMMAND_CENTER.ps1

  Opens the Atlas War Room: runs Atlas Runtime's "war-room" command, which
  generates a combined brief + dashboard + payment-report + content-pack
  summary. This script does not send anything, publish anything, spend
  anything, or create any account. It only reads local repository files
  and writes local report files under 01_Holding_Company/08_Reports/Atlas_Output/.

  Usage: double-click this file, or run it from a PowerShell prompt.
#>

# This script lives at the repository root, so its own folder IS the repo root.
$repoRoot = $PSScriptRoot
Set-Location $repoRoot

Write-Host "AOS Atlas Command Center" -ForegroundColor Cyan
Write-Host "Repository: $repoRoot"
Write-Host ""

$pythonCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python was not found on this system (tried 'py' and 'python')." -ForegroundColor Red
    Write-Host "Install Python, or run Atlas Runtime manually once Python is available." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$atlasScript = Join-Path $repoRoot "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py"

if (-not (Test-Path $atlasScript)) {
    Write-Host "ERROR: Atlas Runtime was not found at:" -ForegroundColor Red
    Write-Host "  $atlasScript" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

& $pythonCmd.Name $atlasScript war-room

Write-Host ""
Write-Host "War room report generated in 01_Holding_Company\08_Reports\Atlas_Output\Atlas_War_Room_Report.md" -ForegroundColor Green
Read-Host "Press Enter to close"
