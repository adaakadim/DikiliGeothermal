"""
hmi/event_timeline/event_viewer.py
==================================
Chronological event viewer.
"""

import tkinter as tk
import tkinter.ttk as ttk
from gui.theme import BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_SUBTITLE

class EventViewerPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        lbl = tk.Label(self, text="EVENT TIMELINE", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(pady=10, anchor="w", padx=20)
        
        columns = ("Timestamp", "Level", "Message")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", style="Alarm.Treeview", height=20)
        
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.heading("Level", text="Level")
        self.tree.heading("Message", text="Message")
        
        self.tree.column("Timestamp", width=150)
        self.tree.column("Level", width=100)
        self.tree.column("Message", width=600)
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._memory = []
        
    def add_event(self, timestamp: str, level: str, message: str):
        self._memory.insert(0, (timestamp, level, message))
        if len(self._memory) > 1000:
            self._memory.pop()
            
        self.tree.insert("", 0, values=(timestamp, level, message), tags=(level,))
        
        self.tree.tag_configure("INFO", foreground="#9ca3af")
        self.tree.tag_configure("WARN", foreground="#fb923c")
        self.tree.tag_configure("CRIT", foreground="#f87171")
