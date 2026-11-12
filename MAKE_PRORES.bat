@echo off
rem Double-click to convert every video in "masters" to ProRes 422 HQ in a new "prores" folder.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\make_prores.ps1" %*
echo.
pause
