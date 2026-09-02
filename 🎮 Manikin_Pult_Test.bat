@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MedLife - Yurak-O'pka Reanimatsiyasi Simulyatori

echo ====================================================================
echo   🫀 MEDLIFE: YURAK-O'PKA REANIMATSIYASI (CPR) SIMULYATORI
echo ====================================================================
echo.
echo Server ishga tushmoqda va brauzer avtomatik ochiladi...
echo.

python manikin_console.py

pause
