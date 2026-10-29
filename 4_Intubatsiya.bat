@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - Intubatsiya Simulyatori

echo ====================================================================
echo   🫁 MEDLIFE: 4. TRAXEYA INTUBATSIYASI SIMULYATORI (SENSORLI)
echo ====================================================================
echo.

netstat -ano | findstr :8700 > nul
if %errorlevel% neq 0 (
    echo Intubatsiya serveri ishga tushirilmoqda...
    start /b python intubation_simulator.py > nul 2>&1
    timeout /t 2 /nobreak > nul
)

echo Intubatsiya ilovasi ochilmoqda...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8700 --start-fullscreen
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8700 --start-fullscreen
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8700 --start-fullscreen
) else (
    start http://localhost:8700
)
exit
