@echo off
REM ---------------------------------------------------------------------------
REM  Real-run log analysis (reads ../MATLAB_Framework/logs/robot_*.jsonl).
REM    1) time account: travel + measure + channel switch + clear  vs  virtual_time_s
REM       -> residual MUST be ~0 s, otherwise the cost model is wrong
REM    2) travel slack: actual path vs NN+2-opt tour over the same visited set
REM  NOTE: logs contain the REAL team ID - keep the report out of any submission.
REM  PURE ASCII ON PURPOSE (see note in the other .bat files of this folder).
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

echo ============================================================
echo  Real-run log analysis
echo ============================================================
echo.

py -3.11 _analyze_real_runs.py > _real_runs_analysis.txt 2>&1
set RC=%ERRORLEVEL%
type _real_runs_analysis.txt
echo.
echo  Report: _real_runs_analysis.txt  (UTF-8)
echo.
pause
exit /b %RC%
