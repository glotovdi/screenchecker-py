import sys
import os
import time
import mss
import numpy as np
import winsound
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import setup_logger, OCRProcessor, validate_config


class ConsoleMode:
    def __init__(self):
        self.logger = setup_logger("screenchecker_console")
        self.ocr = OCRProcessor()
        self.running = False
    
    def select_monitor(self):
        with mss.mss() as sct:
            monitors = [(i, f"Монитор {i} ({m['width']}x{m['height']})")
                       for i, m in enumerate(sct.monitors) if i > 0]
        
        if not monitors:
            monitors = [(1, "Монитор 1")]
        
        print("Доступные мониторы:")
        for idx, name in monitors:
            print(f"  {idx} - {name}")
        
        while True:
            try:
                choice = int(input("\nВыберите монитор: "))
                if choice in [m[0] for m in monitors]:
                    return choice
                print("Неверный выбор.")
            except ValueError:
                print("Введите число.")
    
    def get_settings(self):
        monitor = self.select_monitor()
        
        while True:
            try:
                interval = int(input("Интервал проверки (сек): "))
                if interval >= 1:
                    break
                print("Минимум 1 секунда.")
            except ValueError:
                print("Введите число.")
        
        text = input("Текст для поиска: ").strip()
        if not text:
            print("Текст не может быть пустым.")
            return self.get_settings()
        
        return monitor, interval, text
    
    def capture_monitor(self, monitor_index):
        with mss.mss() as sct:
            if monitor_index < len(sct.monitors):
                return sct.grab(sct.monitors[monitor_index])
        return None
    
    def save_screenshot(self, img_array):
        from PIL import Image
        config = self.ocr.config
        screenshots_dir = f"data/{config.get('screenshots_dir', 'screenshots')}"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{screenshots_dir}/found_{timestamp}.png"
        Image.fromarray(img_array).save(filename)
        return filename
    
    def play_sound(self):
        try:
            winsound.PlaySound(self.ocr.config["sound_file"], winsound.SND_FILENAME)
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения звука: {e}")
    
    def run(self):
        errors = validate_config()
        if errors:
            print("\n[ОШИБКИ КОНФИГУРАЦИИ]:")
            for err in errors:
                print(f"  - {err}")
            print("\nЗапустите check_config.bat для исправления.\n")
            return
        
        monitor, interval, search_text = self.get_settings()
        
        print(f"\n{'─' * 50}")
        print(f"  Монитор: {monitor}")
        print(f"  Интервал: {interval} сек")
        print(f"  Текст: {search_text}")
        print(f"{'─' * 50}")
        print("\nНажмите Ctrl+C для остановки...\n")
        
        self.logger.info(f"Запуск консольного мониторинга: монитор={monitor}, "
                        f"интервал={interval}с, текст='{search_text}'")
        
        self.running = True
        scan_count = 0
        found_count = 0
        
        try:
            while self.running:
                screenshot = self.capture_monitor(monitor)
                
                if screenshot:
                    scan_count += 1
                    img_array = np.array(screenshot)
                    found, text = self.ocr.find_text(img_array, search_text)
                    
                    if found:
                        found_count += 1
                        filename = self.save_screenshot(img_array)
                        print(f"\n\n>>> НАЙДЕНО! <<<\n   Скриншот: {filename}\n")
                        self.logger.info(f"Текст '{search_text}' найден")
                        self.play_sound()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n\nОстановка мониторинга...")
            self.logger.info("Мониторинг остановлен пользователем")
            print(f"\nСтатистика: {scan_count} сканирований, {found_count} найдено")


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    app = ConsoleMode()
    app.run()
    input("\nНажмите Enter для выхода...")
