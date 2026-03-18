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
        self.tesseract_config = self.config.get("ocr_config", "--oem 3 --psm 7")
        self.scale = self.config.get("image_scale", 2.0)
    
    def preprocess(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        processed = cv2.resize(gray, None, fx=self.scale, fy=self.scale, 
                              interpolation=cv2.INTER_CUBIC)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        processed = clahe.apply(processed)
        
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        denoised = cv2.fastNlMeansDenoising(processed, None, 10, 7, 21)
        
        return denoised
    
    def extract_text(self, img_array):
        processed = self.preprocess(img_array)
        
        text = pytesseract.image_to_string(
            processed,
            lang='rus',
            config='--oem 3 --psm 7 -c tessedit_char_whitelist=АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789 .,!?:-'
        )
        
        return text.strip()
    
    def find_text(self, img_array, search_text):
        text = self.extract_text(img_array)
        
        if not text:
            return False, ""
        
        found = search_text.lower() in text.lower()
        return found, text[:500]
    
    def debug_ocr(self, img_array, search_text):
        processed = self.preprocess(img_array)
        
        text = pytesseract.image_to_string(
            processed,
            lang='rus',
            config='--oem 3 --psm 7'
        )
        
        data = pytesseract.image_to_data(
            processed,
            lang='rus',
            config='--oem 3 --psm 7',
            output_type=pytesseract.Output.DICT
        )
        
        confidence = [int(c) for c in data['conf'] if int(c) > 0]
        avg_conf = sum(confidence) / len(confidence) if confidence else 0
        
        return {
            'text': text.strip(),
            'avg_confidence': avg_conf,
            'search_found': search_text.lower() in text.lower()
        }


def validate_config():
    config = load_config()
    errors = []
    
    if not os.path.exists(config["tesseract_path"]):
        errors.append(f"Tesseract не найден: {config['tesseract_path']}")
    
    os.makedirs(config.get("screenshots_dir", "screenshots"), exist_ok=True)
    os.makedirs(config.get("log_dir", "logs"), exist_ok=True)
    
    return errors
