@echo off
REM ---------------------------------------------------------------------------
REM  Q3 SimulatorClient v1.3.1 - offline unit tests (no pytest, no download)
REM  This file is intentionally PURE ASCII: a .bat containing UTF-8 Chinese gets
REM  mis-parsed by cmd.exe on a cp936 console (it splits the echo line and tries
REM  to run the tail as a command). Keeping it ASCII makes it codepage-proof.
REM  Chinese explanation lives in README.md of this folder.
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

echo ============================================================
echo  Q3 SimulatorClient v1.3.1 - offline unit tests
echo  (no pytest needed / no download needed)
echo ============================================================
echo.
echo  Interpreter: py -3.11
echo  Reason: this machine has requests+numpy under Python 3.11.9.
echo          "py -3" resolves to Python 3.13 which LACKS them.
echo.

py -3.11 _run_offline_tests_no_pytest.py
set RC=%ERRORLEVEL%

echo.
echo ============================================================
if "%RC%"=="0" echo  [OK]   ALL PASSED - exit code 0
if "%RC%"=="1" echo  [FAIL] test failures - exit code 1
if "%RC%"=="2" echo  [ENV]  missing deps - exit code 2
echo  Report: _offline_tests_result.txt  (UTF-8)
echo ============================================================
echo.
pause
exit /b %RC%
