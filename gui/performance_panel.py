"""
gui/performance_panel.py
========================
Displays advanced AI monitoring metrics including running average confidence,
reliability status, and top operational features driving the model.
"""

from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, Any, List

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE, FONT_MONO_MD
)

class AIPerformancePanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # Header
        hdr = tk.Label(self, text="  AI PERFORMANCE MONITORING",
                       bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL, anchor="w")
        hdr.pack(fill="x", pady=(0, 2))

        self.container = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.container.pack(fill="both", expand=True, pady=2)
        
        # 1. Prediction History row
        self._lbl_hist = tk.Label(self.container, text="Prediction History: Tracking last 100", 
                                  bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w")
        self._lbl_hist.pack(fill="x", padx=10, pady=(8, 2))
        
        # 2. Avg Confidence & Reliability
        stat_frame = tk.Frame(self.container, bg=BG_SECONDARY)
        stat_frame.pack(fill="x", padx=10, pady=2)
        
        stat_frame.columnconfigure(0, weight=1)
        stat_frame.columnconfigure(1, weight=1)
        stat_frame.columnconfigure(2, weight=1)
        stat_frame.columnconfigure(3, weight=1)
        
        tk.Label(stat_frame, text="Avg Confidence:", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).grid(row=0, column=0, sticky="w")
        self._lbl_avg_conf = tk.Label(stat_frame, text="--- %", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self._lbl_avg_conf.grid(row=0, column=1, sticky="w")
        
        tk.Label(stat_frame, text="Reliability:", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).grid(row=0, column=2, sticky="e")
        self._lbl_reliability = tk.Label(stat_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self._lbl_reliability.grid(row=0, column=3, sticky="e")
        
        # Divider
        tk.Frame(self.container, bg=BORDER, height=1).pack(fill="x", padx=10, pady=6)
        
        # 3. Top Features
        tk.Label(self.container, text="Most Important Features:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="w").pack(fill="x", padx=10, pady=(0, 2))
        
        self._lbl_features = tk.Label(self.container, text="Loading...", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="w", justify="left")
        self._lbl_features.pack(fill="x", padx=10, pady=(0, 4))
        
        # 4. Explainability Support
        tk.Label(self.container, text="AI Decision Support:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="w").pack(fill="x", padx=10, pady=(4, 0))
        
        self._lbl_explain = tk.Label(self.container, text="Waiting for prediction...", bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_MONO_SM, anchor="w", justify="left", wraplength=200)
        self._lbl_explain.pack(fill="x", padx=10, pady=(2, 8))

    def update_performance(self, confidence_stats: Dict[str, Any], top_features: List[Dict[str, Any]], explanation: Dict[str, List[str]]):
        """Updates the panel with the latest stats."""
        # Update confidence
        avg = confidence_stats.get("average", 0.0)
        self._lbl_avg_conf.config(text=f"{avg:.1f} %")
        
        status = confidence_stats.get("status", "UNKNOWN")
        rel_color = CLR_NORMAL if status == "GOOD" else CLR_WARNING
        self._lbl_reliability.config(text=status, fg=rel_color)
        
        # Update top features
        if top_features:
            features_text = "\n".join([f"• {f['name']}: {f['weight']}%" for f in top_features])
            self._lbl_features.config(text=features_text)
            
        # Update explanation
        inc = explanation.get("increasing", [])
        norm = explanation.get("normal", [])
        
        exp_text = ""
        if inc and "No immediate active risk" not in inc[0]:
            exp_text += "Risk Increasing Factors:\n" + "\n".join([f"⚠ {f}" for f in inc]) + "\n"
        if norm:
            exp_text += "Normal Factors:\n" + "\n".join([f"✓ {f}" for f in norm[:2]])
            
        if not exp_text:
            exp_text = "✓ Stable operation"
            
        self._lbl_explain.config(text=exp_text, fg=CLR_WARNING if inc and "No immediate active risk" not in inc[0] else CLR_NORMAL)
