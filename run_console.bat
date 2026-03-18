@echo off
chcp 65001 >nul
title Screen Checker - Console Mode
cd /d "%~dp0"
py -3 src\main.py --console
