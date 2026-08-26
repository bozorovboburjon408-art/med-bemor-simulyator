@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Bemor Simulyatori va Monitor - Internetga Chiqarish

echo ====================================================================
echo   🌐 BEMOR SIMULYATORI VA VITAL MONITORNI INTERNETGA CHIQARISH
echo ====================================================================
echo.
python online_server.py
pause
