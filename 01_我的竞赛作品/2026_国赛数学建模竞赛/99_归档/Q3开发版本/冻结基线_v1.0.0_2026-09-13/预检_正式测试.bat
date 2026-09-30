@echo off
REM ===========================================================================
REM  Q3 formal-test PRE-FLIGHT (GO / NO-GO).  Run this BEFORE every formal test.
REM
REM  Checks: simulator reachable / no stray MATLAB / MATLAB exe / delivery tree
REM  matches the frozen baseline / no team-ID leak in source / logs writable /
REM  time budget vs the 17:30 deadline.
REM
REM  All logic lives in Python (_preflight_q3.py) on purpose: a .bat carrying
REM  UTF-8 Chinese gets mis-parsed by cmd.exe on a cp936 console.
REM ===========================================================================
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Q3 formal test - PRE-FLIGHT
echo ============================================================
echo.
echo  Team ID is used ONLY to scan the delivery source for a leaked ID.
echo  It is not written anywhere. Press Enter to skip that scan.
echo.
set TEAMID=
set /p TEAMID=Team ID (or Enter to skip):

set ARGS=
if not "%TEAMID%"=="" set ARGS=--team-id %TEAMID%

py -3.11 "%~dp0_preflight_q3.py" %ARGS%
set RC=%ERRORLEVEL%

echo.
echo ============================================================
if "%RC%"=="0" echo  [GO]     all checks passed - exit code 0
if not "%RC%"=="0" echo  [NO-GO]  fix the FAIL items above - exit code %RC%
echo ============================================================
echo.
pause
exit /b %RC%
