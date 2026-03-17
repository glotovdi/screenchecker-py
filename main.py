import cv2
import pyautogui
import pytesseract
import winsound
import os
import time
import datetime
from threading import Thread

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def log_event(message):
    """Запись в лог-файл"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("text_monitor.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def monitor():
    print("📝 МОНИТОРИНГ ТЕКСТА (с логированием)\n")
    
    text = input("Текст для поиска: ")
    
    print("\nКоординаты области:")
    x1 = int(input("X1: "))
    y1 = int(input("Y1: "))
    x2 = int(input("X2: "))
    y2 = int(input("Y2: "))
    
    music = input("\nПуть к WAV файлу (Enter для сигнала): ").strip()
    interval = float(input("Интервал проверки (сек): "))
    
    log_event(f"Запуск мониторинга текста '{text}' в области ({x1},{y1})-({x2},{y2})")
    print("\n🔍 Мониторинг запущен. Нажмите Ctrl+C для остановки...\n")
    
    try:
        while True:
            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            img = cv2.cvtColor(cv2.UMat(np.array(screenshot)), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            recognized = pytesseract.image_to_string(gray, lang='rus+eng')
            
            if text.lower() in recognized.lower():
                log_event(f"✅ Текст найден! Распознано: {recognized.strip()}")
                
                if music and os.path.exists(music):
                    winsound.PlaySound(music, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.Beep(1000, 500)
                
                time.sleep(5)  # Пауза чтобы не спамить
            else:
                log_event("❌ Текст не найден")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        log_event("Мониторинг остановлен пользователем")
        print("\n👋 Мониторинг завершен")

if __name__ == "__main__":
    monitor()