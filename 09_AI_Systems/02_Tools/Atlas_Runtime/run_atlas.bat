@echo off
REM Atlas Runtime launcher (batch). Forwards all arguments to atlas.py.
REM Example: run_atlas.bat war-room

set SCRIPT_DIR=%~dp0
py "%SCRIPT_DIR%atlas.py" %*
