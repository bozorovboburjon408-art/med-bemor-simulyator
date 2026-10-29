@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - GitHub va Render Yangilash

echo ========================================================
echo   RENDER VA GITHUBGA YUBORISH (MEDLIFE ENGINE)
echo ========================================================
echo.
git add web_app.py vital_monitor.py static/sw.js Render_Yangilash.bat ai_bemor_pulse_bridge.py
git commit -m "Auto update: system sync and clean project files" 2>nul
echo.
echo GitHub va Render serveriga yuklanmoqda...
git push origin main
echo.
echo ========================================================
echo   Muvaffaqiyatli yuborildi!
echo   Render 1-2 daqiqada yangilanadi.
echo   Saytda klaviaturadan Ctrl + Shift + R bosing!
echo ========================================================
pause
