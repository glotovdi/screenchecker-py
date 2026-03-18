import cv2
import numpy as np
import pytesseract
import json
import os


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


class OCRProcessor:
    def __init__(self):
        self.config = load_config()
        pytesseract.pytesseract.tesseract_cmd = self.config["tesseract_path"]
        self.tesseract_config = self.config.get("ocr_config", "--oem 3 --psm 6")
        self.scale = self.config.get("image_scale", 1.5)
        self.min_conf = self.config.get("min_confidence", 60)
    
    def preprocess(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        scale = int(100 * self.scale)
        processed = cv2.resize(gray, None, fx=self.scale, fy=self.scale, 
                              interpolation=cv2.INTER_CUBIC)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed = clahe.apply(processed)
        
        _, binary = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    def extract_text(self, img_array):
        processed = self.preprocess(img_array)
        
        text = pytesseract.image_to_string(
            processed,
            lang='rus+eng',
            config=self.tesseract_config
        )
        
        return text.strip()
    
    def find_text(self, img_array, search_text):
        text = self.extract_text(img_array)
        
        if not text:
            return False, ""
        
        found = search_text.lower() in text.lower()
        return found, text[:200]


def validate_config():
    config = load_config()
    errors = []
    
    if not os.path.exists(config["tesseract_path"]):
        errors.append(f"Tesseract не найден: {config['tesseract_path']}")
    
    if not os.path.exists(config["sound_file"]):
        errors.append(f"Звуковой файл не найден: {config['sound_file']}")
    
    os.makedirs(config.get("screenshots_dir", "screenshots"), exist_ok=True)
    os.makedirs(config.get("log_dir", "logs"), exist_ok=True)
    
    return errors
