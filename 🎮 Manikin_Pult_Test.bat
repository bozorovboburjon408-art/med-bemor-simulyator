@echo off
chcp 65001 > nul
cd /d "%~dp0"
title GD/H126 Manikin Tester Pulti (General Doctor)

echo ====================================================================
echo   🎮 GD/H126 GENERAL DOCTOR MANIKEN TEST PULTI ISHGA TUSHMOQDA...
echo ====================================================================
echo.
echo Brauzerda ochilmoqda: http://localhost:8600
start http://localhost:8600
python manikin_console.py
pause
