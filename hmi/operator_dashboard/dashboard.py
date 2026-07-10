"""
hmi/operator_dashboard/dashboard.py
===================================
High-level Operator Dashboard showing plant status and critical KPIs.
"""

import tkinter as tk
import collections
from gui.theme import BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, FONT_SUBTITLE, FONT_TITLE, FONT_LABEL_SM, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL
from gui.widgets import KPICard, StatusIndicator

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class OperatorDashboard(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        lbl = tk.Label(self, text="OPERATOR DASHBOARD", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_TITLE)
        lbl.pack(pady=10, anchor="w", padx=20)
        
        # 1. Top Band: Plant Status Summary
        self.frm_status = tk.Frame(self, bg=BG_SECONDARY, highlightthickness=1, highlightbackground=BORDER)
        self.frm_status.pack(fill="x", padx=20, pady=5)
        
        frm_indicators = tk.Frame(self.frm_status, bg=BG_SECONDARY)
        frm_indicators.pack(fill="x")
        
        self.status_indicators = {}
        status_keys = [("health", "Plant Health"), ("comms", "Communications"), ("watchdog", "Watchdog"), 
                       ("historian", "Historian"), ("scheduler", "Scheduler"), ("ai", "AI Engine")]
        
        for i, (key, title) in enumerate(status_keys):
            f = tk.Frame(frm_indicators, bg=BG_SECONDARY)
            f.pack(side="left", expand=True, fill="both", pady=(10, 5))
            ind = StatusIndicator(f, size=20)
            ind.pack(side="left", padx=(20, 10))
            tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(side="left")
            self.status_indicators[key] = ind
            
        self._build_horizontal_legend()
        # 2. Middle Band: KPI Cards
        self.frm_kpi = tk.Frame(self, bg=BG_PRIMARY)
        self.frm_kpi.pack(fill="x", padx=20, pady=10)
        
        self.kpis = {}
        # We will use 5 KPIs
        for i in range(5):
            self.frm_kpi.columnconfigure(i, weight=1, uniform="kpi")
            
        self.kpis["power"] = KPICard(self.frm_kpi, label="Total Production", unit="MW")
        self.kpis["power"].grid(row=0, column=0, sticky="nsew", padx=5)
        
        self.kpis["efficiency"] = KPICard(self.frm_kpi, label="System Efficiency", unit="%")
        self.kpis["efficiency"].grid(row=0, column=1, sticky="nsew", padx=5)
        
        self.kpis["wells"] = KPICard(self.frm_kpi, label="Active Wells", unit="Wells")
        self.kpis["wells"].grid(row=0, column=2, sticky="nsew", padx=5)
        
        self.kpis["pumps"] = KPICard(self.frm_kpi, label="Pump Availability", unit="%")
        self.kpis["pumps"].grid(row=0, column=3, sticky="nsew", padx=5)
        
        self.kpis["alarms"] = KPICard(self.frm_kpi, label="Active Alarms", unit="Count")
        self.kpis["alarms"].grid(row=0, column=4, sticky="nsew", padx=5)

        # 3. Bottom Band: Trend & Analytics
        self.frm_trend = tk.Frame(self, bg=BG_SECONDARY, highlightthickness=1, highlightbackground=BORDER)
        self.frm_trend.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.fig = Figure(figsize=(8, 3), dpi=100, facecolor=BG_SECONDARY)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_trend)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # History buffers for charts
        self._history_power = collections.deque(maxlen=60)
        self._history_eff = collections.deque(maxlen=60)
        
    def update_dashboard(self, status, health, highest_risk_eq, critical_alarm, power, energy, **kwargs):
        """
        Backward compatible signature. We parse kwargs for the new advanced fields,
        otherwise fallback to sensible defaults based on the old arguments.
        """
        # 1. Update Status Indicators
        # Backward compatibility mapping
        self.status_indicators["health"].set_status("CRITICAL" if health < 60 else ("WARNING" if health < 80 else "GOOD"))
        self.status_indicators["comms"].set_status(kwargs.get("status_comms", "GOOD"))
        self.status_indicators["watchdog"].set_status(kwargs.get("status_watchdog", "GOOD"))
        self.status_indicators["historian"].set_status(kwargs.get("status_historian", "GOOD"))
        self.status_indicators["scheduler"].set_status(kwargs.get("status_scheduler", "GOOD"))
        self.status_indicators["ai"].set_status(kwargs.get("status_ai", "GOOD"))
        
        # 2. Update KPIs
        self.kpis["power"].set_value(power)
        self.kpis["efficiency"].set_value(health, CLR_WARNING if health < 80 else TEXT_PRIMARY)
        self.kpis["wells"].set_value(kwargs.get("active_wells", 3))
        self.kpis["pumps"].set_value(kwargs.get("pump_avail", 100))
        
        alarm_cnt = kwargs.get("active_alarms", 1 if critical_alarm != "None" else 0)
        self.kpis["alarms"].set_value(alarm_cnt, CLR_CRITICAL if alarm_cnt > 0 else TEXT_PRIMARY)
        
        # 3. Update Trends
        self._history_power.append(power)
        self._history_eff.append(health)
        
        self.ax.clear()
        self.ax.set_facecolor(BG_SECONDARY)
        self.ax.tick_params(colors=TEXT_SECONDARY)
        for spine in self.ax.spines.values():
            spine.set_color(BORDER)
            
        self.ax.plot(self._history_power, color="#0ea5e9", label="Power (MW)", linewidth=2)
        
        ax2 = self.ax.twinx()
        ax2.plot(self._history_eff, color="#10b981", label="Efficiency (%)", linewidth=2, alpha=0.7, linestyle="--")
        ax2.tick_params(colors=TEXT_SECONDARY)
        ax2.spines["right"].set_color(BORDER)
        ax2.spines["top"].set_color(BG_SECONDARY)
        
        self.ax.set_title("Real-Time Plant Performance", color=TEXT_SECONDARY, pad=10)
        
        # Merge legends
        lines, labels = self.ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        self.ax.legend(lines + lines2, labels + labels2, loc="upper left", facecolor=BG_PRIMARY, edgecolor=BORDER, labelcolor=TEXT_PRIMARY)
        
        self.canvas.draw_idle()

    def _build_horizontal_legend(self):
        legend_container = tk.Frame(self.frm_status, bg=BG_SECONDARY)
        legend_container.pack(fill="x", padx=20, pady=(0, 10))
        
        # Create a row for the legend items, centered
        items_frm = tk.Frame(legend_container, bg=BG_SECONDARY)
        items_frm.pack(anchor="center")
        
        items = [
            ("Green", "Normal (Health ≥ 85%)", CLR_NORMAL),
            ("Yellow", "Warning (70–84%)", CLR_WARNING),
            ("Red", "Critical (60–69%)", CLR_CRITICAL),
            ("Diamond", "Emergency (< 60%)", CLR_CRITICAL)
        ]
        
        for shape, text, color in items:
            item_frm = tk.Frame(items_frm, bg=BG_SECONDARY)
            item_frm.pack(side="left", padx=15)
            
            icon_canvas = tk.Canvas(item_frm, width=16, height=16, bg=BG_SECONDARY, highlightthickness=0)
            icon_canvas.pack(side="left", pady=2)
            
            s = 12
            m = 2
            if shape in ["Green", "Yellow", "Red"]:
                icon_canvas.create_oval(m, m, s+m, s+m, fill=color, outline=BORDER, width=1)
            elif shape == "Diamond":
                cx, cy = m + s/2, m + s/2
                r = s/2
                icon_canvas.create_polygon(cx, cy-r, cx+r, cy, cx, cy+r, cx-r, cy, fill=color, outline=BORDER, width=1)
                
            tk.Label(item_frm, text=text, bg=BG_SECONDARY, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="left", padx=(5, 0))
            
        # Explanatory note
        note_text = "Health Score is calculated from AI risk analysis, sensor telemetry, alarm conditions, and equipment operating status."
        tk.Label(legend_container, text=note_text, bg=BG_SECONDARY, fg=TEXT_MUTED, font=("Segoe UI", 8, "italic")).pack(pady=(5, 0))
