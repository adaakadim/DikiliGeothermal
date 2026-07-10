"""
gui/explainability_panel.py
===========================
Phase 5.2 XAI Panel for real-time SHAP analysis.
Displays human-readable explanations and an embedded Matplotlib Horizontal Bar Chart.
"""

from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, Any, List
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_LABEL_SM, FONT_SUBTITLE, FONT_MONO_SM, FONT_LABEL
)

class ExplainabilityPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # ── Header ──
        hdr = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="AI DECISION EXPLANATION", bg=BG_HEADER, fg="#a855f7", font=FONT_SUBTITLE).pack(pady=4)

        self.container = tk.Frame(self, bg=BG_PRIMARY)
        self.container.pack(fill="both", expand=True)
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=1)

        # ── Left Column: Textual Explanation ──
        left_col = tk.Frame(self.container, bg=BG_PRIMARY)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        # KPIs
        kpi_frame = tk.Frame(left_col, bg=BG_PRIMARY)
        kpi_frame.pack(fill="x")
        self._lbl_risk = self._build_kpi(kpi_frame, "Pump Failure Risk", "%", CLR_WARNING)
        self._lbl_conf = self._build_kpi(kpi_frame, "Prediction Confidence", "%", TEXT_PRIMARY)

        # Explanation boxes
        self._lbl_pos = self._build_info_box(left_col, "MAIN POSITIVE CONTRIBUTORS", "...")
        self._lbl_neg = self._build_info_box(left_col, "MAIN NEGATIVE CONTRIBUTORS", "...")
        self._lbl_overall = self._build_info_box(left_col, "OVERALL DECISION", "...", height=3)

        # ── Right Column: SHAP Chart ──
        right_col = tk.Frame(self.container, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        tk.Label(right_col, text="FEATURE CONTRIBUTION (SHAP)", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM).pack(pady=(4,0))

        self._fig = Figure(figsize=(4, 3), dpi=85)
        self._fig.patch.set_facecolor(BG_SECONDARY)
        # Increased left margin to 0.55 so long labels like "Heat Exchanger Inlet" fit
        self._fig.subplots_adjust(left=0.55, right=0.95, top=0.95, bottom=0.15)
        
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(BG_SECONDARY)
        self._format_ax()
        
        self._canvas = FigureCanvasTkAgg(self._fig, master=right_col)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_kpi(self, parent, title, unit, color):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.pack(side="left", fill="both", expand=True, padx=2, pady=(0, 4))
        # Use wraplength here to prevent "Prediction Confidence" from being cut
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, wraplength=100).pack(pady=(4, 0))
        val_lbl = tk.Label(f, text=f"--- {unit}", bg=BG_SECONDARY, fg=color, font=FONT_SUBTITLE)
        val_lbl.pack(pady=(0, 4))
        return val_lbl

    def _build_info_box(self, parent, title, default_text, height=1):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=(0, 4))
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(4, 0), anchor="w", padx=10)
        # Reduced wraplength from 280 to 200 so it doesn't clip on the right
        lbl = tk.Label(f, text=default_text, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, wraplength=200, justify="left", anchor="w")
        lbl.pack(fill="x", padx=10, pady=(0, 4))
        return lbl

    def _format_ax(self):
        self._ax.clear()
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.set_xlabel("SHAP Value (Impact on Risk)", color=TEXT_PRIMARY, fontsize=9)

    def update_explainability(self, xai_data: Dict[str, Any], risk: float, conf: float):
        """Updates the panel with SHAP outputs."""
        if not xai_data: return
        
        # 1. Update text fields
        self._lbl_risk.config(text=f"{risk:.1f} %", fg=CLR_CRITICAL if risk > 40 else CLR_NORMAL)
        self._lbl_conf.config(text=f"{conf:.1f} %")
        
        pos_list = "\n".join([f"• {x}" for x in xai_data.get("positive_factors", [])[:3]])
        neg_list = "\n".join([f"• {x}" for x in xai_data.get("negative_factors", [])[:3]])
        
        self._lbl_pos.config(text=pos_list if pos_list else "None")
        self._lbl_neg.config(text=neg_list if neg_list else "None")
        self._lbl_overall.config(text=xai_data.get("explanation_text", "No explanation available."))
        
        # 2. Update SHAP Chart
        self._format_ax()
        
        ranked = xai_data.get("ranked_features", {})
        top_overall = ranked.get("top_overall", [])
        
        if top_overall:
            # We want to display the largest absolute values at the top, so we reverse the top N
            # to plot them from bottom-to-top in matplotlib.
            plot_data = list(reversed(top_overall[:5]))
            
            names = []
            vals = []
            colors = []
            
            from analytics.ai.random_forest.explainability.explanation_generator import ExplanationGenerator
            
            for f in plot_data:
                name = ExplanationGenerator.FEATURE_MAP.get(f["feature"], f["feature"].replace('_', ' '))
                val = f["value"]
                names.append(name.title())
                vals.append(val)
                colors.append("#ef4444" if val > 0 else "#3b82f6") # Red for risk+, Blue for risk-
                
            y_pos = range(len(names))
            self._ax.barh(y_pos, vals, color=colors, height=0.6)
            self._ax.set_yticks(y_pos)
            self._ax.set_yticklabels(names)
            
            # Add a zero line
            self._ax.axvline(0, color=BORDER, linewidth=1, linestyle="--")
            
        self._canvas.draw_idle()
