@echo off
chcp 65001 > nul
cd /d "%~dp0"
title GD/H126 Bemor Maniken Test va Imtihon Pulti

echo ====================================================================
echo   🎮 GD/H126 BEMOR MANIKEN TEST VA IMTIHON PULTI
echo ====================================================================
echo.
echo Server ishga tushmoqda va brauzer avtomatik ochiladi...
echo.

python manikin_console.py

pause
