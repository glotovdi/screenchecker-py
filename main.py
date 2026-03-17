import mss
import numpy as np
import pytesseract
import winsound
import time
import os
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def list_monitors():
    """Показывает все доступные мониторы"""
    with mss.mss() as sct:
        for i, monitor in enumerate(sct.monitors):
            print(f"\nМонитор {i}:")
            print(f"  left: {monitor['left']}")
            print(f"  top: {monitor['top']}")
            print(f"  width: {monitor['width']}")
            print(f"  height: {monitor['height']}")

def save_screenshot(img):
    """Сохраняет скриншот с уникальным именем"""
    # Создаем имя файла с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"found_{timestamp}.png"
    
    # Сохраняем через PIL
    from PIL import Image
    Image.fromarray(img).save(filename)
    
    print(f"   📸 Скриншот сохранен: {filename}")
    return filename

def capture_monitor(monitor_index, region=None):
    """
    Делает скриншот указанного монитора
    monitor_index: 0 - все мониторы, 1 - первый, 2 - второй и т.д.
    region: (x, y, width, height) - область на мониторе
    """
    with mss.mss() as sct:
        if monitor_index < len(sct.monitors):
            monitor = sct.monitors[monitor_index].copy()
            
            if region:
                x, y, w, h = region
                monitor['left'] += x
                monitor['top'] += y
                monitor['width'] = w
                monitor['height'] = h
            
            return sct.grab(monitor)
        else:
            print(f"Монитор {monitor_index} не существует")
            return None

# Использование
print("Доступные мониторы:")
list_monitors()

monitor_num = int(input("\nНомер монитора (1 - первый, 2 - второй): "))
interval = int(input("\nВведите интервал в секундах: "))
text = input("\nВведите текст для поиска: ")
sound_file = r'C:\sound.wav'

print(f"\n🔍 Мониторинг монитора {monitor_num}...")

try:
    while True:
        # Скриншот всего второго монитора
        screenshot = capture_monitor(monitor_num)
        
        if screenshot:
            img = np.array(screenshot)
            found = pytesseract.image_to_string(img, lang='rus')
            
            if text.lower() in found.lower():
                save_screenshot(img)
                print(f"[{time.strftime('%H:%M:%S')}] ✅ НАЙДЕНО!")
                os.startfile(sound_file)
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ нет")
        
        time.sleep(interval)
        
except KeyboardInterrupt:
    print("\n👋 Стоп")