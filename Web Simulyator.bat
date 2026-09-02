@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - AI Bemor Simulyatori
echo ===================================================
echo   🏥 MEDLIFE: AI BEMOR SIMULYATORI
echo ===================================================
echo.
echo Server ishga tushmoqda...
start http://localhost:8000
python web_app.py
pause
