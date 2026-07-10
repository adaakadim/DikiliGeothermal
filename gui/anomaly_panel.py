"""
gui/anomaly_panel.py
====================
AI Anomaly Detection & Root Cause Analysis Dashboard.
Displays anomaly score, status, root causes, affected equipment,
and historical anomaly trend.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    FONT_SUBTITLE, FONT_LABEL, FONT_MONO_MD, FONT_MONO_LG, FONT_MONO_XL,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL
)
from gui.i18n import tr

logger = logging.getLogger(__name__)

# Status colors
_STATUS_COLORS = {
    "Normal": "#10b981",
    "Minor": "#f59e0b",
    "Moderate": "#f97316",
    "Severe": "#ef4444",
}


class AnomalyPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # 1. Header
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        tk.Label(header, text=tr("AI ANOMALY DETECTION & ROOT CAUSE ANALYSIS"),
                 bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(
            pady=(10, 5), anchor="w", padx=20)

        # 2. Top row: Score gauge + Status + Affected Equipment
        top_row = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        top_row.pack(fill="x", padx=20, pady=10)

        # Anomaly Score
        score_frame = tk.Frame(top_row, bg=BG_SECONDARY, padx=20, pady=15)
        score_frame.pack(side="left", fill="y")
        tk.Label(score_frame, text=tr("Anomaly Score"), bg=BG_SECONDARY,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack()
        self.lbl_score = tk.Label(score_frame, text="0.0", bg=BG_SECONDARY,
                                  fg="#10b981", font=FONT_MONO_XL)
        self.lbl_score.pack()

        # Status
        status_frame = tk.Frame(top_row, bg=BG_SECONDARY, padx=20, pady=15)
        status_frame.pack(side="left", fill="y")
        tk.Label(status_frame, text=tr("Status"), bg=BG_SECONDARY,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack()
        self.lbl_status = tk.Label(status_frame, text="Normal", bg=BG_SECONDARY,
                                   fg="#10b981", font=FONT_MONO_LG)
        self.lbl_status.pack()

        # Affected Equipment
        eq_frame = tk.Frame(top_row, bg=BG_SECONDARY, padx=20, pady=15)
        eq_frame.pack(side="left", fill="y")
        tk.Label(eq_frame, text=tr("Affected Equipment"), bg=BG_SECONDARY,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack()
        self.lbl_affected = tk.Label(eq_frame, text="None", bg=BG_SECONDARY,
                                     fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_affected.pack()

        # Confidence
        conf_frame = tk.Frame(top_row, bg=BG_SECONDARY, padx=20, pady=15)
        conf_frame.pack(side="left", fill="y")
        tk.Label(conf_frame, text=tr("AI Confidence"), bg=BG_SECONDARY,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack()
        self.lbl_confidence = tk.Label(conf_frame, text="0.0%", bg=BG_SECONDARY,
                                       fg=TEXT_PRIMARY, font=FONT_MONO_LG)
        self.lbl_confidence.pack()

        # 3. Root Cause Analysis
        rca_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        rca_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(rca_frame, text=tr("Root Cause Analysis"), bg=BG_SECONDARY,
                 fg=TEXT_PRIMARY, font=FONT_LABEL).pack(anchor="w", padx=10, pady=5)

        self.rca_grid = tk.Frame(rca_frame, bg=BG_SECONDARY)
        self.rca_grid.pack(fill="x", padx=10, pady=(0, 10))

        # Primary / Secondary / Tertiary labels
        for i, rank in enumerate(["Primary Contributor", "Secondary Contributor", "Third Contributor"]):
            tk.Label(self.rca_grid, text=tr(rank), bg=BG_SECONDARY, fg=TEXT_PRIMARY,
                     font=FONT_SUBTITLE, width=25, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")

        self.lbl_primary = tk.Label(self.rca_grid, text="---", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, anchor="w")
        self.lbl_primary.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.lbl_secondary = tk.Label(self.rca_grid, text="---", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, anchor="w")
        self.lbl_secondary.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.lbl_tertiary = tk.Label(self.rca_grid, text="---", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, anchor="w")
        self.lbl_tertiary.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        # Explanation
        tk.Label(rca_frame, text=tr("Engineering Explanation"), bg=BG_SECONDARY,
                 fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(anchor="w", padx=10)
        self.lbl_explanation = tk.Label(rca_frame, text="All parameters within normal ranges.",
                                        bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL,
                                        wraplength=900, justify="left", anchor="w")
        self.lbl_explanation.pack(anchor="w", padx=10, pady=(0, 10))

        # Recommendation
        rec_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        rec_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(rec_frame, text=tr("Recommended Action"), bg=BG_SECONDARY,
                 fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(anchor="w", padx=10, pady=5)
        self.lbl_recommendation = tk.Label(rec_frame, text="Continue normal operation.",
                                            bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL,
                                            wraplength=900, justify="left", anchor="w")
        self.lbl_recommendation.pack(anchor="w", padx=10, pady=(0, 10))

        # 4. History Trend Graph
        self._build_history_graph()

    def _build_history_graph(self):
        graph_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        graph_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        tk.Label(graph_frame, text=tr("Anomaly Score Trend"), bg=BG_SECONDARY,
                 fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=(5, 0), anchor="w", padx=10)

        self._fig = Figure(figsize=(8, 2.0), dpi=85)
        self._fig.patch.set_facecolor(BG_SECONDARY)
        self._fig.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.22)

        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)

        self._canvas = FigureCanvasTkAgg(self._fig, master=graph_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_anomaly(self, anomaly_data: Dict[str, Any]):
        """Update the anomaly panel with latest detection results."""
        score = anomaly_data.get("Anomaly Score", 0.0)
        status = anomaly_data.get("Status", "Normal")
        color = _STATUS_COLORS.get(status, "#10b981")

        self.lbl_score.config(text=f"{score:.1f}", fg=color)
        self.lbl_status.config(text=status, fg=color)
        self.lbl_affected.config(text=anomaly_data.get("Affected Equipment", "None"))
        self.lbl_confidence.config(text=f"{anomaly_data.get('Confidence', 0.0):.1f}%")

        # Root Cause
        rca = anomaly_data.get("Root Cause", {})
        self.lbl_primary.config(text=rca.get("primary", "---"))
        self.lbl_secondary.config(text=rca.get("secondary", "---"))
        self.lbl_tertiary.config(text=rca.get("tertiary", "---"))
        self.lbl_explanation.config(text=rca.get("explanation", "All parameters within normal ranges."))

        self.lbl_recommendation.config(text=anomaly_data.get("Recommendation", "Continue normal operation."))

    def update_history_graph(self, score_trend: List[float]):
        """Update the anomaly score trend chart."""
        self._ax.clear()
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)

        self._ax.set_ylabel(tr("Score"), color=TEXT_SECONDARY, fontsize=9)

        if score_trend:
            self._ax.plot(score_trend, color="#3b82f6", linewidth=2, label="Anomaly Score")
            # Draw threshold lines
            self._ax.axhline(y=25, color="#f59e0b", linewidth=1, linestyle="--", alpha=0.5)
            self._ax.axhline(y=50, color="#f97316", linewidth=1, linestyle="--", alpha=0.5)
            self._ax.axhline(y=75, color="#ef4444", linewidth=1, linestyle="--", alpha=0.5)
            self._ax.set_ylim(0, 105)

        self._canvas.draw()
