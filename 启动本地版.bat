@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (py start_local.py) else (python start_local.py)
pause
