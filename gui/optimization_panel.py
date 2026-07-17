"""
gui/optimization_panel.py
=========================
Intelligent Energy & Process Optimization Dashboard.
Displays overall plant efficiency, lowest efficiency equipment, 
and AI-generated actionable recommendations.
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
    FONT_SUBTITLE, FONT_LABEL, FONT_MONO_MD, FONT_MONO_LG
)
from gui.i18n import tr

logger = logging.getLogger(__name__)

class OptimizationPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        # 1. Header
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        lbl_title = tk.Label(header, text=tr("ENERGY & PROCESS OPTIMIZATION ENGINE"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        lbl_title.pack(pady=(10, 5), anchor="w", padx=20)
        
        # 2. KPI Summary Frame
        self.kpi_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.kpi_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_overall_eff = self._create_kpi_box(self.kpi_frame, "Overall Plant Efficiency", 0, 0)
        self.lbl_hx_eff = self._create_kpi_box(self.kpi_frame, "Heat Exchanger Efficiency", 0, 1)
        self.lbl_pump_eff = self._create_kpi_box(self.kpi_frame, "Pump Efficiency", 0, 2)
        self.lbl_plant_load = self._create_kpi_box(self.kpi_frame, "Plant Load", 0, 3)
        self.lbl_sec = self._create_kpi_box(self.kpi_frame, "Specific Energy Consumption", 0, 4)
        
        # 3. Recommendations Table
        self.rec_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.rec_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        tk.Label(self.rec_frame, text=tr("Optimization Opportunities & Recommendations"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(anchor="w", padx=10, pady=5)
        
        # Treeview for recommendations
        columns = ("Equipment", "Efficiency", "Target", "Suggestion", "Est. Improvement", "Priority")
        self.tree = ttk.Treeview(self.rec_frame, columns=columns, show="headings", height=5, style="Opt.Treeview")
        
        style = ttk.Style()
        style.configure("Opt.Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=40, font=FONT_LABEL)
        style.map("Opt.Treeview", background=[("selected", BG_HEADER)])
        
        self.tree.heading("Equipment", text=tr("Equipment"))
        self.tree.column("Equipment", width=100, anchor="w")
        
        self.tree.heading("Efficiency", text=tr("Current Eff."))
        self.tree.column("Efficiency", width=100, anchor="center")
        
        self.tree.heading("Target", text=tr("Target Eff."))
        self.tree.column("Target", width=100, anchor="center")
        
        self.tree.heading("Suggestion", text=tr("Optimization Suggestion"))
        self.tree.column("Suggestion", width=800, anchor="w")
        
        self.tree.heading("Est. Improvement", text=tr("Est. Improvement"))
        self.tree.column("Est. Improvement", width=120, anchor="center")
        
        self.tree.heading("Priority", text=tr("Priority"))
        self.tree.column("Priority", width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 4. History Trend Graph
        self._build_history_graph()
        
    def _create_kpi_box(self, parent, title, row, col):
        frame = tk.Frame(parent, bg=BG_SECONDARY, padx=10, pady=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=5)
        parent.grid_columnconfigure(col, weight=1)
        
        tk.Label(frame, text=tr(title), bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, wraplength=120, justify="center").pack()
        lbl_val = tk.Label(frame, text="0.0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_LG)
        lbl_val.pack()
        return lbl_val
        
    def _build_history_graph(self):
        graph_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        graph_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        
        tk.Label(graph_frame, text=tr("Historical Efficiency Trend"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=(5,0), anchor="w", padx=10)
        
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

    def update_dashboard(self, opt_data: Dict[str, Any]):
        """Update the dashboard with latest optimization insights."""
        kpis = opt_data.get("KPIs", {})
        
        # Update KPIs
        self.lbl_overall_eff.config(text=f"{kpis.get('Overall Plant Efficiency (%)', 0):.1f}%")
        self.lbl_hx_eff.config(text=f"{kpis.get('Heat Exchanger Efficiency (%)', 0):.1f}%")
        self.lbl_pump_eff.config(text=f"{kpis.get('Pump Efficiency (%)', 0):.1f}%")
        self.lbl_plant_load.config(text=f"{kpis.get('Plant Load (%)', 0):.1f}%")
        
        sec = kpis.get("Specific Energy Consumption (kWh/MWh_th)", 0)
        self.lbl_sec.config(text=f"{sec:.1f}")
        
        # Color coding for Overall Eff
        overall = kpis.get('Overall Plant Efficiency (%)', 0)
        if overall < 75:
            self.lbl_overall_eff.config(fg="#ff4444")
        elif overall < 85:
            self.lbl_overall_eff.config(fg="#ffaa00")
        else:
            self.lbl_overall_eff.config(fg="#10b981")
            
        # Update Recommendations
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        recs = opt_data.get("Recommendations", [])
        for rec in recs:
            self.tree.insert("", "end", values=(
                rec.get("Equipment", "Unknown"),
                f"{rec.get('Efficiency', 0):.1f}%",
                f"{rec.get('Target Efficiency', 0):.1f}%",
                rec.get("Suggestion", ""),
                rec.get("Estimated Improvement", ""),
                rec.get("Priority", "")
            ))
            
    def update_history_graph(self, history_manager):
        """Update the historical efficiency chart."""
        if not self.winfo_ismapped(): return
        
        self._ax.clear()
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(BORDER)
        self._ax.spines["bottom"].set_color(BORDER)
        
        self._ax.set_ylabel(tr("Efficiency (%)"), color=TEXT_SECONDARY, fontsize=9)
        
        overall = history_manager.get_trend("overall_efficiency")
        pump = history_manager.get_trend("pump_efficiency")
        hx = history_manager.get_trend("hx_efficiency")
        
        if overall:
            self._ax.plot(overall, label="Overall Plant", color="#10b981", linewidth=2)
        if pump:
            self._ax.plot(pump, label="Pump", color="#3b82f6", linewidth=1.5, linestyle="--")
        if hx:
            self._ax.plot(hx, label="Heat Exchanger", color="#f59e0b", linewidth=1.5, linestyle="--")
            
        if overall or pump or hx:
            legend = self._ax.legend(loc="lower right", frameon=False, fontsize=8)
            for text in legend.get_texts():
                text.set_color(TEXT_PRIMARY)
                
        self._canvas.draw()
