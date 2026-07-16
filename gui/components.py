import tkinter as tk
from tkinter import ttk
import math
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, BG_SECONDARY, TEXT_PRIMARY, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL

class KPICard(ttk.Frame):
    """Reusable Enterprise KPI Card with Title, Value, Unit, Trend, and Timestamp."""
    def __init__(self, parent, title: str, unit: str = "", default_val: str = "--"):
        super().__init__(parent, style="Card.TFrame")
        
        # Inner padding frame
        self.inner = ttk.Frame(self, style="Card.TFrame")
        self.inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header (Title + Time)
        self.header = ttk.Frame(self.inner, style="Card.TFrame")
        self.header.pack(fill=tk.X)
        
        self.lbl_title = tk.Label(self.header, text=title.upper(), font=FONT_LABEL, bg=BG_SECONDARY, fg="#94a3b8")
        self.lbl_title.pack(side=tk.LEFT)
        
        self.lbl_time = tk.Label(self.header, text="--:--:--", font=("Segoe UI", 8), bg=BG_SECONDARY, fg="#64748b")
        self.lbl_time.pack(side=tk.RIGHT)
        
        # Value row
        self.val_frame = ttk.Frame(self.inner, style="Card.TFrame")
        self.val_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.lbl_val = tk.Label(self.val_frame, text=default_val, font=("Segoe UI", 24, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY)
        self.lbl_val.pack(side=tk.LEFT)
        
        self.lbl_unit = tk.Label(self.val_frame, text=unit, font=FONT_SUBTITLE, bg=BG_SECONDARY, fg="#64748b")
        self.lbl_unit.pack(side=tk.LEFT, padx=(5, 0), anchor="s")
        
        # Trend
        self.lbl_trend = tk.Label(self.val_frame, text="--", font=FONT_LABEL, bg=BG_SECONDARY, fg="#94a3b8")
        self.lbl_trend.pack(side=tk.RIGHT, anchor="s")
        
        self.prev_val = None

    def update_value(self, val: float, formatted_str: str, color: str = TEXT_PRIMARY):
        self.lbl_val.config(text=formatted_str, fg=color)
        
        import datetime
        self.lbl_time.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        
        # Calculate trend arrow
        if self.prev_val is not None:
            if val > self.prev_val * 1.01:
                self.lbl_trend.config(text="▲", fg=CLR_CRITICAL if color == CLR_CRITICAL else CLR_NORMAL)
            elif val < self.prev_val * 0.99:
                self.lbl_trend.config(text="▼", fg=CLR_WARNING if color == CLR_CRITICAL else "#3b82f6")
            else:
                self.lbl_trend.config(text="●", fg="#94a3b8")
        self.prev_val = val


class StatusGauge(tk.Canvas):
    """Animated canvas radial gauge."""
    def __init__(self, parent, width=150, height=150, bg=BG_SECONDARY, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.arc_width = 12
        self.target_val = 0
        self.current_val = 0
        self.val_color = CLR_NORMAL
        
        # Draw background track
        self.create_arc(20, 20, width-20, height-20, start=180, extent=-180, style=tk.ARC, width=self.arc_width, outline="#1e293b")
        self.arc = self.create_arc(20, 20, width-20, height-20, start=180, extent=0, style=tk.ARC, width=self.arc_width, outline=self.val_color)
        
        self.lbl = self.create_text(width/2, height - 30, text="0%", font=("Segoe UI", 20, "bold"), fill=TEXT_PRIMARY)
        self.animating = False

    def set_value(self, pct: float, color: str = CLR_NORMAL):
        self.target_val = max(0, min(100, pct))
        self.val_color = color
        if not self.animating:
            self._animate()

    def _animate(self):
        self.animating = True
        diff = self.target_val - self.current_val
        if abs(diff) < 0.5:
            self.current_val = self.target_val
            self.animating = False
        else:
            self.current_val += diff * 0.2
            self.after(30, self._animate)
            
        extent = -180 * (self.current_val / 100)
        self.itemconfig(self.arc, extent=extent, outline=self.val_color)
        self.itemconfig(self.lbl, text=f"{int(self.current_val)}%")
