@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (py -3 start_local.py) else (python start_local.py)
echo.
echo 如果没有出现连接助手，请先安装 Python 3，并阅读本地版使用说明。
pause
