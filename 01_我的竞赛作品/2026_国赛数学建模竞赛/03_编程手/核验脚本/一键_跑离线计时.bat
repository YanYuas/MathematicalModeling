@echo off
REM ---------------------------------------------------------------------------
REM  Offline TIMING via the mini-simulator (deterministic seeds).
REM  Reproduces physics + per-item virtual-time accounting, so algorithm changes
REM  can be compared WITHOUT spending any formal-test quota.
REM  PURE ASCII ON PURPOSE: cmd.exe on a cp936 console mis-parses a .bat that
REM  contains UTF-8 Chinese (it splits the line and runs the tail as a command).
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

echo ============================================================
echo  Q3 offline timing  (mini-simulator, seeds 2026 / 7 / 99)
echo  Expect: ~349.5 s per source, clear ratio 100%%
echo ============================================================
echo.

py -3.11 _run_mini_sim.py --seeds 2026,7,99
set RC=%ERRORLEVEL%
echo.
echo  Report: _mini_sim_result.txt  (UTF-8)
echo.
pause
exit /b %RC%
