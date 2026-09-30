@echo off
REM ASCII-only on purpose: a .bat containing non-ASCII text gets mis-parsed by
REM cmd.exe on a cp936 console (it splits the echo line and runs the tail as a
REM command). All logic lives in pack_handover.py, which handles Unicode paths.
cd /d "%~dp0"
py -3.11 pack_handover.py
echo.
pause
