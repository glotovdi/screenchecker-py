import cv2
import numpy as np
import pytesseract
import json
import os
import random

os.environ['PYTHONHASHSEED'] = '42'
random.seed(42)
np.random.seed(42)


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
        
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        kernel = np.ones((1, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.bitwise_not(thresh)
        
        height, width = gray.shape
        new_height = int(height * self.scale)
        new_width = int(width * self.scale)
        processed = cv2.resize(thresh, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return processed
    
    def extract_text(self, img_array, psm=6):
        processed = self.preprocess(img_array)
        
        data = pytesseract.image_to_data(
            processed,
            lang='rus+eng',
            config=f'--oem 1 --psm {psm}',
            output_type=pytesseract.Output.DICT
        )
        
        confidence = [float(c) for c in data['conf'] if c != '-1']
        avg_conf = sum(confidence) / len(confidence) if confidence else 0
        
        text = pytesseract.image_to_string(
            processed,
            lang='rus+eng',
            config=f'--oem 1 --psm {psm}'
        )
        
        return text.strip(), avg_conf
    
    def extract_text_best(self, img_array):
        psm_modes = [6, 11, 4]
        best_text = ""
        best_conf = 0
        
        for psm in psm_modes:
            text, conf = self.extract_text(img_array, psm=psm)
            if conf > best_conf:
                best_conf = conf
                best_text = text
        
        return best_text, best_conf
    
    def find_text(self, img_array, search_text, use_best=False):
        if use_best:
            text, confidence = self.extract_text_best(img_array)
        else:
            text, confidence = self.extract_text(img_array)
        
        if not text:
            return False, "", confidence
        
        found = search_text.lower() in text.lower()
        return found, text[:500], confidence


def validate_config():
    config = load_config()
    errors = []
    
    tesseract_path = config.get("tesseract_path", "")
    if not tesseract_path or not os.path.exists(tesseract_path):
        errors.append(f"Tesseract не найден: {tesseract_path}")
    
    screenshots = config.get("screenshots_dir", "screenshots")
    log_dir = config.get("log_dir", "logs")
    os.makedirs(screenshots, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    return errors
