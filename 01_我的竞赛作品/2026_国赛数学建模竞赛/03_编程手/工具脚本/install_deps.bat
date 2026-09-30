@echo off
rem ===================================================================
rem  CUMCM2026 B  --  Python dependency installer
rem  Lives at:  <programmer workspace>\install_deps.bat
rem             (the folder that also contains Q1\ Q2\ Q3\ Q4\)
rem  Scope:     the WHOLE workspace. Run it ONCE.
rem
rem  WHAT IT DOES
rem    1. locates the Python interpreter (absolute path pinned, with a
rem       fallback to whatever `python` resolves to)
rem    2. reports which packages are already present
rem    3. installs the MISSING REQUIRED ones
rem         matplotlib  -- every figure script in Q1..Q4
rem         requests    -- HTTP client for the Q3/Q4 simulator
rem                        (POST + JSON to 127.0.0.1:2026; urllib also
rem                         works, requests is simply more convenient)
rem    4. verifies by importing everything the figure scripts use
rem    5. resolves the Q1 results folder and prints a ready-to-paste
rem       command that generates the Q1 figures
rem
rem  NETWORK
rem    Tries the Tsinghua PyPI mirror first (fast in CN); on failure it
rem    retries against the default PyPI index automatically.
rem
rem  WHY THIS FILE IS PURE ASCII
rem    A .bat containing non-ASCII text is parsed under the console
rem    codepage (GBK on a Chinese Windows) and gets garbled. This file
rem    therefore contains NO non-ASCII bytes at all: every path that
rem    needs to be displayed is derived at run time from %~dp0 or from a
rem    wildcard search, never typed into the file.
rem ===================================================================
setlocal DisableDelayedExpansion
title CUMCM2026-B dependency installer

set "ROOT=%~dp0"
set "PY=C:\Users\21722\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"

set "MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
set "TRUSTHOST=pypi.tuna.tsinghua.edu.cn"
set "REQUIRED=matplotlib requests"

rem --- resolve the Q1 results folder WITHOUT naming it (folder name is
rem --- non-ASCII, so it must never appear literally in this file)
set "Q1DIR="
for /d %%D in ("%ROOT%Q1\*") do set "Q1DIR=%%~fD"

echo.
echo ===================================================================
echo   [0/5] interpreter
echo ===================================================================
"%PY%" -c "import sys;print('  exe     :',sys.executable);print('  version :',sys.version.split()[0]);print('  platform:',sys.platform)"
if errorlevel 1 (
  echo.
  echo   [FATAL] the interpreter above is not runnable.
  echo           Edit the PY= line in this file to point at your python.exe.
  pause
  exit /b 1
)

echo.
echo ===================================================================
echo   [1/5] workspace root
echo ===================================================================
echo   %ROOT%
if defined Q1DIR echo   Q1 results folder resolved: %Q1DIR%

echo.
echo ===================================================================
echo   [2/5] current package state
echo ===================================================================
"%PY%" -c "import importlib.util as u;print('\n'.join('  %-12s %s'%(m,'present' if u.find_spec(m) else 'MISSING') for m in ['numpy','scipy','pandas','PIL','matplotlib','requests','networkx','shapely','tqdm']))"

echo.
echo ===================================================================
echo   [3/5] install required:  %REQUIRED%
echo ===================================================================
echo   mirror: %MIRROR%
echo.
"%PY%" -m pip install -i %MIRROR% --trusted-host %TRUSTHOST% --upgrade %REQUIRED%
if errorlevel 1 (
  echo.
  echo   [WARN] mirror failed -- retrying with the default PyPI index ...
  "%PY%" -m pip install --upgrade %REQUIRED%
)
if errorlevel 1 (
  echo.
  echo   [FAIL] installation failed.
  echo          Check network / proxy. To use another mirror manually:
  echo            python -m pip install -i ^<mirror-url^> %REQUIRED%
  pause
  exit /b 1
)

echo.
echo ===================================================================
echo   [4/5] verify -- import EVERYTHING the figure scripts use
echo ===================================================================
"%PY%" -c "import matplotlib, matplotlib.pyplot as plt; from matplotlib import gridspec, cm; from matplotlib.patches import Circle, Polygon, Wedge, Arc, FancyArrowPatch, Rectangle, ConnectionPatch; from matplotlib.collections import LineCollection, PatchCollection; from mpl_toolkits.axes_grid1 import make_axes_locatable; from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset; from mpl_toolkits.mplot3d import Axes3D; from mpl_toolkits.mplot3d.art3d import Poly3DCollection; import numpy, scipy, pandas, requests; from scipy import stats; from scipy.spatial import Voronoi; from scipy.stats import gaussian_kde; print('  matplotlib :', matplotlib.__version__); print('  numpy      :', numpy.__version__); print('  scipy      :', scipy.__version__); print('  pandas     :', pandas.__version__); print('  requests   :', requests.__version__); print('  ALL IMPORTS OK')"
if errorlevel 1 (
  echo.
  echo   [FAIL] import check failed -- read the traceback above.
  pause
  exit /b 1
)

echo.
echo ===================================================================
echo   [5/5] DONE -- now generate the Q1 figures
echo ===================================================================
echo.
echo   The figure scripts write to a RELATIVE path and therefore MUST be
echo   launched with the Q1 results folder as the working directory.
echo   Paste exactly this:
echo.
if defined Q1DIR (
  echo     cd /d "%Q1DIR%"
) else (
  echo     cd /d "%ROOT%Q1\"   ^(then enter the results subfolder^)
)
echo     "%PY%" q1_figures_final.py
echo.
echo   q1_figures_final.py is the recommended one (clean journal styling).
echo   All seven figure scripts now request a CJK font as the first
echo   fallback, so the Chinese labels in q1_figures.py render correctly
echo   too.
echo.
echo   OPTIONAL EXTRAS (NOT installed by default):
echo     "%PY%" -m pip install -i %MIRROR% --trusted-host %TRUSTHOST% networkx shapely seaborn
echo       networkx : graph / route ordering, useful for Q3-Q4 waypoints
echo       shapely  : robust 2D geometry primitives
echo       seaborn  : statistical plots layered on matplotlib
echo.
pause
exit /b 0
