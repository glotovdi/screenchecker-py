@echo off
chcp 65001 >nul
echo ========================================
echo   Проверка конфигурации Screen Checker
echo ========================================
echo.

py -3 src\core\check_config.py

pause
