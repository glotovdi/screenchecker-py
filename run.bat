@echo off
chcp 1251 >nul
title ScreenChecker

echo ========================================
echo         SCREENCHECKER
echo ========================================
echo.
echo 1 - GUI режим
echo 2 - Интерактивный режим
echo 3 - CLI режим
echo 4 - Установить зависимости
echo 5 - Выход
echo.

choice /c 12345 /n /m "Выберите действие: "

if errorlevel 5 exit /b
if errorlevel 4 goto install
if errorlevel 3 goto cli
if errorlevel 2 goto interactive
if errorlevel 1 goto gui

:gui
call run-gui.bat
goto end

:interactive
call run-interactive.bat
goto end

:cli
echo.
echo Использование: run-cli.bat --text "text" --region X Y W H
echo Пример: run-cli.bat --text "Hello" --region 0 0 800 600
echo.
call run-cli.bat --text "test" --select-region
goto end

:install
call install.bat
goto end

:end
pause
