@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Shiguang local phone launcher - keep this window open.
if not exist "launch_web.py" goto missing_files
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys;raise SystemExit(sys.version_info[0] != 3)" >nul 2>nul
if errorlevel 1 goto try_python
py -3 launch_web.py
goto finished
:try_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -c "import sys;raise SystemExit(sys.version_info[0] != 3)" >nul 2>nul
if errorlevel 1 goto missing_python
python launch_web.py
goto finished
:missing_python
echo Python 3 was not found. Install Python 3 from python.org and try again.
echo Installation guide: https://zhusichen520.github.io/zhusichen520/help-ollama.html
goto finished
:missing_files
echo Missing launch_web.py. Right-click the ZIP and choose Extract All first.
:finished
echo.
echo The launcher has stopped. This window stays open so you can read any error.
echo If startup-errors.log exists, it contains the startup error, without passwords.
exit /b
