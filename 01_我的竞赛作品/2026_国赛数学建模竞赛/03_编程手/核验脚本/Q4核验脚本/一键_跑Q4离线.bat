@echo off
REM ---------------------------------------------------------------------------
REM  Q4 OFFLINE batch run on the mini Q4 simulator (directional physics).
REM  No real simulator, no network, NO drill/formal quota used.
REM  PURE ASCII ON PURPOSE: cmd.exe on a cp936 console mis-parses a .bat that
REM  contains UTF-8 Chinese (it splits the line and runs the tail as a command).
REM  Chinese runbook: see the .md files in this folder.
REM ---------------------------------------------------------------------------
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================================
echo  Q4 offline batch  (mini Q4 simulator)
echo ============================================================
echo   1 = standard random   (3 seeds, all directional, R_eff random)
echo   2 = worst case        (boundary + outward, R_eff = 1000)   [assertion 5]
echo   3 = Q3 subset check   (0 percent directional, degenerate run)
echo   4 = custom seeds
echo.
set MODE=
set /p MODE=Choose 1-4 (Enter = 1):
if "%MODE%"=="" set MODE=1
set ARGS=--seeds 2026,7,99 --n 13

if "%MODE%"=="1" goto :run
if "%MODE%"=="2" goto :mode2
if "%MODE%"=="3" goto :mode3
if "%MODE%"=="4" goto :mode4
echo  unknown choice "%MODE%" - using 1.
goto :run

:mode2
set ARGS=--seeds 2026,7,99 --n 13 --pos extreme --r-eff 1000
goto :run

:mode3
set ARGS=--seeds 2026,7,99 --n 13 --dir-frac 0
goto :run

:mode4
set SEEDS=
set /p SEEDS=Seeds (comma separated, e.g. 2026,7,99):
if "%SEEDS%"=="" set SEEDS=2026,7,99
set ARGS=--seeds %SEEDS% --n 13
goto :run

:run
echo.
echo  running: py -3.11 _run_mini_sim_q4.py %ARGS%
echo  (MATLAB starts once and runs every seed in ONE session; ~4-8 min)
echo.
py -3.11 _run_mini_sim_q4.py %ARGS%
set RC=%ERRORLEVEL%

echo.
echo ============================================================
if "%RC%"=="0" echo  [OK]   exit code 0
if not "%RC%"=="0" echo  [FAIL] exit code %RC%
echo  Report : _mini_sim_q4_result.txt   (UTF-8)
echo  Per-run: _q4_offline_runs.csv      (Excel friendly, UTF-8 BOM)
echo  Raw    : MATLAB_Framework_v2.0\logs\run_summary_Q4_*.json
echo ============================================================
echo.
pause
exit /b %RC%
