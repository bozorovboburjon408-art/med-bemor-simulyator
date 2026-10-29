@echo off
cd /d "%~dp0"
echo ========================================================
echo   RENDER VA GITHUBGA YUBORISH (V3 TO'LIQ TUZATILDI)
echo ========================================================
echo.
git add web_app.py static/sw.js Render_Yangilash.bat ai_bemor_pulse_bridge.py
git commit -m "Auto update: clean JS and ServiceWorker v3" 2>nul
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
