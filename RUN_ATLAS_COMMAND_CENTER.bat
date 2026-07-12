@echo off
REM RUN_ATLAS_COMMAND_CENTER.bat
REM
REM Opens the Atlas War Room: runs Atlas Runtime's "war-room" command, which
REM generates a combined brief + dashboard + payment-report + content-pack
REM summary. This script does not send anything, publish anything, spend
REM anything, or create any account. It only reads local repository files
REM and writes local report files under 01_Holding_Company\08_Reports\Atlas_Output\.
REM
REM Usage: double-click this file.

cd /d "%~dp0"

echo AOS Atlas Command Center
echo Repository: %cd%
echo.

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" war-room
    goto done
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" war-room
    goto done
)

echo ERROR: Python was not found on this system (tried 'py' and 'python').
echo Install Python, or run Atlas Runtime manually once Python is available.
pause
exit /b 1

:done
echo.
echo War room report generated in 01_Holding_Company\08_Reports\Atlas_Output\Atlas_War_Room_Report.md
pause
