@echo off
pushd "%~dp0"
py -3 GUI.py 2>nul
if %errorlevel% equ 0 exit /b 0
python GUI.py
if errorlevel 1 pause
popd
