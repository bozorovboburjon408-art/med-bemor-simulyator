@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ===================================================
echo   BEMOR MANIKEN SIMULYATORI (WEB ILOVA)
echo ===================================================
echo.
echo Server ishga tushmoqda...
start http://localhost:8000
python web_app.py
pause
