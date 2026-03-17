@echo off
chcp 1251 >nul
title Поиск текста на экране

echo ========================================
echo    ПОИСК ТЕКСТА НА ЭКРАНЕ (Windows)
echo ========================================
echo.

:: Проверка наличия Python
python3 --version 
if errorlevel 1 (
    echo [ERROR] Python не найден!
    echo Установите Python с python.org
    pause
    exit /b
)

:: Запуск скрипта
python3 main.py

pause