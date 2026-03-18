@echo off
chcp 1251 >nul
title ScreenChecker - Install

echo ========================================
echo    ScreenChecker - Установка зависимостей
echo ========================================
echo.

:: Проверка Python
python3 --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python не найден!
        echo Установите Python 3.7+ с python.org
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
    set PYCMD=python
    echo [OK] Python найден: 
    python --version
) else (
    set PYCMD=python3
    echo [OK] Python найден:
    python3 --version
)

echo.
echo Установка зависимостей...
echo.

%PYCMD% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка установки!
    echo Попробуйте: %PYCMD% -m pip install --upgrade pip
) else (
    echo.
    echo [OK] Зависимости установлены!
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
