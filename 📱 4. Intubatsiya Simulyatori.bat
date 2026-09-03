@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - Intubatsiya Maniken Moduli
echo ===================================================
echo   🩺 MEDLIFE: INTUBATSIYA MANIKEN MODULI
echo ===================================================
echo.
echo Web server tekshirilmoqda...
start http://localhost:8000/intubation
python web_app.py
pause
