@echo off
REM ===========================================================================
REM  RESTORE the Q3 delivery tree to the frozen v1.1.0 snapshot.
REM
REM  Git anchors (both already pushed to origin):
REM    q3-v1.1.0 -> commit 70c7e4a   (this version)
REM    q3-v1.0.0 -> commit 9b01124   (previous version)
REM
REM  Two ways back, both fine:
REM    (a) this script  - no git needed, restores from the snapshot beside it
REM    (b) in the repo  - git checkout q3-v1.1.0 -- <the framework path>
REM                       (substitute q3-v1.0.0 for the previous version)
REM
REM  PURE ASCII ON PURPOSE: cmd.exe on a cp936 console mis-parses a .bat that
REM  carries UTF-8 Chinese. The target folder is DISCOVERED, never hard-coded.
REM ===========================================================================
setlocal
set "SNAPDIR=%~dp0."
set "DEST="

if not exist "%SNAPDIR%\MANIFEST.txt" (
  echo [FAIL] MANIFEST.txt not found next to this script: %SNAPDIR%
  pause
  exit /b 2
)

REM  Exact folder name match: "MATLAB_Framework", not the "_v2.0" one.
for /d %%D in ("%SNAPDIR%\..\HelloMathModeling\*") do (
  if /i "%%~nxD"=="MATLAB_Framework" set "DEST=%%~fD"
)
if not defined DEST (
  echo [FAIL] could not locate HelloMathModeling\...\MATLAB_Framework
  pause
  exit /b 2
)
if not exist "%DEST%\main_Q3Q4.m" (
  echo [FAIL] target does not look like MATLAB_Framework: %DEST%
  pause
  exit /b 2
)

echo ============================================================
echo  RESTORE   MATLAB_Framework   ^<-   Q3 v1.1.0 snapshot
echo ------------------------------------------------------------
echo  source : %SNAPDIR%
echo  target : %DEST%
echo ============================================================
echo.
choice /c YN /m "Proceed"
if errorlevel 2 goto :cancelled

copy /y "%SNAPDIR%\*.m"   "%DEST%\" >nul
copy /y "%SNAPDIR%\*.md"  "%DEST%\" >nul
copy /y "%SNAPDIR%\*.bat" "%DEST%\" >nul

echo.
echo  Restored. Verifying the snapshot against its own manifest...
py -3.11 "%SNAPDIR%\_verify_baseline.py"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" echo  [OK]  restored and verified.
if not "%RC%"=="0" echo  [FAIL] verification failed - exit code %RC%
pause
exit /b %RC%

:cancelled
echo  Cancelled. Nothing changed.
pause
exit /b 1
