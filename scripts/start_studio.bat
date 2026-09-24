@echo off
chcp 65001 >nul
title Anima Agent Studio
cd /d "%~dp0\.."
echo ============================================================
echo   🌸 Starting Anima Agent Studio...
echo ============================================================
python -u web_gui.py
pause
