@echo off
chcp 1251 >nul
title ScreenChecker - CLI

echo ========================================
echo    ScreenChecker - CLI Mode
echo ========================================
echo.

:: Проверка Python
python3 --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python не найден!
        echo Установите Python 3.7+ с python.org
        pause
        exit /b 1
    )
    set PYCMD=python
) else (
    set PYCMD=python3
)

:: Проверка зависимостей
%PYCMD% -c "import cv2, pyautogui, pytesseract, numpy" 2>nul
if errorlevel 1 (
    echo [WARNING] Зависимости не установлены.
    echo Запустите install.bat для установки.
    pause
    exit /b 1
)

:: Запуск с параметрами
:: Пример: run-cli.bat --text "Hello" --region 0 0 800 600
%PYCMD% main.py %*

pause
