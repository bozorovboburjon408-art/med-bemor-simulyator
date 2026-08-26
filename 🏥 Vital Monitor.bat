@echo off
chcp 65001 > nul
cd /d "%~dp0"
title ICU Bemor Hayotiy Ko'rsatkichlari Monitori

echo ====================================================================
echo   🏥 ICU BEMOR HAYOTIY KO'RSATKICHLARI MONITORI SIMULYATORI
echo ====================================================================
echo.
echo Server ishga tushirilmoqda...
start http://localhost:8500
python vital_monitor.py
pause
