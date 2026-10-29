@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - ICU Vital Monitor & CPR

echo ====================================================================
echo   🫀 MEDLIFE: 2. ICU VITAL MONITOR & CPR REANIMATSIYA (SENSORLI)
echo ====================================================================
echo.

netstat -ano | findstr :8500 > nul
if %errorlevel% neq 0 (
    echo Vital Monitor serveri ishga tushirilmoqda...
    start /b python vital_monitor.py > nul 2>&1
    timeout /t 2 /nobreak > nul
)

echo Vital Monitor ilovasi ochilmoqda...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8500 --start-fullscreen
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8500 --start-fullscreen
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8500 --start-fullscreen
) else (
    start http://localhost:8500
)
exit
