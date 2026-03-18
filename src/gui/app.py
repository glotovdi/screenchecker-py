import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mss
import numpy as np
import threading
import time
import json
import os
from datetime import datetime
from PIL import Image

import pygame
pygame.mixer.init()

from src.core import setup_logger, OCRProcessor, validate_config, get_monitor_info
from src.core.region_selector import RegionSelector


class ScreenCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Checker")
        self.root.geometry("550x450")
        self.root.minsize(450, 400)
        self.root.resizable(True, True)
        
        self.logger = setup_logger()
        self.ocr = OCRProcessor()
        self.monitor_thread = None
        self.running = False
        self.monitor_num = 1
        self.interval = 5
        self.search_text = ""
        self.found_count = 0
        self.scan_count = 0
        self.sound_file = ""
        self.region = None
        self.use_region = tk.BooleanVar(value=False)
        
        self.load_config()
        self.create_widgets()
        self.enumerate_monitors()
    
    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.sound_file = self.config.get("sound_file", "")
    
    def save_config(self):
        self.config["sound_file"] = self.sound_file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Монитор:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.monitor_var = tk.StringVar(value="1")
        self.monitor_combo = ttk.Combobox(
            top_frame, textvariable=self.monitor_var, width=12, state="readonly")
        self.monitor_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.monitor_combo.bind('<<ComboboxSelected>>', lambda e: self.on_monitor_change())
        
        ttk.Checkbutton(top_frame, text="Область", variable=self.use_region, 
                        command=self.on_region_toggle).grid(row=0, column=2, padx=10)
        
        self.region_btn = ttk.Button(top_frame, text="Выбрать область", 
                                     command=self.select_region, width=12)
        self.region_btn.grid(row=0, column=3, pady=5)
        self.region_btn.state(['disabled'])
        
        self.region_label = tk.Label(top_frame, text="Весь экран", font=("Segoe UI", 9), fg="gray")
        self.region_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, padx=5)
        
        ttk.Label(top_frame, text="Интервал (сек):", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.interval_var = tk.StringVar(value=str(self.config.get("default_interval", 5)))
        interval_entry = ttk.Entry(top_frame, textvariable=self.interval_var, width=18)
        interval_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(top_frame, text="Текст для поиска:", font=("Segoe UI", 10)).grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.search_text_widget = tk.Text(top_frame, width=30, height=2, font=("Segoe UI", 10))
        self.search_text_widget.grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        sound_frame = ttk.Frame(top_frame)
        sound_frame.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        ttk.Label(sound_frame, text="Звук:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.sound_label = tk.Label(sound_frame, text="Не выбран", font=("Segoe UI", 9), fg="gray")
        self.sound_label.pack(side=tk.LEFT)
        if self.sound_file and os.path.exists(self.sound_file):
            self.sound_label.config(text=os.path.basename(self.sound_file), fg="green")
        ttk.Button(sound_frame, text="Выбрать", command=self.select_sound, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(sound_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        volume_frame = ttk.Frame(sound_frame)
        volume_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(volume_frame, text="Громкость:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_slider = ttk.Scale(volume_frame, from_=0.5, to=5.0, orient=tk.HORIZONTAL,
                                       variable=self.volume_var, length=100,
                                       command=lambda v: self.on_volume_change(v))
        self.volume_slider.pack(side=tk.LEFT, padx=5)
        self.volume_label = tk.Label(volume_frame, text="1.0x", font=("Segoe UI", 9), width=5)
        self.volume_label.pack(side=tk.LEFT)
        
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
        
        tools_frame = ttk.Frame(main_frame)
        tools_frame.pack(pady=5)
        
        ttk.Button(tools_frame, text="Сброс логов", command=self.clear_logs, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(tools_frame, text="Сброс работы", command=self.reset_work, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(tools_frame, text="Удалить скриншоты", command=self.delete_screenshots, width=15).pack(side=tk.LEFT, padx=3)
        
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
    
    def on_monitor_change(self):
        if self.use_region.get():
            self.region = None
            self.region_label.config(text="Весь экран", fg="gray")
    
    def on_region_toggle(self):
        if self.use_region.get():
            self.region_btn.state(['!disabled'])
        else:
            self.region_btn.state(['disabled'])
            self.region = None
            self.region_label.config(text="Весь экран", fg="gray")
    
    def select_region(self):
        try:
            monitor_str = self.monitor_var.get()
            monitor_num = int(monitor_str.split()[1]) if "Монитор" in monitor_str else 1
        except:
            monitor_num = 1
        
        monitor_info = get_monitor_info(monitor_num)
        if not monitor_info:
            messagebox.showerror("Ошибка", "Не удалось получить информацию о мониторе")
            return
        
        self.root.withdraw()
        time.sleep(0.2)
        
        selector = RegionSelector(monitor_info)
        region = selector.get_region()
        
        self.root.deiconify()
        self.root.focus_force()
        
        if region and region['width'] > 10 and region['height'] > 10:
            self.region = region
            self.region_label.config(
                text=f"Область: {region['width']}x{region['height']} (x={region['x']}, y={region['y']})",
                fg="green"
            )
            self.log_message(f"Выбрана область: {region['width']}x{region['height']}", "yellow")
        else:
            self.region = None
            self.use_region.set(False)
            self.region_label.config(text="Весь экран", fg="gray")
    
    def select_sound(self):
        filepath = filedialog.askopenfilename(
            title="Выберите звуковой файл",
            filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")]
        )
        if filepath:
            self.sound_file = filepath
            self.sound_label.config(text=os.path.basename(filepath), fg="green")
            self.save_config()
            self.log_message(f"Звуковой файл: {os.path.basename(filepath)}")
    
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
        self.log_text.tag_config("yellow", foreground="#DAA520")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def update_stats(self):
        self.stats_label.config(text=f"Сканирований: {self.scan_count} | Найдено: {self.found_count}")
    
    def save_screenshot(self, img_array):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.config['screenshots_dir'], exist_ok=True)
        filename = f"{self.config['screenshots_dir']}\\found_{timestamp}.png"
        Image.fromarray(img_array).save(filename)
        return filename
    
    def on_volume_change(self, value=None):
        if value is None:
            value = self.volume_var.get()
        self.volume_label.config(text=f"{value:.1f}x")
    
    def play_sound(self):
        if not self.sound_file or not os.path.exists(self.sound_file):
            return
        try:
            volume = self.volume_var.get()
            
            sound = pygame.mixer.Sound(self.sound_file)
            sound.set_volume(min(1.0, volume))
            
            repetitions = max(1, int(volume))
            sound.play(repetitions=repetitions - 1)
            
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения звука: {e}")
    
    def capture_region(self, region):
        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_num].copy()
            monitor['left'] = region['x']
            monitor['top'] = region['y']
            monitor['width'] = region['width']
            monitor['height'] = region['height']
            return sct.grab(monitor)
    
    def capture_monitor(self):
        with mss.mss() as sct:
            if self.monitor_num < len(sct.monitors):
                return sct.grab(sct.monitors[self.monitor_num])
        return None
    
    def clear_logs(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        self.log_message("Логи очищены", "yellow")
    
    def reset_work(self):
        self.running = False
        self.found_count = 0
        self.scan_count = 0
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        self.monitor_thread = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Готов к работе", foreground="black")
        self.update_stats()
        self.log_message("Работа сброшена", "yellow")
        self.logger.info("Работа сброшена пользователем")
    
    def delete_screenshots(self):
        screenshots_dir = self.config.get('screenshots_dir', 'data/screenshots')
        if os.path.exists(screenshots_dir):
            count = 0
            for f in os.listdir(screenshots_dir):
                if f.endswith('.png'):
                    try:
                        os.remove(os.path.join(screenshots_dir, f))
                        count += 1
                    except:
                        pass
            self.log_message(f"Удалено скриншотов: {count}", "yellow")
        else:
            self.log_message("Папка скриншотов пуста", "yellow")
    
    def start_monitoring(self):
        errors = validate_config()
        if errors:
            messagebox.showerror("Ошибка конфигурации", "\n".join(errors))
            return
        
        if not self.sound_file:
            if not messagebox.askyesno("Внимание", "Звуковой файл не выбран. Продолжить?"):
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
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Мониторинг активен...", foreground="#228B22")
        
        capture_mode = "область" if self.use_region.get() and self.region else "экран"
        self.logger.info(f"Запуск мониторинга: монитор={self.monitor_num}, "
                        f"режим={capture_mode}, интервал={self.interval}с")
        self.log_message(f"Запуск мониторинга (режим: {capture_mode})")
        
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Готов к работе", foreground="black")
        self.log_message("Мониторинг остановлен")
        self.logger.info("Мониторинг остановлен пользователем")
    
    def monitor_loop(self):
        self.root.after(0, lambda: self.stop_btn.config(state="normal"))
        
        while self.running:
            try:
                if self.use_region.get() and self.region:
                    screenshot = self.capture_region(self.region)
                else:
                    screenshot = self.capture_monitor()
                
                if screenshot:
                    self.scan_count += 1
                    img_array = np.array(screenshot)
                    found, text = self.ocr.find_text(img_array, self.search_text)
                    
                    if found:
                        self.found_count += 1
                        filename = self.save_screenshot(img_array)
                        self.log_message(f"НАЙДЕНО! Скриншот: {os.path.basename(filename)}", "found")
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
