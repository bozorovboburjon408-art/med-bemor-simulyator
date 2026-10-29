@echo off
cd /d "%~dp0"
echo ========================================================
echo   RENDER VA GITHUBGA YUBORISH
echo ========================================================
echo.
git add web_app.py Render_Yangilash.bat ai_bemor_pulse_bridge.py
git commit -m "Fix: Instant disease loading and bulletproof WebSerial pulse" 2>nul
echo.
echo GitHub va Render bulutiga yuborilmoqda...
git push origin main
echo.
echo ========================================================
echo   Muvaffaqiyatli yuklandi! Render 1-2 daqiqada yangilanadi.
echo ========================================================
pause
