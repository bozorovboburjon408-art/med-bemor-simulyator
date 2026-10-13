@echo off
chcp 65001 > nul
cd /d "%~dp0"
title CPR Reanimatsiya (30:2) va Vital Monitor Simulyatori

echo ====================================================================
echo   🫀 YURAK-O'PKA REANIMATSIYASI (CPR 30:2) VA VITAL MONITOR
echo ====================================================================
echo.

:: Server ishlayotganini tekshirish yoki ishga tushirish
netstat -ano | findstr :8000 > nul
if %errorlevel% neq 0 (
    echo Server ishga tushirilmoqda...
    start /b python web_app.py > nul 2>&1
    timeout /t 2 /nobreak > nul
)

echo CPR va Vital Monitor to'liq ekranda ochilmoqda...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8000/cpr --start-fullscreen
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8000/cpr --start-fullscreen
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8000/cpr --start-fullscreen
) else (
    start http://localhost:8000/cpr
)
exit
