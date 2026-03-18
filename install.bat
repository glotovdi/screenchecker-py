@echo off
chcp 65001 >nul
echo ========================================
echo   Установка зависимостей Screen Checker
echo ========================================
echo.

py -3 -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo [OK] Зависимости установлены успешно
pause
