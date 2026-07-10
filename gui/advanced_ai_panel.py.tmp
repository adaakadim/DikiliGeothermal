"""
gui/advanced_ai_panel.py
========================
The ultimate Phase 4 Advanced AI Analytics Dashboard for the SCADA system.
Combines health indexes, feature importance, degradation trends, and
intelligent maintenance recommendations.
"""

from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, Any, List

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE, FONT_MONO_MD, FONT_TITLE
)

class AdvancedAICenterPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # ── Title Header ──
        hdr_frame = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        hdr_frame.pack(fill="x", pady=(0, 4))
        
        tk.Label(hdr_frame, text="DIKILI GEOTHERMAL AI CENTER",
                 bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE, anchor="center").pack(pady=4)

        # ── Grid Container ──
        self.container = tk.Frame(self, bg=BG_PRIMARY)
        self.container.pack(fill="both", expand=True)
        
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=1)
        
        # ── Left Column: Metrics ──
        left_col = tk.Frame(self.container, bg=BG_PRIMARY)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        self._build_kpi_box(left_col, "PLANT HEALTH", "health", "%", CLR_NORMAL)
        self._build_kpi_box(left_col, "PUMP FAILURE RISK", "risk", "%", CLR_WARNING)
        self._build_kpi_box(left_col, "AI CONFIDENCE", "conf", "%", TEXT_PRIMARY)
        
        # ── Right Column: Insights ──
        right_col = tk.Frame(self.container, bg=BG_PRIMARY)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        
        self._build_info_box(right_col, "MAIN RISK FACTOR", "risk_factor", "Normal Operation")
        self._build_info_box(right_col, "EQUIPMENT STATUS", "status", "NORMAL")
        self._build_info_box(right_col, "MAINTENANCE ADVICE", "advice", "Continue Monitoring", height=3)
        
        # ── Bottom Row: Trends & Components ──
        bottom_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        bottom_frame.pack(fill="x", pady=(4, 0))
        
        self._lbl_trend = tk.Label(bottom_frame, text="Trend: Gathering data...", bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_LABEL_SM, anchor="w")
        self._lbl_trend.pack(fill="x", padx=10, pady=4)

        self._lbl_components = tk.Label(bottom_frame, text="Pump: 100% | Motor: 100% | HX: 100%", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="w")
        self._lbl_components.pack(fill="x", padx=10, pady=(0, 4))

    def _build_kpi_box(self, parent, title, key, unit, color):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=(0, 4))
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(4, 0))
        val_lbl = tk.Label(f, text=f"--- {unit}", bg=BG_SECONDARY, fg=color, font=FONT_SUBTITLE)
        val_lbl.pack(pady=(0, 4))
        
        if not hasattr(self, '_kpi_labels'):
            self._kpi_labels = {}
        self._kpi_labels[key] = val_lbl

    def _build_info_box(self, parent, title, key, default_text, height=1):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=(0, 4))
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(4, 0))
        
        lbl = tk.Label(f, text=default_text, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, wraplength=160, justify="center")
        lbl.pack(pady=(0, 4))
        
        if not hasattr(self, '_info_labels'):
            self._info_labels = {}
        self._info_labels[key] = lbl

    def update_dashboard(self, 
                         health_indexes: Dict[str, float], 
                         failure_prob: float, 
                         confidence: float, 
                         top_features: List[Dict[str, Any]], 
                         maint_rec: Dict[str, Any], 
                         trend: Dict[str, Any]):
        """Injects Phase 4 backend data into the UI."""
        
        # Update KPI
        plant_h = health_indexes.get("Overall Plant Health", 100.0)
        self._kpi_labels["health"].config(text=f"{plant_h:.1f} %", fg=CLR_NORMAL if plant_h > 80 else CLR_CRITICAL)
        self._kpi_labels["risk"].config(text=f"{failure_prob:.1f} %", fg=CLR_CRITICAL if failure_prob > 40 else CLR_NORMAL)
        self._kpi_labels["conf"].config(text=f"{confidence:.1f} %", fg=CLR_WARNING if confidence < 75 else TEXT_PRIMARY)
        
        # Update Insights
        main_factor = top_features[0]["name"] if top_features else "N/A"
        self._info_labels["risk_factor"].config(text=f"{main_factor}\n({top_features[0]['weight']}% influence)" if top_features else "N/A")
        
        status = maint_rec.get("Current Status", "UNKNOWN")
        self._info_labels["status"].config(text=status, fg=CLR_CRITICAL if "MAINTENANCE" in status else (CLR_WARNING if "MONITORING" in status else CLR_NORMAL))
        
        actions = maint_rec.get("Recommended Actions", ["Continue Normal Operation"])
        advice_text = "\n".join([f"• {a}" for a in actions[:2]])
        self._info_labels["advice"].config(text=advice_text)
        
        # Update Trends
        trend_msg = f"Trend: {trend.get('Assessment', 'Stable')} (Change: {trend.get('Change', 0.0):+.1f}%)"
        self._lbl_trend.config(text=trend_msg)
        
        comp_msg = f"Pump: {health_indexes.get('Pump Health', 100.0):.0f}% | Motor: {health_indexes.get('Motor Health', 100.0):.0f}% | HX: {health_indexes.get('Heat Exchanger Health', 100.0):.0f}%"
        self._lbl_components.config(text=comp_msg)
