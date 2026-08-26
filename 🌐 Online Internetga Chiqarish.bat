@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Bemor Maniken Simulyatori - Online Tunnel

echo ====================================================================
echo   🏥 BEMOR MANIKEN SIMULYATORI - ONLINE REJIM
echo ====================================================================
echo.
echo 1. Web server alohida fonda ishga tushirilmoqda...
start "Bemor Web Server" cmd /c "python web_app.py"
timeout /t 3 /nobreak > nul

echo 2. Dunyo bo'yicha kirish uchun xavfsiz HTTPS havola ulanmoqda...
echo.
echo ====================================================================
echo   TELEFONDA OCHISH UCHUN 2 XIL YO'L BOR:
echo.
echo   A) AGAR BIR XIL WI-FI GA ULANIB TURGAN BO'LSANGIZ:
echo      To'g'ridan-to'g'ri lokal IP manzildan kiring.
echo.
echo   B) AGAR INTERNET ORQALI DUNYONING ISTALGAN JOYIDAN KIRMOQCHI BO'LSANGIZ:
echo      Quyidagi "https://...serveousercontent.com" havolani oching!
echo ====================================================================
echo.

ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 serveo.net
pause
