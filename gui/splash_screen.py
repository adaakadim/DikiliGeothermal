import tkinter as tk
from tkinter import ttk
import time

class SplashScreen(tk.Toplevel):
    def __init__(self, parent: tk.Widget = None, title: str = "Dikili Geothermal SCADA", version: str = "1.0.0"):
        # We can either be a Toplevel (if parent exists) or the temporary Root if no parent.
        if parent:
            super().__init__(parent)
            self.is_root = False
        else:
            # We are acting as a temporary root before the main app starts
            self.root = tk.Tk()
            self.is_root = True
            
        win = self.root if self.is_root else self
        
        win.overrideredirect(True)
        win.configure(bg="#0f172a") # Dark enterprise blue
        
        # Center on screen
        width = 600
        height = 400
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
        
        # Border
        frame = tk.Frame(win, bg="#0f172a", highlightbackground="#3b82f6", highlightthickness=2)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(frame, text=title, font=("Segoe UI", 28, "bold"), bg="#0f172a", fg="#f8fafc").pack(pady=(100, 10))
        tk.Label(frame, text=f"Enterprise Edition v{version}", font=("Segoe UI", 12), bg="#0f172a", fg="#94a3b8").pack(pady=(0, 50))
        
        # Status Label
        self.lbl_status = tk.Label(frame, text="Initializing core subsystems...", font=("Segoe UI", 10), bg="#0f172a", fg="#e2e8f0")
        self.lbl_status.pack(pady=(0, 10))
        
        # Progress Bar
        style = ttk.Style(win)
        style.theme_use('clam')
        style.configure("Splash.Horizontal.TProgressbar", background="#3b82f6", troughcolor="#1e293b", bordercolor="#0f172a", lightcolor="#3b82f6", darkcolor="#3b82f6")
        
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=400, mode='determinate', style="Splash.Horizontal.TProgressbar")
        self.progress.pack()
        
        self.win = win

    def update_progress(self, value: int, message: str):
        self.progress["value"] = value
        self.lbl_status.config(text=message)
        self.win.update()
        
    def close(self):
        self.win.destroy()

def run_splash_sequence():
    """Run a fake initialization sequence for polish."""
    splash = SplashScreen()
    
    steps = [
        (10, "Loading configuration..."),
        (25, "Initializing Historian database..."),
        (40, "Connecting to Digital Twin..."),
        (60, "Loading AI models..."),
        (80, "Starting Predictive Maintenance Engine..."),
        (95, "Compiling GUI assets..."),
        (100, "System Ready.")
    ]
    
    for val, msg in steps:
        splash.update_progress(val, msg)
        time.sleep(0.3)
        
    splash.close()
