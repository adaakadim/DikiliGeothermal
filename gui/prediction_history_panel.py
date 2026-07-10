"""
gui/prediction_history_panel.py
===============================
Provides a comprehensive UI for browsing, searching, analyzing, and exporting
historical AI predictions. Includes a Timeline, Trend Visualizations, and KPIs.
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk # type: ignore
from matplotlib.figure import Figure # type: ignore

from analytics.ai.prediction_history import PredictionHistoryLogger

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    FONT_LABEL, FONT_LABEL_SM, FONT_MONO_SM, FONT_TITLE, FONT_SUBTITLE, FONT_MONO_MD
)

class PredictionHistoryPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, history_logger: PredictionHistoryLogger, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.logger = history_logger
        
        # UI Layout
        self.columnconfigure(0, weight=6)
        self.columnconfigure(1, weight=4)
        self.rowconfigure(1, weight=1)
        
        # 1. Top Bar: Filters & Export
        top_bar = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        tk.Label(top_bar, text="PREDICTION HISTORY", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(side="left", padx=10, pady=5)
        
        # Filters
        tk.Label(top_bar, text="Equip:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(10, 2))
        self.cb_equip = ttk.Combobox(top_bar, values=["All", "PLANT", "P-101", "P-201", "P-301"], width=10, state="readonly")
        self.cb_equip.current(0)
        self.cb_equip.pack(side="left", padx=2)
        
        tk.Label(top_bar, text="Status:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(10, 2))
        self.cb_status = ttk.Combobox(top_bar, values=["All", "NORMAL", "WARNING", "CRITICAL"], width=10, state="readonly")
        self.cb_status.current(0)
        self.cb_status.pack(side="left", padx=2)
        
        tk.Label(top_bar, text="Min Conf:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(10, 2))
        self.cb_conf = ttk.Combobox(top_bar, values=["0", "50", "80", "95"], width=5, state="readonly")
        self.cb_conf.current(0)
        self.cb_conf.pack(side="left", padx=2)
        
        tk.Label(top_bar, text="Search:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(10, 2))
        self.entry_search = ttk.Entry(top_bar, width=20)
        self.entry_search.pack(side="left", padx=2)
        
        btn_apply = tk.Button(top_bar, text="Apply Filters", bg="#374151", fg=TEXT_PRIMARY, relief="flat", command=self.refresh_data)
        btn_apply.pack(side="left", padx=10)
        
        btn_exp_csv = tk.Button(top_bar, text="Export CSV", bg="#10b981", fg="white", relief="flat", command=self._export_csv)
        btn_exp_csv.pack(side="right", padx=(5, 10))
        btn_exp_xl = tk.Button(top_bar, text="Export Excel", bg="#0ea5e9", fg="white", relief="flat", command=self._export_excel)
        btn_exp_xl.pack(side="right", padx=5)

        # 2. Left Column: Timeline
        left_col = tk.Frame(self, bg=BG_PRIMARY)
        left_col.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        
        tree_frame = tk.Frame(left_col, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        tree_frame.pack(fill="both", expand=True)
        
        cols = ("time", "equip", "risk", "health", "maint", "status", "conf")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("equip", text="Equip")
        self.tree.heading("risk", text="Fail Risk %")
        self.tree.heading("health", text="Health %")
        self.tree.heading("maint", text="Maint?")
        self.tree.heading("status", text="Status")
        self.tree.heading("conf", text="Conf %")
        
        self.tree.column("time", width=130, anchor="center")
        self.tree.column("equip", width=80, anchor="center")
        self.tree.column("risk", width=80, anchor="center")
        self.tree.column("health", width=80, anchor="center")
        self.tree.column("maint", width=80, anchor="center")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("conf", width=60, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # 3. Right Column: Stats & Trends
        right_col = tk.Frame(self, bg=BG_PRIMARY)
        right_col.grid(row=1, column=1, sticky="nsew", padx=(2, 0))
        
        # Stats
        stats_frame = tk.Frame(right_col, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        stats_frame.pack(fill="x", pady=(0, 4))
        
        tk.Label(stats_frame, text="AI PERFORMANCE SUMMARY", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(4, 2))
        self.stats_labels = {}
        
        stats_grid = tk.Frame(stats_frame, bg=BG_SECONDARY)
        stats_grid.pack(fill="x", padx=10, pady=5)
        
        self._build_stat_box(stats_grid, "Total Predictions", "total", 0, 0)
        self._build_stat_box(stats_grid, "Avg Failure %", "avg_fail", 0, 1)
        self._build_stat_box(stats_grid, "Lowest Health %", "low_hlth", 0, 2)
        self._build_stat_box(stats_grid, "Avg Conf %", "avg_conf", 1, 0, colspan=3)
        
        # Trend Chart
        chart_frame = tk.Frame(right_col, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        chart_frame.pack(fill="both", expand=True)
        
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor(BG_SECONDARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_PRIMARY)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        
        toolbar_frame = tk.Frame(chart_frame, bg=BG_SECONDARY)
        toolbar_frame.pack(side="bottom", fill="x")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        from gui.theme import style_matplotlib_toolbar
        style_matplotlib_toolbar(toolbar)
            
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        self.current_data = []

    def _build_stat_box(self, parent, title, key, row, col, colspan=1):
        f = tk.Frame(parent, bg=BG_PRIMARY, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)
        parent.columnconfigure(col, weight=1)
        tk.Label(f, text=title, bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(2, 0))
        lbl = tk.Label(f, text="--", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        lbl.pack(pady=(0, 2))
        self.stats_labels[key] = lbl

    def refresh_data(self):
        eq = self.cb_equip.get()
        st = self.cb_status.get()
        cf = float(self.cb_conf.get())
        sq = self.entry_search.get()
        
        self.current_data = self.logger.filter_history(
            equipment=eq, status=st, min_conf=cf, search_term=sq
        )
        
        # Update Table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for rec in reversed(self.current_data): # Newest first in table
            maint = "YES" if rec.get("maintenance_required") else "NO"
            self.tree.insert("", "end", values=(
                rec.get("time"),
                rec.get("equipment"),
                f"{rec.get('failure_probability', 0):.1f}",
                f"{rec.get('health_score', 100):.1f}",
                maint,
                rec.get("status"),
                f"{rec.get('confidence', 100):.1f}"
            ))
            
        # Update Stats
        stats = self.logger.get_summary_statistics(self.current_data)
        self.stats_labels["total"].config(text=str(stats["total"]))
        self.stats_labels["avg_fail"].config(text=f"{stats['avg_failure']:.1f}")
        self.stats_labels["low_hlth"].config(text=f"{stats['lowest_health']:.1f}")
        self.stats_labels["avg_conf"].config(text=f"{stats['avg_confidence']:.1f}")
        
        # Update Chart
        self._update_chart()

    def _update_chart(self):
        self.ax.clear()
        
        if not self.current_data:
            self.ax.text(0.5, 0.5, "No Data Found", color=TEXT_MUTED, ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
            
        # Chronological for chart
        data_asc = self.current_data
        
        times = [d.get("time", "") for d in data_asc]
        fails = [d.get("failure_probability", 0) for d in data_asc]
        healths = [d.get("health_score", 100) for d in data_asc]
        
        x_idx = range(len(times))
        
        self.ax.plot(x_idx, fails, color="#ef4444", label="Failure Prob %")
        self.ax.plot(x_idx, healths, color="#10b981", label="Health %")
        
        # Grid and styling
        self.ax.set_ylim(0, 105)
        self.ax.grid(True, color="#374151", linestyle="--", alpha=0.5)
        self.ax.tick_params(colors=TEXT_MUTED, labelsize=8)
        
        # Simplify X-axis if many points
        if len(times) > 10:
            step = len(times) // 5
            self.ax.set_xticks(x_idx[::step])
            self.ax.set_xticklabels([t.split(" ")[1] for t in times[::step]], rotation=15)
        else:
            self.ax.set_xticks(x_idx)
            self.ax.set_xticklabels([t.split(" ")[1] for t in times], rotation=15)
            
        self.ax.legend(loc="upper right", facecolor=BG_PRIMARY, edgecolor=BORDER, labelcolor=TEXT_PRIMARY, fontsize=8)
        self.ax.set_title("AI Trend Visualization", color=TEXT_SECONDARY, fontsize=10)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _on_tree_select(self, event):
        pass

    def _export_csv(self):
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if fp:
            if self.logger.export_to_csv(fp, self.current_data):
                messagebox.showinfo("Export", "CSV Exported Successfully!")
            else:
                messagebox.showerror("Export", "Failed to export CSV.")

    def _export_excel(self):
        fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if fp:
            if self.logger.export_to_excel(fp, self.current_data):
                messagebox.showinfo("Export", "Excel Exported Successfully!")
            else:
                messagebox.showerror("Export", "Failed to export Excel.")
