import tkinter as tk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui import ScreenCheckerApp
from src.core import validate_config


def main():
    mode = None
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode == "--console":
        from src.console_mode import main as console_main
        console_main()
    else:
        errors = validate_config()
        
        root = tk.Tk()
        app = ScreenCheckerApp(root)
        
        if errors:
            messagebox.showwarning("Предупреждение конфигурации", 
                                   "Некоторые настройки требуют внимания:\n" + "\n".join(errors))
        
        root.mainloop()


if __name__ == "__main__":
    main()
