@echo off
setlocal EnableDelayedExpansion
title Converting to ProRes
rem Double-click to convert every .mp4 in the "masters" folder (next to this file)
rem to ProRes 422 HQ in a new "prores" folder. Finished files are skipped on re-runs.
cd /d "%~dp0"

if not exist "masters\" (
  echo.
  echo Could not find a "masters" folder next to this file.
  echo Move MAKE_PRORES.bat into the folder that contains "masters", then double-click it again.
  echo.
  pause
  exit /b 1
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo.
  echo ffmpeg is not installed, or Windows has not picked it up yet.
  echo Open PowerShell, paste this line and press Enter:
  echo     winget install --id Gyan.FFmpeg -e
  echo Then close all windows and double-click this file again.
  echo.
  pause
  exit /b 1
)

set "ROOT=%CD%"
set /a N=0
set /a FAILED=0
echo.
echo Converting every video in "masters" to ProRes 422 HQ. This can take a while.
echo.

for /r "%ROOT%\masters" %%F in (*.mp4) do (
  set "SRC=%%~fF"
  set "REL=!SRC:%ROOT%\masters\=!"
  set "OUT=%ROOT%\prores\!REL:~0,-4!_PRORES.mov"
  set "PART=%ROOT%\prores\!REL:~0,-4!_PRORES.partial.mov"
  set /a N+=1
  if exist "!OUT!" (
    echo [!N!] already done: !REL!
  ) else (
    for %%D in ("!OUT!") do if not exist "%%~dpD" mkdir "%%~dpD"
    echo [!N!] converting: !REL!
    ffmpeg -hide_banner -loglevel error -stats -nostdin -y -i "!SRC!" -c:v prores_ks -profile:v 3 -vendor apl0 -pix_fmt yuv422p10le -an "!PART!"
    if errorlevel 1 (
      echo     FAILED: !REL!
      set /a FAILED+=1
      if exist "!PART!" del "!PART!"
    ) else (
      move /y "!PART!" "!OUT!" >nul
    )
  )
)

echo.
if !FAILED! EQU 0 (
  echo All done. Your ProRes files are in: "%ROOT%\prores"
) else (
  echo Finished, but !FAILED! file^(s^) failed. Double-click again to retry them.
)
echo.
pause
