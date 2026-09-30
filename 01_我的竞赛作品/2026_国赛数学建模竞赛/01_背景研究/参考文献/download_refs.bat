@echo off
rem ===================================================================
rem  CUMCM2026 B problem - background reference downloader  (v2)
rem
rem  Target folder = the folder this .bat sits in   (pushd "%~dp0")
rem
rem  Designed to survive the two failures seen in v1:
rem    (a) a transfer cut mid-stream that still exits 0  -> integrity
rem        check rejects it (PDF must contain "%%EOF")
rem    (b) a WAF rejecting a request and returning an HTML page
rem        -> same integrity check rejects it
rem
rem  This file is 100%% ASCII on purpose: Chinese inside a .bat breaks
rem  under the default GBK codepage. ASCII = no codepage/BOM issue.
rem
rem  Behaviour:
rem    - already-present valid file      -> SKIP (no re-download)
rem    - .part file from an earlier run  -> resumes with  curl -C -
rem    - download finishes but is corrupt-> deleted, counted as FAILED
rem    - run again to retry only what is missing/broken
rem ===================================================================
setlocal DisableDelayedExpansion
pushd "%~dp0"

set /a OK=0
set /a BAD=0
set /a SKIP=0

echo.
echo Target folder: %CD%
echo.

where curl >nul 2>nul || (echo [FATAL] curl.exe not found - Windows 10/11 ships it in System32. & popd & pause & exit /b 1)

call :GET "ITU-R-SM.854-3-2011.pdf"                     "https://www.itu.int/dms_pubrec/itu-r/rec/sm/R-REC-SM.854-3-201109-I!!PDF-E.pdf"
call :GET "Welzl-1991-Smallest-Enclosing-Disks.pdf"     "https://people.inf.ethz.ch/emo/PublFiles/SmallEnclDisk_LNCS555_91.pdf"
call :GET "Yang-2016-Sparse-Methods-for-DOA.pdf"        "https://arxiv.org/pdf/1609.09596v2"
call :GET "Chen-2024-GyroCopter-RF-Localization.pdf"    "https://arxiv.org/pdf/2410.13081v1"
call :GET "Masrur-2025-UAV-RF-Localization.pdf"         "https://arxiv.org/pdf/2502.13969v1"
call :GET "Jing-2020-MultiUAV-Coverage-Path.pdf"        "https://arxiv.org/pdf/2007.13065v1"
call :GET "Shahid-2024-UAV-Coverage-Exclusion-Zones.pdf" "https://arxiv.org/pdf/2411.07053v2"

echo.
echo ===================================================================
echo   DONE.   ok=%OK%   skipped=%SKIP%   failed=%BAD%
echo ===================================================================
echo.
echo Paywalled classics (not obtainable here - campus network / library):
echo   [3]  Stansfield 1947          doi:10.1049/ji-3a-2.1947.0096
echo   [4]  Gavish ^& Weiss 1992      doi:10.1109/7.256302
echo   [5]  Nardone et al. 1984      doi:10.1109/tac.1984.1103664
echo   [6]  Toussaint (OA journal!)  doi:10.17781/p001290
echo   [8]  Andrew 1979              doi:10.1016/0020-0190(79)90072-3
echo   [9]  Choset 2001              doi:10.1023/a:1016639210559
echo  [10]  Galceran ^& Carreras 2013 doi:10.1016/j.robot.2013.09.004
echo  [11]  Koopman 1956             doi:10.1287/opre.4.3.324
echo.
popd
pause
exit /b 0

rem -------------------------------------------------------------------
rem  :GET  %1 = output filename   %2 = URL
rem -------------------------------------------------------------------
:GET
if exist "%~1" (
  call :VERIFY "%~1"
  if not errorlevel 1 goto :SKIP
  echo [~] %~1  -- present but corrupt, re-downloading
  del "%~1" >nul 2>nul
) else (
  echo [ ] %~1
)

curl -L -f -s -S --retry 5 --retry-delay 5 -C - -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -o "%~1.part" "%~2"
if errorlevel 1 goto :FAIL

call :VERIFY "%~1.part"
if errorlevel 1 (
  echo     [FAIL] incomplete or not a PDF
  del "%~1.part" >nul 2>nul
  set /a BAD+=1
  exit /b 0
)

move /y "%~1.part" "%~1" >nul
echo     OK
set /a OK+=1
exit /b 0

:SKIP
echo [=] %~1  (valid, skipped)
set /a SKIP+=1
exit /b 0

:FAIL
echo     [FAIL] curl error - %~2
del "%~1.part" >nul 2>nul
set /a BAD+=1
exit /b 0

rem -------------------------------------------------------------------
rem  :VERIFY  %1 = file to check.  exit 0 = looks like a complete PDF.
rem  Rules: at least 1 KB, first byte is the percent sign (0x25), tail
rem  contains "EOF".  NOTE: the percent sign is compared as byte 37 on
rem  purpose - a lone percent sign inside a .bat gets eaten by the parser.
rem -------------------------------------------------------------------
:VERIFY
powershell -NoProfile -Command "$p='%~1'; try { $b=[IO.File]::ReadAllBytes($p) } catch { exit 1 }; if ($b.Length -lt 1024) { exit 1 }; if ($b[0] -ne 37) { exit 1 }; $n=[Math]::Min(64,$b.Length); $t=[Text.Encoding]::ASCII.GetString($b,($b.Length-$n),$n); if ($t -match 'EOF') { exit 0 } else { exit 1 }"
exit /b
