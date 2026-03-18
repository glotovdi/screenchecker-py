import mss
import numpy as np
from PIL import Image


class ScreenCapture:
    def __init__(self):
        self.sct = None
    
    def get_monitors(self):
        with mss.mss() as sct:
            return [
                {"index": i, "width": m["width"], "height": m["height"], "left": m["left"], "top": m["top"]}
                for i, m in enumerate(sct.monitors)
            ]
    
    def capture(self, monitor_index=1, region=None):
        with mss.mss() as sct:
            if monitor_index >= len(sct.monitors):
                return None
            
            monitor = sct.monitors[monitor_index].copy()
            
            if region:
                x, y, w, h = region
                monitor['left'] += x
                monitor['top'] += y
                monitor['width'] = w
                monitor['height'] = h
            
            screenshot = sct.grab(monitor)
            return np.array(screenshot)
    
    def save_screenshot(self, img_array, filepath):
        Image.fromarray(img_array).save(filepath)
