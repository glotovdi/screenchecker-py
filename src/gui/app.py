import tkinter as tk
from tkinter import ttk, messagebox
import mss
import numpy as np
import threading
import time
import winsound
import json
from datetime import datetime
from PIL import Image

from src.core import setup_logger, OCRProcessor, validate_config


class ScreenCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Checker")
        self.root.geometry("500x350")
        self.root.minsize(400, 300)
        self.root.resizable(True, True)
        
        self.logger = setup_logger()
        self.ocr = OCRProcessor()
        
        self.running = False
        self.monitor_num = 1
        self.interval = 5
        self.search_text = ""
        self.found_count = 0
        self.scan_count = 0
        
        self.load_config()
        self.create_widgets()
        self.enumerate_monitors()
    
    def load_config(self):
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Монитор:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.monitor_var = tk.StringVar(value="1")
        self.monitor_combo = ttk.Combobox(
            top_frame, textvariable=self.monitor_var, width=15, state="readonly")
        self.monitor_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(top_frame, text="Интервал (сек):", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.interval_var = tk.StringVar(value=str(self.config.get("default_interval", 5)))
        interval_entry = ttk.Entry(top_frame, textvariable=self.interval_var, width=18)
        interval_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(top_frame, text="Текст для поиска:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.search_text_widget = tk.Text(top_frame, width=30, height=2, font=("Segoe UI", 10))
        self.search_text_widget.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.status_label = ttk.Label(
            main_frame, text="Готов к работе", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=10)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        self.start_btn = ttk.Button(
            button_frame, text="Старт", command=self.start_monitoring, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame, text="Стоп", command=self.stop_monitoring, width=12, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.stats_label = ttk.Label(
            main_frame, text="Сканирований: 0 | Найдено: 0", font=("Segoe UI", 9))
        self.stats_label.pack(pady=5)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=5, state="disabled",
                                 font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def enumerate_monitors(self):
        with mss.mss() as sct:
            monitors = [(i, f"Монитор {i} ({m['width']}x{m['height']})") 
                       for i, m in enumerate(sct.monitors) if i > 0]
        
        if not monitors:
            monitors = [(1, "Монитор 1")]
        
        self.monitor_combo["values"] = [m[1] for m in monitors]
        self.monitor_combo.current(0)
    
    def log_message(self, msg, level="info"):
        self.log_text.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", level)
        self.log_text.tag_config("green", foreground="#228B22")
        self.log_text.tag_config("red", foreground="#DC143C")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def update_stats(self):
        self.stats_label.config(text=f"Сканирований: {self.scan_count} | Найдено: {self.found_count}")
    
    def save_screenshot(self, img_array):
        import os
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.config['screenshots_dir'], exist_ok=True)
        filename = f"{self.config['screenshots_dir']}\\found_{timestamp}.png"
        Image.fromarray(img_array).save(filename)
        return filename
    
    def play_sound(self):
        import os
        try:
            sound_path = self.config["sound_file"]
            if not os.path.isabs(sound_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sound_path = os.path.join(base_dir, sound_path)
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения звука: {e}")
    
    def capture_monitor(self, monitor_index):
        with mss.mss() as sct:
            if monitor_index < len(sct.monitors):
                return sct.grab(sct.monitors[monitor_index])
        return None
    
    def start_monitoring(self):
        errors = validate_config()
        if errors:
            messagebox.showerror("Ошибка конфигурации", "\n".join(errors))
            return
        
        try:
            monitor_str = self.monitor_var.get()
            self.monitor_num = int(monitor_str.split()[1]) if "Монитор" in monitor_str else 1
            self.interval = int(self.interval_var.get())
            if self.interval < 1:
                raise ValueError("Интервал должен быть >= 1")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        
        self.search_text = self.search_text_widget.get("1.0", tk.END).strip()
        if not self.search_text:
            messagebox.showerror("Ошибка", "Введите текст для поиска")
            return
        
        self.running = True
        self.found_count = 0
        self.scan_count = 0
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Мониторинг активен...", foreground="#228B22")
        
        self.logger.info(f"Запуск мониторинга: монитор={self.monitor_num}, "
                        f"интервал={self.interval}с, текст='{self.search_text[:30]}...'")
        self.log_message(f"Запуск мониторинга монитора {self.monitor_num}")
        
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Готов к работе", foreground="black")
        self.log_message("Мониторинг остановлен")
        self.logger.info("Мониторинг остановлен пользователем")
    
    def monitor_loop(self):
        while self.running:
            try:
                screenshot = self.capture_monitor(self.monitor_num)
                
                if screenshot:
                    self.scan_count += 1
                    img_array = np.array(screenshot)
                    found, text = self.ocr.find_text(img_array, self.search_text)
                    
                    if found:
                        self.found_count += 1
                        filename = self.save_screenshot(img_array)
                        self.log_message(f"НАЙДЕНО! Скриншот: {filename}", "found")
                        self.logger.info(f"Текст найден: '{self.search_text}'")
                        self.play_sound()
                        self.root.after(0, self.update_stats)
                    else:
                        self.log_message("Проверка...")
                    
                    self.root.after(0, self.update_stats)
                
                time.sleep(self.interval)
                
            except Exception as e:
                self.log_message(f"Ошибка: {e}", "error")
                self.logger.error(f"Ошибка мониторинга: {e}")
                time.sleep(self.interval)
