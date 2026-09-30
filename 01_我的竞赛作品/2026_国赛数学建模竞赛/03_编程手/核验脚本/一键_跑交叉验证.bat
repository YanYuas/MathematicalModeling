@echo off
REM ---------------------------------------------------------------------------
REM  Q1 geometry CROSS-IMPLEMENTATION check:
REM    MATLAB  Q1_geometry.intersect_wedges  (polyshape boolean intersect)
REM    Python  q1_main.py                    (half-plane / ray intersection)
REM  Expect: 79 cases, 0 disagreements after domain clipping.
REM  PURE ASCII ON PURPOSE (see note in the other .bat files of this folder).
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

echo ============================================================
echo  Q1 geometry cross-implementation validation
echo ============================================================
echo.

py -3.11 _crossval_q1_geom.py
set RC=%ERRORLEVEL%
echo.
echo  Report: _crossval_report.txt  (UTF-8)
echo.
pause
exit /b %RC%
