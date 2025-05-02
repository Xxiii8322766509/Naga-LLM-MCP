@echo off
chcp 65001 >nul
title Naga Assistant 2.0 - Multi-Channel Processing Agent
cd /d %~dp0
call .venv\Scripts\activate.bat
python main.py
pause 