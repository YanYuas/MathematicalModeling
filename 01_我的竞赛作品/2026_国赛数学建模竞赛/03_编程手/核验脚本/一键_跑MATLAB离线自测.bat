@echo off
REM ===========================================================================
REM  Offline self-test for SimulatorClient (logging + dual check + retry rules)
REM  No real simulator needed: 5 mock servers are started on ports 20259-20263,
REM  one MATLAB session runs all 5 modes. PURE ASCII ON PURPOSE (see note in
REM  the Q3 launcher .bat in MATLAB_Framework about cmd.exe + cp936 + UTF-8).
REM ===========================================================================
cd /d "%~dp0"

echo ============================================================
echo  SimulatorClient offline self-test
echo  5 modes: ok / accepted_false / http400 / http409 / hang
echo ============================================================
echo.
echo  Interpreter: py -3.11   (Python 3.13 on this box lacks requests/numpy)
echo.

py -3.11 _run_client_selftest.py > _selftest_result.txt 2>&1
set RC=%ERRORLEVEL%

echo  Full output: _selftest_result.txt
echo.
type _selftest_result.txt

echo.
echo ============================================================
if "%RC%"=="0" echo  [OK]   all 5 modes passed - exit code 0
if not "%RC%"=="0" echo  [FAIL] self-test failed - exit code %RC%
echo ============================================================
echo.
pause
exit /b %RC%
