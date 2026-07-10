"""
hmi/trend_workspace/trend_detail_panel.py
=========================================
The full view panel for an expanded trend chart.
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from datetime import datetime, timedelta
import logging
import os

from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_SUBTITLE, FONT_LABEL, BORDER, WELL_COLORS
from gui.trend_detail_chart import TrendDetailChartPanel

logger = logging.getLogger("TrendDetailUI")

# Import the specs to find the correct tuple
from gui.trend_charts import _T_HI, _T_LO, _P_LO, _Q_LO, _RISK_WARN, _RISK_CRIT, CLR_WARNING, CLR_CRITICAL
_SPECS = {
    "temp":   ("temp",   "Temperature",      "°C",   (70, 112), [(_T_HI, CLR_CRITICAL), (100.0, CLR_WARNING)]),
    "pres":   ("pres",   "Pressure",         "bar",  (2, 13),   [(_P_LO, CLR_WARNING), (3.5, CLR_CRITICAL)]),
    "flow":   ("flow",   "Flow Rate",        "m³/h", (40, 310), [(_Q_LO, CLR_WARNING), (60.0, CLR_CRITICAL)]),
    "risk":   ("risk",   "AI Failure Risk",  "%",    (-2, 102), [(_RISK_WARN, CLR_WARNING), (_RISK_CRIT, CLR_CRITICAL)]),
    "health": ("health", "Equipment Health", "%",    (-2, 102), [(50.0, CLR_CRITICAL), (80.0, CLR_WARNING)]),
    "conf":   ("conf",   "AI Confidence",    "%",    (-2, 102), [(70.0, CLR_WARNING), (50.0, CLR_CRITICAL)]),
}

class TrendDetailPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, chart_key: str, title: str, historian, well_ids: list[str], on_close, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.pack_propagate(False)
        self.chart_key = chart_key
        self.historian = historian
        self.well_ids = well_ids
        self.on_close = on_close
        
        # Priority / Title Bar
        title_frame = tk.Frame(self, bg=BG_PRIMARY)
        title_frame.pack(fill="x", pady=5)
        
        lbl = tk.Label(title_frame, text=f"Trend Detail – {title}", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(side="left", padx=20)
        
        btn_close = tk.Button(title_frame, text="✖ Close", bg="#ef4444", fg="white", font=FONT_LABEL, relief="flat", command=self.on_close)
        btn_close.pack(side="right", padx=20)
        
        # Control Toolbar
        self._build_toolbar()
        
        # Main Area (Chart + Stats)
        main_area = tk.Frame(self, bg=BG_PRIMARY)
        main_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        spec = _SPECS.get(chart_key)
        self.chart = TrendDetailChartPanel(main_area, chart_key, spec, well_ids)
        self.chart.pack(side="top", fill="both", expand=True, pady=(0, 10))
        
        # Stats Table
        self._build_stats_panel(main_area)
        
    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=BG_SECONDARY, bd=1, relief="ridge")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))
        
        # Time Range
        tk.Label(toolbar, text="Time Range:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left", padx=10, pady=5)
        self.cb_range = ttk.Combobox(toolbar, values=["Live (Rolling)", "Last 10 Min", "Last 30 Min", "Last 1 Hour", "Last 6 Hours", "Last 24 Hours"], state="readonly", width=15)
        self.cb_range.current(0)
        self.cb_range.pack(side="left", padx=5)
        self.cb_range.bind("<<ComboboxSelected>>", self._on_range_changed)
        
        tk.Button(toolbar, text="Load History", bg=BG_PRIMARY, fg=TEXT_PRIMARY, relief="flat", command=self._load_history).pack(side="left", padx=5)
        
        self.lbl_live_status = tk.Label(toolbar, text="🟢 LIVE", bg=BG_SECONDARY, fg="#10b981", font=FONT_SUBTITLE)
        self.lbl_live_status.pack(side="left", padx=15)
        
        # Vertical Separator
        tk.Frame(toolbar, width=2, bg=BORDER).pack(side="left", fill="y", padx=10, pady=2)
        
        # Toggles
        tk.Label(toolbar, text="Sensors:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left", padx=5)
        self.var_toggles = {}
        for wid in self.well_ids:
            var = tk.BooleanVar(value=True)
            self.var_toggles[wid] = var
            color = WELL_COLORS.get(wid, TEXT_PRIMARY)
            chk = tk.Checkbutton(toolbar, text=wid, variable=var, bg=BG_SECONDARY, fg=color, selectcolor=BG_PRIMARY, activebackground=BG_SECONDARY, activeforeground=color, command=lambda w=wid, v=var: self._on_toggle_changed(w, v))
            chk.pack(side="left", padx=5)
            
        # Vertical Separator
        tk.Frame(toolbar, width=2, bg=BORDER).pack(side="left", fill="y", padx=10, pady=2)
        
        # Export
        tk.Button(toolbar, text="CSV", bg="#10b981", fg="white", relief="flat", command=self._export_csv).pack(side="right", padx=10, pady=5)
        tk.Button(toolbar, text="PNG", bg="#3b82f6", fg="white", relief="flat", command=self._export_png).pack(side="right", padx=5)
        tk.Button(toolbar, text="PDF", bg="#ef4444", fg="white", relief="flat", command=self._export_pdf).pack(side="right", padx=5)
        tk.Label(toolbar, text="Export:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="right", padx=5)
        
    def _build_stats_panel(self, parent):
        stats_frame = tk.Frame(parent, bg=BG_SECONDARY, bd=1, relief="ridge", height=100)
        stats_frame.pack(side="bottom", fill="x")
        stats_frame.pack_propagate(False)
        
        # Header
        tk.Label(stats_frame, text="Well Name", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=0, sticky="ew", padx=1)
        tk.Label(stats_frame, text="Current Value", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=1, sticky="ew", padx=1)
        tk.Label(stats_frame, text="Average", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=2, sticky="ew", padx=1)
        tk.Label(stats_frame, text="Minimum", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=3, sticky="ew", padx=1)
        tk.Label(stats_frame, text="Maximum", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=4, sticky="ew", padx=1)
        tk.Label(stats_frame, text="Std Dev", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL, width=15).grid(row=0, column=5, sticky="ew", padx=1)
        
        self.stat_labels = {}
        for i, wid in enumerate(self.well_ids, start=1):
            color = WELL_COLORS.get(wid, TEXT_PRIMARY)
            tk.Label(stats_frame, text=wid, bg=BG_SECONDARY, fg=color, font=FONT_LABEL).grid(row=i, column=0, pady=2)
            
            lbls = {}
            for j, key in enumerate(["curr", "avg", "min", "max", "std"], start=1):
                lbl = tk.Label(stats_frame, text="--", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
                lbl.grid(row=i, column=j, pady=2)
                lbls[key] = lbl
            self.stat_labels[wid] = lbls
            
    def initialize_from_live(self, times, data, visibilities=None):
        self.chart.initialize_from_live(times, data)
        
        if visibilities:
            for wid, is_vis in visibilities.items():
                if wid in self.var_toggles:
                    self.var_toggles[wid].set(is_vis)
                    self.chart.set_line_visibility(wid, is_vis)
                    
        self._update_stats_ui()
        
    def _on_toggle_changed(self, wid, var):
        self.chart.set_line_visibility(wid, var.get())
        self._update_stats_ui()
        
    def _on_range_changed(self, event=None):
        if self.cb_range.get() == "Live (Rolling)":
            self.lbl_live_status.config(text="🟢 LIVE", fg="#10b981")
            # Clear and rely on live updates (optionally fetch last hour to re-init)
            self._load_live_history()
        else:
            self.lbl_live_status.config(text="⚪ HISTORICAL MODE", fg=TEXT_MUTED)
            self._load_history()
            
    def _load_live_history(self):
        if self.historian and hasattr(self.historian, 'query_sensor_history'):
            end = datetime.now()
            start = end - timedelta(hours=1)
            try:
                data = self.historian.query_sensor_history(start.isoformat(), end.isoformat())
                if data:
                    # Parse into format expected by initialize_from_live
                    # We can use the chart's plot_historical_data and then re-enable live mode
                    self.chart.plot_historical_data(data)
            except Exception as e:
                logger.error(f"Failed to load live history: {e}")
                
    def _load_history(self):
        rng = self.cb_range.get()
        if rng == "Live (Rolling)": return
        
        end = datetime.now()
        if rng == "Last 10 Min": start = end - timedelta(minutes=10)
        elif rng == "Last 30 Min": start = end - timedelta(minutes=30)
        elif rng == "Last 1 Hour": start = end - timedelta(hours=1)
        elif rng == "Last 6 Hours": start = end - timedelta(hours=6)
        elif rng == "Last 24 Hours": start = end - timedelta(hours=24)
        else: start = end - timedelta(hours=1)
            
        if self.historian and hasattr(self.historian, 'query_sensor_history'):
            try:
                data = self.historian.query_sensor_history(start.isoformat(), end.isoformat())
                if not data:
                    messagebox.showinfo("No Data", "No historical data available for the selected period.")
                self.chart.plot_historical_data(data)
                self._update_stats_ui()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load history:\n{e}")
        else:
            messagebox.showerror("Error", "Historian module not accessible.")
            
    def update_data(self, readings, reports, ai_result, rul_results=None, health_indexes=None):
        if self.cb_range.get() != "Live (Rolling)":
            return
            
        # Package into format that chart expects
        now = datetime.now()
        import matplotlib.dates as mdates
        t = mdates.date2num(now)
        
        self.chart.sync_live_view()
        self._update_stats_ui()
        
    def _update_stats_ui(self):
        stats = self.chart.get_stats()
        for wid in self.well_ids:
            if not self.var_toggles[wid].get() or wid not in stats:
                for lbl in self.stat_labels[wid].values():
                    lbl.config(text="--")
                continue
                
            s = stats[wid]
            self.stat_labels[wid]["curr"].config(text=f"{s['curr']:.2f}")
            self.stat_labels[wid]["avg"].config(text=f"{s['avg']:.2f}")
            self.stat_labels[wid]["min"].config(text=f"{s['min']:.2f}")
            self.stat_labels[wid]["max"].config(text=f"{s['max']:.2f}")
            self.stat_labels[wid]["std"].config(text=f"{s['std']:.2f}")
            
    def _export_csv(self):
        export_data = self.chart.get_visible_data()
        if not export_data:
            messagebox.showinfo("Export", "There is no visible data to export.")
            return
            
        import pandas as pd
        df = pd.DataFrame(export_data)
        df = df.sort_values(by=["Timestamp", "Well Name"])
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_detail_{self.chart_key}_{ts_str}.csv"
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Exported detail view data to {filename}")
            messagebox.showinfo("Export Success", f"Visible trend data exported to:\n{os.path.abspath(filename)}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            messagebox.showerror("Export Failed", f"Failed to export data: {e}")
            
    def _export_png(self):
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_detail_{self.chart_key}_{ts_str}.png"
        try:
            self.chart.get_figure().savefig(filename, facecolor=BG_PRIMARY, bbox_inches="tight", dpi=150)
            messagebox.showinfo("Export Success", f"Chart exported to:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export PNG: {e}")
            
    def _export_pdf(self):
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_detail_{self.chart_key}_{ts_str}.pdf"
        try:
            self.chart.get_figure().savefig(filename, facecolor=BG_PRIMARY, bbox_inches="tight")
            messagebox.showinfo("Export Success", f"Chart exported to:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export PDF: {e}")
