"""
hmi/operator_dashboard/dashboard.py
===================================
High-level Operator Dashboard showing plant status and critical KPIs.
"""

import tkinter as tk
import collections
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, FONT_SUBTITLE, FONT_TITLE, FONT_LABEL_SM, FONT_LABEL, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_RUNNING, CLR_STOPPED
from gui.widgets import KPICard, StatusIndicator, GaugeWidget
import matplotlib.ticker as ticker

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
        
        self.frm_status.columnconfigure(0, weight=3)
        self.frm_status.columnconfigure(1, weight=1)
        
        frm_indicators = tk.Frame(self.frm_status, bg=BG_SECONDARY)
        frm_indicators.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        frm_health = tk.Frame(self.frm_status, bg=BG_SECONDARY)
        frm_health.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.health_gauge = GaugeWidget(frm_health, label="Plant Health", unit="%", min_val=0, max_val=100, warn_lo=60, warn_hi=85, crit_lo=0, crit_hi=60, size=110)
        self.health_gauge.pack(anchor="center", pady=10)
        
        self.status_indicators = {}
        status_keys = [("health", "Plant Health"), ("comms", "Communications"), ("watchdog", "Watchdog"), 
                       ("historian", "Historian"), ("scheduler", "Scheduler"), ("ai", "AI Engine")]
        
        for i in range(3): frm_indicators.columnconfigure(i, weight=1)
        
        for i, (key, title) in enumerate(status_keys):
            row = i // 3
            col = i % 3
            card = tk.Frame(frm_indicators, bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            
            top_frm = tk.Frame(card, bg=BG_TERTIARY)
            top_frm.pack(fill="x", padx=10, pady=(8, 2))
            tk.Label(top_frm, text=title, bg=BG_TERTIARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left")
            
            bot_frm = tk.Frame(card, bg=BG_TERTIARY)
            bot_frm.pack(fill="x", padx=10, pady=(2, 8))
            ind = StatusIndicator(bot_frm, size=16)
            ind.pack(side="left", padx=(0, 6))
            lbl_stat = tk.Label(bot_frm, text="UNKNOWN", bg=BG_TERTIARY, fg=TEXT_MUTED, font=FONT_LABEL)
            lbl_stat.pack(side="left")
            
            self.status_indicators[key] = {"ind": ind, "lbl": lbl_stat, "card": card}
            
        # 2. Middle Band: KPI Cards
        self.frm_kpi = tk.Frame(self, bg=BG_PRIMARY)
        self.frm_kpi.pack(fill="x", padx=20, pady=10)
        
        self.kpis = {}
        for i in range(5):
            self.frm_kpi.columnconfigure(i, weight=1, uniform="kpi")
            
        self.kpis["power"] = KPICard(self.frm_kpi, label="Total Production", unit="MW", icon="⚡")
        self.kpis["power"].grid(row=0, column=0, sticky="nsew", padx=10)
        
        self.kpis["efficiency"] = KPICard(self.frm_kpi, label="System Efficiency", unit="%", icon="⟳")
        self.kpis["efficiency"].grid(row=0, column=1, sticky="nsew", padx=10)
        
        self.kpis["wells"] = KPICard(self.frm_kpi, label="Active Wells", unit="Wells", icon="🌊")
        self.kpis["wells"].grid(row=0, column=2, sticky="nsew", padx=10)
        
        self.kpis["pumps"] = KPICard(self.frm_kpi, label="Pump Availability", unit="%", icon="⚙")
        self.kpis["pumps"].grid(row=0, column=3, sticky="nsew", padx=10)
        
        self.kpis["alarms"] = KPICard(self.frm_kpi, label="Active Alarms", unit="Count", icon="⚠")
        self.kpis["alarms"].grid(row=0, column=4, sticky="nsew", padx=10)

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
        def _set_stat(key, health_str, text_str):
            color_map = {"GOOD": CLR_RUNNING, "WARNING": CLR_WARNING, "CRITICAL": CLR_CRITICAL, "OFFLINE": CLR_STOPPED}
            c = color_map.get(health_str, CLR_STOPPED)
            self.status_indicators[key]["ind"].set_status(health_str)
            self.status_indicators[key]["lbl"].config(text=text_str, fg=c)
            
        _set_stat("health", "CRITICAL" if health < 60 else ("WARNING" if health < 80 else "GOOD"), "HEALTHY" if health >= 80 else "DEGRADED")
        _set_stat("comms", kwargs.get("status_comms", "GOOD"), "CONNECTED" if kwargs.get("status_comms", "GOOD") == "GOOD" else "DISCONNECTED")
        _set_stat("watchdog", kwargs.get("status_watchdog", "GOOD"), "ONLINE" if kwargs.get("status_watchdog", "GOOD") == "GOOD" else "OFFLINE")
        _set_stat("historian", kwargs.get("status_historian", "GOOD"), "RUNNING" if kwargs.get("status_historian", "GOOD") == "GOOD" else "STOPPED")
        _set_stat("scheduler", kwargs.get("status_scheduler", "GOOD"), "RUNNING" if kwargs.get("status_scheduler", "GOOD") == "GOOD" else "STOPPED")
        _set_stat("ai", kwargs.get("status_ai", "GOOD"), "ONLINE" if kwargs.get("status_ai", "GOOD") == "GOOD" else "OFFLINE")
        
        self.health_gauge.set_value(health)
        
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
        
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_SECONDARY)
        self.ax.tick_params(colors=TEXT_SECONDARY)
        for spine in self.ax.spines.values():
            spine.set_color(BORDER)
            
        self.ax.plot(self._history_power, color="#0ea5e9", label="Power", linewidth=2.5, antialiased=True)
        self.ax.yaxis.set_major_locator(ticker.MaxNLocator(6))
        
        def _power_eng_fmt(x, pos):
            if x >= 1.0: return f"{x:.1f} MW"
            if x >= 0.001: return f"{x*1000:.1f} kW"
            return f"{x*1000000:.1f} W"
            
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(_power_eng_fmt))
        self.ax.grid(True, linestyle="--", alpha=0.2, color=TEXT_MUTED)
        
        ax2 = self.ax.twinx()
        ax2.plot(self._history_eff, color="#10b981", label="Efficiency (%)", linewidth=2.5, alpha=0.8, antialiased=True)
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(6))
        ax2.tick_params(colors=TEXT_SECONDARY)
        for spine in ax2.spines.values(): spine.set_color(BORDER)
        ax2.spines["top"].set_color(BG_SECONDARY)
        
        self.ax.set_title("Real-Time Plant Performance", color=TEXT_SECONDARY, pad=20, fontdict={'fontsize': 14, 'fontweight': 'bold'})
        
        lines, labels = self.ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        self.ax.legend(lines + lines2, labels + labels2, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=False, labelcolor=TEXT_PRIMARY)
        
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.82, bottom=0.1)
        
        self.canvas.draw_idle()
