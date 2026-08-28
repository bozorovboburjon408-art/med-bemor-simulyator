@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Bemor Maniken Test va Imtihon Pulti

echo ====================================================================
echo   🎓 BEMOR MANIKEN TEST VA IMTIHON PULTI ISHGA TUSHMOQDA...
echo ====================================================================
echo.

:: 1. Eski qotib qolgan port 8600 jarayonlarini tozalash (Port xatosini oldini olish)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8600 ^| findstr LISTENING') do (
    taskkill /F /PID %%a > nul 2>&1
)

:: 2. Maniken Console serverini ishga tushirish
start /b python manikin_console.py

:: 3. Server to'liq yuklanishi uchun 1.5 soniya kutish
timeout /t 2 /nobreak > nul

:: 4. Brauzerni keshsiz yangi holatda ochish
echo Brauzerda ochilmoqda: http://localhost:8600
start http://localhost:8600/?v=%random%

echo.
echo ====================================================================
echo   ✅ TIZIM MUVAFFAQIYATLI ISHGA TUSHDI!
echo   Pult manzili: http://localhost:8600
echo   Darchani yopmang, pult fonda ishlaydi.
echo ====================================================================
echo.

:: Serverni jonli ushlab turish
python manikin_console.py
pause
