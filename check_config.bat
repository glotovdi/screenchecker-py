@echo off
chcp 65001 >nul
echo ========================================
echo   Проверка конфигурации Screen Checker
echo ========================================
echo.

py -3 -c "
import json
import os
import sys

try:
    with open('data/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as e:
    print(f'[ОШИБКА] Не удалось прочитать config.json: {e}')
    sys.exit(1)

errors = []

tesseract = config.get('tesseract_path', '')
if not os.path.exists(tesseract):
    errors.append(f'[ОШИБКА] Tesseract не найден: {tesseract}')
else:
    print(f'[OK] Tesseract: {tesseract}')

sound = config.get('sound_file', '')
if not os.path.exists(sound):
    errors.append(f'[ОШИБКА] Звуковой файл не найден: {sound}')
else:
    print(f'[OK] Звуковой файл: {sound}')

screenshots = config.get('screenshots_dir', 'data/screenshots')
if not os.path.exists(screenshots):
    print(f'[СОЗДАНО] Папка скриншотов: {screenshots}')
    os.makedirs(screenshots, exist_ok=True)
else:
    print(f'[OK] Папка скриншотов: {screenshots}')

logs = config.get('log_dir', 'data/logs')
if not os.path.exists(logs):
    print(f'[СОЗДАНО] Папка логов: {logs}')
    os.makedirs(logs, exist_ok=True)
else:
    print(f'[OK] Папка логов: {logs}')

print()
if errors:
    print('=' * 40)
    print(' НАЙДЕНЫ ОШИБКИ КОНФИГУРАЦИИ:')
    print('=' * 40)
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print('=' * 40)
    print(' КОНФИГУРАЦИЯ OK - ВСЁ ГОТОВО К РАБОТЕ')
    print('=' * 40)
"

pause
