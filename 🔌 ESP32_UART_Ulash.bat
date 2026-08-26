@echo off
chcp 65001 > nul
cd /d "%~dp0"
title ESP32 UART Serial Bridge

echo ====================================================================
echo   🔌 ESP32 UART -> MONITORGA MA'LUMOT UZATISH KO'PRIGI
echo ====================================================================
echo.
python esp32_serial_bridge.py
pause
