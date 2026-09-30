@echo off
REM ===========================================================================
REM  Q3 robot-dog program - one-click launcher (MATLAB main line)
REM  PURE ASCII ON PURPOSE: a .bat with UTF-8 Chinese gets mis-parsed by cmd.exe
REM  on a cp936 console (it splits the echo line and runs the tail as a command).
REM  Chinese runbook: see the .md runbook file in this same folder.
REM  Batch mode: answer the 'Number of CONSECUTIVE games' prompt with N>1 and it
REM  runs N games in ONE MATLAB session (main_batch_Q3Q4), waiting between games
REM  for you to click 'confirm start' in the simulator UI. N=1 = the old behaviour.
REM ===========================================================================
cd /d "%~dp0"
set HERE=%~dp0
set HERE=%HERE:~0,-1%

echo ============================================================
echo  CUMCM2026 B  Q4  robot-dog program
echo ============================================================
echo.
echo  Your team ID is REQUIRED - the simulator checks it byte-by-byte:
echo    "robot_id must equal the currently logged-in team ID" (App.2 sec.5.1)
echo  It is NOT stored in source (competition rule: hide the team ID).
echo.

set ROBOTID=
set /p ROBOTID=Enter your team ID (robot_id):
if "%ROBOTID%"=="" goto :notid

set CASECODE=
set /p CASECODE=Test case code from simulator UI (optional, Enter to skip):

set NGAMES=
set /p NGAMES=Number of CONSECUTIVE games (Enter = 1, e.g. 8 for a 320-target batch):
set /a NGAMES=%NGAMES%+0 2>nul
if "%NGAMES%"=="" set NGAMES=1
if "%NGAMES%"=="0" set NGAMES=1

echo.
echo  team ID : %ROBOTID%
echo  case    : %CASECODE%
echo  games   : %NGAMES%
if not "%NGAMES%"=="1" echo.
if not "%NGAMES%"=="1" echo  BATCH MODE: MATLAB stays alive between games. After each game,
if not "%NGAMES%"=="1" echo  click "confirm start test" in the simulator UI. The program WAITS
if not "%NGAMES%"=="1" echo  (up to 600 s) and enters as soon as the interface opens.
echo.
echo  NOTE: MATLAB takes ~40 s to start. Start this script BEFORE the
echo        simulator 5-second countdown ends, otherwise /enter will fail.
echo.

set MATLAB_EXE=D:\R2026a_Windows\bin\matlab.exe
if not exist "%MATLAB_EXE%" set MATLAB_EXE=D:\R2022b_Windows\bin\matlab.exe
if not exist "%MATLAB_EXE%" goto :nomatlab

echo  MATLAB  : %MATLAB_EXE%
echo  starting...
echo.

if "%NGAMES%"=="1" (
  "%MATLAB_EXE%" -nosplash -sd "%HERE%" -batch "main_Q3Q4('Q4','%ROBOTID%','%CASECODE%')"
) else (
  "%MATLAB_EXE%" -nosplash -sd "%HERE%" -batch "main_batch_Q3Q4('Q4','%ROBOTID%',%NGAMES%,[],[],600)"
)
set RC=%ERRORLEVEL%

echo.
echo ============================================================
if "%RC%"=="0" echo  [OK]   program finished, exit code 0
if not "%RC%"=="0" echo  [FAIL] program exit code %RC%
echo  Robot-side log: MATLAB_Framework\logs\robot_*.jsonl  (next to this file)
if not "%NGAMES%"=="1" echo  Batch summary : MATLAB_Framework\logs\batch_summary_*.txt
echo ============================================================
echo.
pause
exit /b %RC%

:notid
echo.
echo  [ERROR] team ID is required.
echo.
pause
exit /b 2

:nomatlab
echo.
echo  [ERROR] MATLAB not found at D:\R2026a_Windows or D:\R2022b_Windows.
echo          Edit MATLAB_EXE in this .bat.
echo.
pause
exit /b 2
