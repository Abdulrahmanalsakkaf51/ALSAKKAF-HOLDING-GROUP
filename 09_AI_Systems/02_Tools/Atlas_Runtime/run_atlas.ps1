# Atlas Runtime launcher (PowerShell)
# Forwards all arguments to atlas.py. Example: .\run_atlas.ps1 war-room

$ScriptDir = $PSScriptRoot
$AtlasPy = Join-Path $ScriptDir "atlas.py"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "Python launcher 'py' was not found. Install Python and ensure 'py' is on PATH." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $AtlasPy)) {
    Write-Host "atlas.py not found at $AtlasPy" -ForegroundColor Red
    exit 1
}

py $AtlasPy @args
