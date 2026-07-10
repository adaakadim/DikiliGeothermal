"""
gui/kpi_dashboard.py
====================
Executive KPI and Operational Intelligence Dashboard.
"""

import tkinter as tk
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_LIGHT
from gui.theme import CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM, FONT_MONO_MD
from gui.i18n import tr
from gui.widgets import KPICard

class KPIDashboard(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.pack_propagate(False)
        self._build_ui()
        
    def _build_ui(self):
        # ─── Top Header ───
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text=tr("EXECUTIVE DASHBOARD - OPERATIONAL INTELLIGENCE"), 
                 bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(side="left", padx=15, pady=10)
                 
        # ─── Main Content (Left: KPIs & Intel, Right: Trends) ───
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=10, pady=5)
        
        left_panel = tk.Frame(content, bg=BG_PRIMARY)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_panel = tk.Frame(content, bg=BG_PRIMARY)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # --- Left Panel ---
        # 1. Executive Summary Cards
        summary_frame = tk.Frame(left_panel, bg=BG_PRIMARY)
        summary_frame.pack(fill="x", pady=5)
        
        self.kpis = {}
        self.kpis["health"] = KPICard(summary_frame, "Plant Health", "%", width=140)
        self.kpis["eff"] = KPICard(summary_frame, "Overall Efficiency", "%", width=140)
        self.kpis["risk"] = KPICard(summary_frame, "Overall AI Risk", "%", width=140)
        self.kpis["maint"] = KPICard(summary_frame, "Maint Readiness", "%", width=140)
        
        self.kpis["health"].pack(side="left", padx=5)
        self.kpis["eff"].pack(side="left", padx=5)
        self.kpis["risk"].pack(side="left", padx=5)
        self.kpis["maint"].pack(side="left", padx=5)
        
        # 2. Performance Scorecards
        scorecard_frame = tk.LabelFrame(left_panel, text=tr("Performance Scorecards"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        scorecard_frame.pack(fill="x", pady=10, ipady=5)
        
        self.scorecards = {}
        sc_names = ["Production Performance", "Energy Performance", "Equipment Reliability", "AI System Performance"]
        for i, name in enumerate(sc_names):
            lbl = tk.Label(scorecard_frame, text=name, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
            lbl.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            val = tk.Label(scorecard_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
            val.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            status = tk.Label(scorecard_frame, text="UNKNOWN", bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_LABEL_SM)
            status.grid(row=i, column=2, sticky="w", padx=10, pady=5)
            self.scorecards[name] = {"val": val, "status": status}
            
        # 3. Operational Intelligence
        intel_frame = tk.LabelFrame(left_panel, text=tr("Operational Intelligence"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        intel_frame.pack(fill="both", expand=True, pady=5)
        
        self.intel_labels = {}
        intel_keys = ["Highest Risk Equipment", "Lowest Health Equipment", "Lowest Efficiency Equipment", 
                      "Most Frequent Alarm Source", "Immediate Maintenance Needed", "Fastest Degrading Equipment"]
                      
        for i, key in enumerate(intel_keys):
            tk.Label(intel_frame, text=key, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).grid(row=i, column=0, sticky="w", padx=10, pady=6)
            val = tk.Label(intel_frame, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
            val.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            self.intel_labels[key] = val
            
        # --- Right Panel ---
        # 4. Trend Charts
        chart_frame = tk.Frame(right_panel, bg=BG_SECONDARY, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        chart_frame.pack(fill="both", expand=True, pady=(0, 10))
        tk.Label(chart_frame, text=tr("Historical KPI Trends"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(pady=5)
        
        plt.style.use("dark_background")
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.fig.patch.set_facecolor(BG_SECONDARY)
        
        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title("Health & Efficiency", color=TEXT_SECONDARY, fontsize=10)
        self.ax1.set_facecolor(BG_TERTIARY)
        self.ax1.tick_params(colors=TEXT_MUTED, labelsize=8)
        
        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_title("AI Risk & Readiness", color=TEXT_SECONDARY, fontsize=10)
        self.ax2.set_facecolor(BG_TERTIARY)
        self.ax2.tick_params(colors=TEXT_MUTED, labelsize=8)
        
        self.fig.tight_layout(pad=2.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # 5. Engineering Recommendations
        rec_frame = tk.LabelFrame(right_panel, text=tr("Plant-Wide Engineering Recommendations"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        rec_frame.pack(fill="x", pady=5)
        
        self.rec_text = tk.Text(rec_frame, height=5, bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, bd=0)
        self.rec_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def update_dashboard(self, kpi_data: dict, history: dict):
        if not kpi_data: return
        
        # Update KPIs
        health = kpi_data.get("Overall Plant Health (%)", 0)
        self.kpis["health"].set_value(health, color=CLR_NORMAL if health > 80 else CLR_WARNING)
        
        eff = kpi_data.get("Overall Efficiency (%)", 0)
        self.kpis["eff"].set_value(eff, color=CLR_NORMAL if eff > 80 else CLR_WARNING)
        
        risk = kpi_data.get("Overall AI Risk (%)", 0)
        self.kpis["risk"].set_value(risk, color=CLR_CRITICAL if risk > 70 else (CLR_WARNING if risk > 40 else CLR_NORMAL))
        
        maint = kpi_data.get("Maintenance Readiness Index (%)", 0)
        self.kpis["maint"].set_value(maint, color=CLR_NORMAL if maint > 70 else CLR_CRITICAL)
        
        # Update Scorecards
        prod_val = kpi_data.get("Equipment Availability (%)", 0)
        self.scorecards["Production Performance"]["val"].config(text=f"{prod_val:.1f} %")
        self.scorecards["Production Performance"]["status"].config(text="EXCELLENT" if prod_val > 95 else "NEEDS ATTENTION", fg=CLR_NORMAL if prod_val > 95 else CLR_WARNING)
        
        en_val = kpi_data.get("Energy Efficiency Score (%)", 0)
        self.scorecards["Energy Performance"]["val"].config(text=f"{en_val:.1f} %")
        self.scorecards["Energy Performance"]["status"].config(text="OPTIMAL" if en_val > 85 else "SUB-OPTIMAL", fg=CLR_NORMAL if en_val > 85 else CLR_WARNING)
        
        rel_val = kpi_data.get("Average Equipment Health (%)", 0)
        self.scorecards["Equipment Reliability"]["val"].config(text=f"{rel_val:.1f} %")
        self.scorecards["Equipment Reliability"]["status"].config(text="RELIABLE" if rel_val > 80 else "DEGRADING", fg=CLR_NORMAL if rel_val > 80 else CLR_WARNING)
        
        ai_val = kpi_data.get("Prediction Confidence Average (%)", 0)
        self.scorecards["AI System Performance"]["val"].config(text=f"{ai_val:.1f} %")
        self.scorecards["AI System Performance"]["status"].config(text="HIGH CONFIDENCE" if ai_val > 80 else "LEARNING", fg=CLR_NORMAL if ai_val > 80 else CLR_WARNING)
        
        # Update Operational Intelligence
        intel = kpi_data.get("Operational Intelligence", {})
        self.intel_labels["Highest Risk Equipment"].config(text=intel.get("Highest Risk Equipment", "---"))
        self.intel_labels["Lowest Health Equipment"].config(text=intel.get("Lowest Health Equipment", "---"))
        self.intel_labels["Lowest Efficiency Equipment"].config(text=intel.get("Lowest Efficiency Equipment", "---"))
        self.intel_labels["Most Frequent Alarm Source"].config(text=intel.get("Most Frequent Alarm Source", "---"))
        self.intel_labels["Immediate Maintenance Needed"].config(text=intel.get("Equipment Requiring Immediate Maintenance", "---"))
        self.intel_labels["Fastest Degrading Equipment"].config(text=intel.get("Fastest Degrading Equipment", "---"))
        
        # Update Recommendations
        recs = kpi_data.get("Engineering Recommendations", [])
        self.rec_text.delete(1.0, tk.END)
        for i, rec in enumerate(recs, 1):
            self.rec_text.insert(tk.END, f"{i}. {rec}\n")
            
        # Update Trends
        self.ax1.clear()
        self.ax2.clear()
        
        self.ax1.set_title("Health & Efficiency", color=TEXT_SECONDARY, fontsize=10)
        self.ax2.set_title("AI Risk & Readiness", color=TEXT_SECONDARY, fontsize=10)
        
        if history and len(history.get("Plant Health (%)", [])) > 0:
            x = list(range(len(history["Plant Health (%)"])))
            self.ax1.plot(x, history["Plant Health (%)"], color="#10b981", label="Plant Health")
            self.ax1.plot(x, history["Overall Efficiency (%)"], color="#3b82f6", label="Efficiency")
            self.ax1.legend(loc="upper right", fontsize=8)
            
            self.ax2.plot(x, history["Overall AI Risk (%)"], color="#ef4444", label="AI Risk")
            self.ax2.plot(x, history["Maintenance Readiness (%)"], color="#f59e0b", label="Maint Readiness")
            self.ax2.legend(loc="upper right", fontsize=8)
            
        self.canvas.draw()
