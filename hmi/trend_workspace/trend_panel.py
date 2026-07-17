"""
hmi/trend_workspace/trend_panel.py
==================================
Professional Trend Workspace wrapper.
"""

import tkinter as tk
import tkinter.ttk as ttk
from gui.theme import BG_PRIMARY, BG_SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY, FONT_SUBTITLE, FONT_LABEL, BORDER
from gui.trend_charts import TrendChartPanel
from datetime import datetime, timedelta
import tkinter.messagebox as messagebox
import logging

logger = logging.getLogger("HistorianUI")

class TrendWorkspace(tk.Frame):
    def __init__(self, parent: tk.Widget, well_ids: list, historian=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.pack_propagate(False)
        self.well_ids = well_ids
        self.historian = historian
        
        logger.info("Initializing Historian & Trend Analysis Workspace.")
        
        # Priority / Title Bar
        title_frame = tk.Frame(self, bg=BG_PRIMARY)
        title_frame.pack(fill="x", pady=5)
        lbl = tk.Label(title_frame, text="INDUSTRIAL HISTORIAN & TREND ANALYSIS", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(side="left", padx=20)
        
        # Control Toolbar
        self._build_toolbar()
        
        # The actual charts
        self.charts = TrendChartPanel(self, well_ids=well_ids)
        self.charts.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.charts.on_chart_click_cb = self._on_chart_click
        
        self.after(500, self._init_live_history)
        
    def _on_chart_click(self, chart_key: str, title: str):
        main_win = self.winfo_toplevel().children.get("!scadaguiapp", self.winfo_toplevel())
        if hasattr(main_win, '_handle_expand_chart'):
            main_win._handle_expand_chart(chart_key, title)
        
    def _init_live_history(self):
        if self.historian and hasattr(self.historian, 'query_sensor_history'):
            logger.info("Pre-loading live historian buffer with past 1 hour of data...")
            end = datetime.now()
            start = end - timedelta(hours=1)
            try:
                data = self.historian.query_sensor_history(start.isoformat(), end.isoformat())
                if data:
                    self.charts.initialize_history(data)
                    logger.info(f"Loaded {len(data)} historical points into live buffer.")
                else:
                    logger.warning("Historian query returned no data for the past 1 hour.")
            except Exception as e:
                logger.error(f"Exception while initializing live history: {e}")
        else:
            logger.error("Historian object not injected correctly or missing query method.")
        
    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=BG_SECONDARY, bd=1, relief="ridge")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))
        
        # Time Range
        tk.Label(toolbar, text="Time Range:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left", padx=10, pady=5)
        self.cb_range = ttk.Combobox(toolbar, values=["Live (5 Min)", "Live (15 Min)", "Live (1 Hour)", "Last 5 Min", "Last 15 Min", "Last 1 Hour", "Last 24 Hours"], state="readonly", width=15)
        self.cb_range.current(2)  # Default to Live (1 Hour)
        self.cb_range.pack(side="left", padx=5)
        self.cb_range.bind("<<ComboboxSelected>>", self._on_range_changed)
        
        tk.Button(toolbar, text="Load History", bg=BG_PRIMARY, fg=TEXT_PRIMARY, relief="flat", command=self._load_history).pack(side="left", padx=5)
        
        self.lbl_live_status = tk.Label(toolbar, text="🟢 LIVE", bg=BG_SECONDARY, fg="#10b981", font=FONT_SUBTITLE)
        self.lbl_live_status.pack(side="left", padx=15)
        
        # Vertical Separator
        tk.Frame(toolbar, width=2, bg=BORDER).pack(side="left", fill="y", padx=10, pady=2)
        
        # Toggles
        tk.Label(toolbar, text="Sensors:", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left", padx=5)
        
        from gui.theme import WELL_COLORS
        self.var_toggles = {}
        for wid in self.well_ids:
            var = tk.BooleanVar(value=True)
            self.var_toggles[wid] = var
            color = WELL_COLORS.get(wid, TEXT_PRIMARY)
            chk = tk.Checkbutton(toolbar, text=wid, variable=var, bg=BG_SECONDARY, fg=color, selectcolor=BG_PRIMARY, activebackground=BG_SECONDARY, activeforeground=color, command=self._on_toggle_changed)
            chk.pack(side="left", padx=2)
            
        # Vertical Separator
        tk.Frame(toolbar, width=2, bg=BORDER).pack(side="left", fill="y", padx=10, pady=2)
        
        # Export
        tk.Button(toolbar, text="Export CSV", bg=BG_PRIMARY, fg=TEXT_PRIMARY, relief="flat", command=self._export_csv).pack(side="right", padx=5)
        tk.Button(toolbar, text="Export PNG", bg=BG_PRIMARY, fg=TEXT_PRIMARY, relief="flat", command=self._export_png).pack(side="right", padx=5)
        tk.Button(toolbar, text="Export PDF", bg=BG_PRIMARY, fg=TEXT_PRIMARY, relief="flat", command=self._export_pdf).pack(side="right", padx=5)
        
    def _on_toggle_changed(self):
        # Pass visibility states to the charts
        states = {wid: var.get() for wid, var in self.var_toggles.items()}
        self.charts.set_line_visibility(states)
        
    def _on_range_changed(self, event=None):
        rng = self.cb_range.get()
        if "Live" in rng:
            self.charts.set_mode("LIVE")
            self.lbl_live_status.config(text="🟢 LIVE", fg="#10b981")
            
            # Apply time window size to live chart
            if "5 Min" in rng:
                self.charts.set_live_window_minutes(5)
            elif "15 Min" in rng:
                self.charts.set_live_window_minutes(15)
            elif "1 Hour" in rng:
                self.charts.set_live_window_minutes(60)
        else:
            self.charts.set_mode("HISTORICAL")
            self.lbl_live_status.config(text="⚪ OFFLINE", fg="#9ca3af")
            self._load_history()

    def _load_history(self):
        rng = self.cb_range.get()
        if "Live" in rng:
            messagebox.showinfo("Historian", "System is in Live mode. Select a historical time range to load data.")
            return
            
        end = datetime.now()
        if "5 Min" in rng:
            start = end - timedelta(minutes=5)
        elif "15 Min" in rng:
            start = end - timedelta(minutes=15)
        elif "1 Hour" in rng:
            start = end - timedelta(hours=1)
        elif "24 Hours" in rng:
            start = end - timedelta(hours=24)
        else:
            start = end - timedelta(hours=1)
            
        # Try fetching from historian
        if self.historian and hasattr(self.historian, 'query_sensor_history'):
            logger.info(f"Loading historical data from {start} to {end}")
            try:
                data = self.historian.query_sensor_history(start.isoformat(), end.isoformat())
                self.charts.plot_historical_data(data)
                logger.info(f"Loaded {len(data)} rows for historical view.")
            except Exception as e:
                logger.error(f"Exception during historical data load: {e}")
                messagebox.showerror("Database Error", f"Failed to query database:\n{e}")
        else:
            logger.error("Historian module not accessible when loading history.")
            messagebox.showerror("Error", "Historian module not accessible.\nCheck database connectivity or service status.")
            
    def _export_csv(self):
        rng = self.cb_range.get()
        export_data = self.charts.get_visible_data()
        
        if not export_data:
            messagebox.showinfo("Export", "There is no visible data to export.")
            return
            
        import pandas as pd
        from datetime import datetime
        import os
        
        df = pd.DataFrame(export_data)
        
        # Sort by timestamp and well name
        df = df.sort_values(by=["Timestamp", "Well Name"])
        
        # Determine path
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_trends_{ts_str}.csv"
        
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Exported visible trend data to {filename}")
            messagebox.showinfo("Export Success", f"Visible trend data exported to:\n{os.path.abspath(filename)}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            messagebox.showerror("Export Failed", f"Failed to export data: {e}")

    def _export_png(self):
        self.charts.export_image("png")
        
    def _export_pdf(self):
        self.charts.export_image("pdf")
        
    def update_data(self, readings, reports, ai_result, rul_results=None, health_indexes=None):
        # Only push live data if we are in Live mode
        if "Live" in self.cb_range.get():
            self.charts.update_data(readings, reports, ai_result, rul_results, health_indexes)
