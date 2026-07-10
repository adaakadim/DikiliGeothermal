"""
hmi/diagnostics/diagnostics_panel.py
====================================
Engineering Diagnostics page showing system stats.
"""

import time
import tkinter as tk
from gui.theme import BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_SUBTITLE, FONT_MONO_MD

class DiagnosticsPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self._start_time = time.time()
        
        lbl = tk.Label(self, text="ENGINEERING DIAGNOSTICS", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        lbl.pack(pady=10, anchor="w", padx=20)
        
        self.stats_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.labels = {}
        self._add_stat("Uptime", "00:00:00")
        self._add_stat("AI Engine Latency", "--- ms")
        self._add_stat("Digital Twin Sync", "OFFLINE")
        self._add_stat("Memory Usage", "--- MB")
        self._add_stat("CPU Usage", "--- %")
        
    def _add_stat(self, name, default):
        row = tk.Frame(self.stats_frame, bg=BG_SECONDARY)
        row.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row, text=f"{name}:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Consolas", 12, "bold"), width=25, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=default, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_MONO_MD)
        lbl.pack(side="left")
        self.labels[name] = lbl
        
    def update_diagnostics(self, service: 'DiagnosticsService'):
        metrics = service.get_system_metrics()
        
        # Ensure all incoming metrics have a label row
        for name, value in metrics.items():
            if name not in self.labels:
                self._add_stat(name, str(value))
            self.labels[name].config(text=str(value))
