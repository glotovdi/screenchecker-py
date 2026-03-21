import cv2
import numpy as np
import pytesseract
import json
import os


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class OCRProcessor:
    def __init__(self):
        self.config = load_config()
        pytesseract.pytesseract.tesseract_cmd = self.config["tesseract_path"]
        self.scale = self.config.get("image_scale", 3.0)
    
    def preprocess(self, img_array):
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
        
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        height, width = gray.shape
        new_height = int(height * self.scale)
        new_width = int(width * self.scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return gray
    
    def extract_text(self, img_array):
        processed = self.preprocess(img_array)
        
        text = pytesseract.image_to_string(
            processed,
            lang='rus',
            config='--oem 3 --psm 6'
        )
        
        return text.strip()
    
    def find_text(self, img_array, search_text):
        text = self.extract_text(img_array)
        
        if not text:
            return False, ""
        
        found = search_text.lower() in text.lower()
        return found, text[:500]


def validate_config():
    config = load_config()
    errors = []
    
    if not os.path.exists(config["tesseract_path"]):
        errors.append(f"Tesseract не найден: {config['tesseract_path']}")
    
    os.makedirs(config.get("screenshots_dir", "screenshots"), exist_ok=True)
    os.makedirs(config.get("log_dir", "logs"), exist_ok=True)
    
    return errors
