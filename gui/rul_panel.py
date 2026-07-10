"""
gui/rul_panel.py
================
Remaining Useful Life (RUL) Panel for the SCADA HMI.
Displays the RUL, Maintenance Priority, and Confidence for monitored equipment.
"""

import tkinter as tk
import logging
from tkinter import ttk
from typing import Dict, Any, List

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    FONT_SUBTITLE, FONT_LABEL, FONT_MONO_MD
)
from gui.i18n import tr

logger = logging.getLogger(__name__)

class RULPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        
        lbl_title = tk.Label(header, text=tr("REMAINING USEFUL LIFE (RUL) ESTIMATES"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        lbl_title.pack(pady=(10, 5), anchor="w", padx=20)
        
        self.table_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.table_frame.pack(fill="x", padx=20, pady=10)
        
        # Headers
        self._build_headers()
        
        # Rows
        self.row_widgets = {}
        
        # History Graph
        self._build_history_graph()
        
    def _build_history_graph(self):
        graph_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        graph_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        tk.Label(graph_frame, text=tr("Historical Degradation Trend (RUL)"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=(5,0), anchor="w", padx=10)
        
        self._fig = Figure(figsize=(8, 2.5), dpi=85)
        self._fig.patch.set_facecolor(BG_SECONDARY)
        self._fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.20)
        
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)
        
        self._canvas = FigureCanvasTkAgg(self._fig, master=graph_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def _build_headers(self):
        columns = [
            (tr("Equipment"), 12),
            (tr("RUL (Hours)"), 12),
            (tr("Days Left"), 10),
            (tr("Confidence"), 12),
            (tr("Degradation"), 12),
            (tr("Maintenance Status"), 35),
            (tr("Priority"), 12)
        ]
        
        for i, (text, width) in enumerate(columns):
            lbl = tk.Label(self.table_frame, text=text, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, width=width, anchor="w")
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
    def update_rul_data(self, rul_results: Dict[str, Dict[str, Any]]):
        """
        Update the table with new RUL estimations.
        """
        for eq_id, data in rul_results.items():
            if eq_id not in self.row_widgets:
                self._add_row(eq_id)
                
            self._update_row(eq_id, data)
            
    def update_history_graph(self, history_data: Dict[str, List[float]]):
        """Update the historical degradation chart with RUL trend lines."""
        self._ax.clear()
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)
        
        self._ax.set_ylabel(tr("RUL (Hours)"), color=TEXT_SECONDARY, fontsize=9)
        
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"]
        idx = 0
        
        for eq_id, trend in history_data.items():
            if not trend: continue
            c = colors[idx % len(colors)]
            self._ax.plot(trend, label=eq_id, color=c, linewidth=2)
            idx += 1
            
        if idx > 0:
            legend = self._ax.legend(loc="upper right", frameon=False, fontsize=8)
            for text in legend.get_texts():
                text.set_color(TEXT_PRIMARY)
                
        self._canvas.draw()
            
    def _add_row(self, eq_id: str):
        row_idx = len(self.row_widgets) + 1
        widgets = {}
        
        # Equipment
        widgets["Equipment"] = tk.Label(self.table_frame, text=eq_id, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=12, anchor="w")
        widgets["Equipment"].grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
        
        # RUL
        widgets["RUL"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=12, anchor="w")
        widgets["RUL"].grid(row=row_idx, column=1, padx=5, pady=2, sticky="w")
        
        # Days
        widgets["Days"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=10, anchor="w")
        widgets["Days"].grid(row=row_idx, column=2, padx=5, pady=2, sticky="w")
        
        # Confidence
        widgets["Confidence"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=12, anchor="w")
        widgets["Confidence"].grid(row=row_idx, column=3, padx=5, pady=2, sticky="w")
        
        # Degradation
        widgets["Degradation"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=12, anchor="w")
        widgets["Degradation"].grid(row=row_idx, column=4, padx=5, pady=2, sticky="w")
        
        # Maintenance Status
        widgets["Status"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=35, anchor="w")
        widgets["Status"].grid(row=row_idx, column=5, padx=5, pady=2, sticky="w")
        
        # Priority
        widgets["Priority"] = tk.Label(self.table_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, width=12, anchor="w")
        widgets["Priority"].grid(row=row_idx, column=6, padx=5, pady=2, sticky="w")
        
        self.row_widgets[eq_id] = widgets
        
    def _update_row(self, eq_id: str, data: Dict[str, Any]):
        w = self.row_widgets[eq_id]
        
        rul_val = data["Remaining Useful Life (Hours)"]
        w["RUL"].config(text=f"{rul_val:.1f}")
        
        days_val = data.get("Estimated Remaining Days", 0)
        w["Days"].config(text=f"{days_val:.1f} d")
        
        # Color coding for RUL
        if rul_val < 100.0:
            w["RUL"].config(fg="#ff4444") # Red
        elif rul_val < 500.0:
            w["RUL"].config(fg="#ffaa00") # Orange
        else:
            w["RUL"].config(fg=TEXT_PRIMARY)
            
        w["Confidence"].config(text=f"{data['Confidence (%)']:.1f}%")
        w["Degradation"].config(text=data["Current Degradation"])
        w["Status"].config(text=data["Maintenance Status"])
        
        pri = data["Maintenance Priority"]
        w["Priority"].config(text=pri)
        if pri == "Critical":
            w["Priority"].config(fg="#ff4444", font=("Consolas", 11, "bold"))
        elif pri == "High":
            w["Priority"].config(fg="#ffaa00", font=("Consolas", 11, "bold"))
        elif pri == "Medium":
            w["Priority"].config(fg="#ffff00", font=("Consolas", 11, "normal"))
        else:
            w["Priority"].config(fg=TEXT_PRIMARY, font=FONT_MONO_MD)
