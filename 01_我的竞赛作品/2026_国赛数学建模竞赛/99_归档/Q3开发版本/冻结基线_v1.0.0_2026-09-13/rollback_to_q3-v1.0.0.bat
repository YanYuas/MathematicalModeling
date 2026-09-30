@echo off
REM ===========================================================================
REM  ROLLBACK: restore the Q3 delivery baseline MATLAB_Framework/ from the
REM  frozen snapshot this script lives in.
REM
REM  Frozen snapshot : the folder containing this .bat
REM  Git anchor      : git tag q3-v1.0.0  ->  commit 9b01124
REM
REM  Restores ONLY the 32 source/doc/launcher files - it never deletes logs\
REM  or the doc-history folder in the target.
REM
REM  PURE ASCII ON PURPOSE: cmd.exe on a cp936 console mis-parses a .bat that
REM  carries UTF-8 Chinese (it splits the line and runs the tail as a command).
REM  So the target is DISCOVERED, not hard-coded, and all real logic is Python.
REM ===========================================================================
setlocal
set "SNAPDIR=%~dp0."
set "DEST="

if not exist "%SNAPDIR%\MANIFEST.txt" (
  echo [FAIL] MANIFEST.txt not found next to this script: %SNAPDIR%
  pause
  exit /b 2
)

REM  Find the v1 folder by EXACT name - "MATLAB_Framework", not "..._v2.0".
for /d %%D in ("%SNAPDIR%\..\HelloMathModeling\*") do (
  if /i "%%~nxD"=="MATLAB_Framework" set "DEST=%%~fD"
)

if not defined DEST (
  echo [FAIL] could not locate HelloMathModeling\...\MATLAB_Framework
  echo        Expected a sibling tree: ..\HelloMathModeling\
  pause
  exit /b 2
)
if not exist "%DEST%\main_Q3Q4.m" (
  echo [FAIL] target does not look like MATLAB_Framework: %DEST%
  pause
  exit /b 2
)

echo ============================================================
echo  ROLLBACK   MATLAB_Framework   ^<-   frozen q3-v1.0.0 snapshot
echo ------------------------------------------------------------
echo  source : %SNAPDIR%
echo  target : %DEST%
echo ============================================================
echo.
echo  Overwrites the 32 tracked source/doc files in the target.
echo  Does NOT touch logs\ or the doc-history folder.
echo.
choice /c YN /m "Proceed with rollback"
if errorlevel 2 goto :cancelled

copy /y "%SNAPDIR%\*.m"   "%DEST%\" >nul
copy /y "%SNAPDIR%\*.md"  "%DEST%\" >nul
copy /y "%SNAPDIR%\*.bat" "%DEST%\" >nul

echo.
echo  Restored. Verifying snapshot integrity AND live drift...
echo.
py -3.11 "%SNAPDIR%\_verify_baseline.py" --live
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" echo  [OK]   rollback complete, live tree matches the frozen baseline.
if not "%RC%"=="0" echo  [FAIL] verification failed - exit code %RC%
echo.
echo  Next: re-run the offline MATLAB self-test (12 checks) from the
echo        verification-scripts folder to confirm the rollback is green.
echo.
pause
exit /b %RC%

:cancelled
echo  Cancelled. Nothing changed.
pause
exit /b 1
