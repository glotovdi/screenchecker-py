import tkinter as tk
import mss


class RegionSelector:
    def __init__(self, monitor_num=1):
        self.region = None
        self.start_x = 0
        self.start_y = 0
        self.monitor_num = monitor_num
        
        with mss.mss() as sct:
            monitor = sct.monitors[monitor_num]
        
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='gray')
        
        self.canvas = tk.Canvas(self.root, cursor='cross', bg='gray', 
                               highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.rect = None
        
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        self.root.bind('<Escape>', lambda e: self.cancel())
        
        self.root.focus_force()
        self.root.grab_set()
    
    def on_click(self, event):
        self.start_x = self.root.winfo_x() + event.x
        self.start_y = self.root.winfo_y() + event.y
        
        if self.rect:
            self.canvas.delete(self.rect)
        
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=3
        )
    
    def on_drag(self, event):
        if self.rect:
            current_x = self.root.winfo_x() + event.x
            current_y = self.root.winfo_y() + event.y
            self.canvas.coords(
                self.rect,
                self.start_x, self.start_y, current_x, current_y
            )
    
    def on_release(self, event):
        end_x = self.root.winfo_x() + event.x
        end_y = self.root.winfo_y() + event.y
        
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        self.region = {
            'x': x1,
            'y': y1,
            'width': x2 - x1,
            'height': y2 - y1
        }
        
        self.root.destroy()
    
    def cancel(self):
        self.region = None
        self.root.destroy()
    
    def get_region(self):
        self.root.wait_window()
        return self.region
