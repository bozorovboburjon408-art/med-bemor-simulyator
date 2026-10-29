@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - O'qituvchi Boshqaruv Pulti

echo ====================================================================
echo   📱 MEDLIFE: 3. O'QITUVCHI BOSHQARUV PULTI (SENSORLI MONITOR)
echo ====================================================================
echo.

netstat -ano | findstr :8600 > nul
if %errorlevel% neq 0 (
    echo Maniken Pulti serveri ishga tushirilmoqda...
    start /b python manikin_console.py > nul 2>&1
    timeout /t 2 /nobreak > nul
)

echo Maniken Pulti ochilmoqda...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8600 --start-fullscreen
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8600 --start-fullscreen
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8600 --start-fullscreen
) else (
    start http://localhost:8600
)
exit
