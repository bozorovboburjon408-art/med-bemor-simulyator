@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - Maniken Boshqaruv Pulti (Sensorli Ekran)

echo ====================================================================
echo   🎛️ MEDLIFE: MANIKEN PULTI VA CPR IMTIHON (SENSORLI ILOVA)
echo ====================================================================
echo.

:: Server ishlayotganini tekshirish yoki ishga tushirish
netstat -ano | findstr :8000 > nul
if %errorlevel% neq 0 (
    echo Server ishga tushirilmoqda...
    start /b python web_app.py > nul 2>&1
    timeout /t 2 /nobreak > nul
)

echo Sensorli ekran ilovasi ochilmoqda...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8000/console --start-fullscreen
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8000/console --start-fullscreen
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8000/console --start-fullscreen
) else (
    start http://localhost:8000/console
)
exit
