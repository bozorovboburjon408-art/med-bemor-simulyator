@echo off
chcp 65001 > nul
cd /d "%~dp0"
title GD/H126 Bemor Maniken Test va Imtihon Pulti

echo ====================================================================
echo   🎮 GD/H126 BEMOR MANIKEN TEST VA IMTIHON PULTI
echo ====================================================================
echo.
echo Brauzerda ochilmoqda: http://localhost:8600
echo.

start http://localhost:8600
python manikin_console.py

pause
