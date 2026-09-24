@echo off
chcp 65001 >nul
title Image Agent Studio
cd /d "%~dp0\.."
echo ============================================================
echo   🌸 Starting Image Agent Studio...
echo ============================================================
python -u web_gui.py
pause
