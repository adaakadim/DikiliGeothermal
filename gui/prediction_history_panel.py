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
        self.columnconfigure(0, weight=45)
        self.columnconfigure(1, weight=55)
        self.rowconfigure(1, weight=1)
        
        # 1. Top Bar: Filters & Export
        top_bar = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        tk.Label(top_bar, text="PREDICTION HISTORY", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(side="left", padx=15, pady=10)
        
        # Filters (aligned vertically with equal heights)
        filter_frame = tk.Frame(top_bar, bg=BG_HEADER)
        filter_frame.pack(side="left", fill="y", pady=10, padx=5)
        
        tk.Label(filter_frame, text="Equip:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(10, 5))
        self.cb_equip = ttk.Combobox(filter_frame, values=["All", "PLANT", "P-101", "P-201", "P-301"], width=10, state="readonly")
        self.cb_equip.current(0)
        self.cb_equip.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Status:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(15, 5))
        self.cb_status = ttk.Combobox(filter_frame, values=["All", "NORMAL", "WARNING", "CRITICAL"], width=10, state="readonly")
        self.cb_status.current(0)
        self.cb_status.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Min Conf:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(15, 5))
        self.cb_conf = ttk.Combobox(filter_frame, values=["0", "50", "80", "95"], width=5, state="readonly")
        self.cb_conf.current(0)
        self.cb_conf.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Search:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(15, 5))
        self.entry_search = ttk.Entry(filter_frame, width=20)
        self.entry_search.pack(side="left", padx=5)
        
        btn_apply = tk.Button(filter_frame, text="Apply Filters", bg="#374151", fg=TEXT_PRIMARY, relief="flat", command=self.refresh_data)
        btn_apply.pack(side="left", padx=15)
        
        # Export Buttons on far right
        btn_exp_xl = tk.Button(top_bar, text="Export Excel", bg="#0ea5e9", fg="white", relief="flat", command=self._export_excel)
        btn_exp_xl.pack(side="right", padx=(5, 15), pady=10)
        btn_exp_csv = tk.Button(top_bar, text="Export CSV", bg="#10b981", fg="white", relief="flat", command=self._export_csv)
        btn_exp_csv.pack(side="right", padx=5, pady=10)

        # 2. Left Column: Timeline
        left_col = tk.Frame(self, bg=BG_PRIMARY)
        left_col.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        
        tree_frame = tk.Frame(left_col, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        tree_frame.pack(fill="both", expand=True)
        
        cols = ("time", "equip", "risk", "health", "maint", "status", "conf")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        
        def _sort_tree(col, reverse):
            l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(reverse=reverse)
            for index, (val, k) in enumerate(l):
                self.tree.move(k, '', index)
            self.tree.heading(col, command=lambda: _sort_tree(col, not reverse))

        self.tree.heading("time", text="Timestamp", command=lambda: _sort_tree("time", False))
        self.tree.heading("equip", text="Equipment", command=lambda: _sort_tree("equip", False))
        self.tree.heading("risk", text="Failure Risk", command=lambda: _sort_tree("risk", False))
        self.tree.heading("health", text="Health", command=lambda: _sort_tree("health", False))
        self.tree.heading("maint", text="Maintenance", command=lambda: _sort_tree("maint", False))
        self.tree.heading("status", text="Status", command=lambda: _sort_tree("status", False))
        self.tree.heading("conf", text="Confidence", command=lambda: _sort_tree("conf", False))
        
        self.tree.column("time", width=170, anchor="center")
        self.tree.column("equip", width=130, anchor="center")
        self.tree.column("risk", width=90, anchor="center")
        self.tree.column("health", width=90, anchor="center")
        self.tree.column("maint", width=120, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("conf", width=90, anchor="center")
        
        self.tree.tag_configure("evenrow", background=BG_SECONDARY)
        self.tree.tag_configure("oddrow", background=BG_TERTIARY)
        self.tree.tag_configure("hover", background="#334155")
        
        self.tree.tag_configure("status_normal", foreground=CLR_NORMAL)
        self.tree.tag_configure("status_warning", foreground=CLR_WARNING)
        self.tree.tag_configure("status_critical", foreground=CLR_CRITICAL)
        
        self._last_hover = None
        def _on_tree_motion(event):
            item = self.tree.identify_row(event.y)
            if self._last_hover and self._last_hover != item:
                self.tree.tk.call(self.tree, "tag", "remove", "hover", self._last_hover)
            if item:
                self.tree.tk.call(self.tree, "tag", "add", "hover", item)
                self._last_hover = item
                
        def _on_tree_leave(event):
            if self._last_hover:
                self.tree.tk.call(self.tree, "tag", "remove", "hover", self._last_hover)
                self._last_hover = None
                
        self.tree.bind("<Motion>", _on_tree_motion)
        self.tree.bind("<Leave>", _on_tree_leave)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # 3. Right Column: Stats & Trends
        right_col = tk.Frame(self, bg=BG_PRIMARY)
        right_col.grid(row=1, column=1, sticky="nsew", padx=(2, 0))
        
        # AI Performance Summary
        stats_frame = tk.Frame(right_col, bg=BG_PRIMARY)
        stats_frame.pack(fill="x", pady=(0, 4))
        
        tk.Label(stats_frame, text="AI PERFORMANCE SUMMARY", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(4, 6), anchor="w")
        
        stats_grid = tk.Frame(stats_frame, bg=BG_PRIMARY)
        stats_grid.pack(fill="x")
        
        for i in range(3): stats_grid.columnconfigure(i, weight=1)
        
        self.kpi_cards = {}
        def _add_kpi(key, title, icon, desc, r, c):
            from gui.widgets import KPICard
            
            # Temporary internal class if KPICard isn't matching perfectly
            class AnalyticsKPICard(tk.Frame):
                def __init__(self, parent, title, icon="■", desc="", **kwargs):
                    super().__init__(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
                    self.pack_propagate(False)
                    self.config(height=85)
                    
                    hdr = tk.Frame(self, bg=BG_SECONDARY)
                    hdr.pack(side="top", fill="x", padx=10, pady=(6, 2))
                    
                    tk.Label(hdr, text=icon, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(0, 4))
                    tk.Label(hdr, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w").pack(side="left", fill="x")
                    
                    self.lbl_val = tk.Label(self, text="-", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Consolas", 18, "bold"), anchor="w")
                    self.lbl_val.pack(side="top", fill="x", padx=10)
                    
                    self.lbl_desc = tk.Label(self, text=desc, bg=BG_SECONDARY, fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")
                    self.lbl_desc.pack(side="top", fill="x", padx=10, pady=(0, 4))
                    
                def set_value(self, val, color=None):
                    self.lbl_val.config(text=str(val))
                    if color: self.lbl_val.config(fg=color)
            
            card = AnalyticsKPICard(stats_grid, title, icon=icon, desc=desc)
            card.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
            self.kpi_cards[key] = card
            
        _add_kpi("total", "Total Predictions", "📊", "Historical records", 0, 0)
        _add_kpi("avg_fail", "Avg Failure Risk", "⚠️", "Overall probability", 0, 1)
        _add_kpi("avg_hlth", "Average Health", "❤️", "Equipment condition", 0, 2)
        _add_kpi("avg_conf", "Avg Confidence", "🎯", "Model certainty", 1, 0)
        _add_kpi("crit", "Critical Predictions", "🔥", "Immediate action", 1, 1)
        _add_kpi("maint", "Maintenance Req", "🔧", "Actions required", 1, 2)
        
        # Trend Chart
        self.chart_container = tk.Frame(right_col, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.chart_container.pack(fill="both", expand=True, pady=(5, 0))
        
        # Empty State
        self.empty_frame = tk.Frame(self.chart_container, bg=BG_SECONDARY)
        tk.Label(self.empty_frame, text="📈", bg=BG_SECONDARY, fg="#3b82f6", font=("Segoe UI", 48)).pack(pady=(60, 10))
        tk.Label(self.empty_frame, text="No prediction history available.", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(pady=(0, 5))
        tk.Label(self.empty_frame, text="Run the AI Engine to generate predictions.", bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_LABEL).pack(pady=(0, 40))
        
        # Plot Frame
        self.plot_frame = tk.Frame(self.chart_container, bg=BG_SECONDARY)
        
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor(BG_SECONDARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_PRIMARY)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        
        toolbar_frame = tk.Frame(self.plot_frame, bg=BG_SECONDARY)
        toolbar_frame.pack(side="bottom", fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        from gui.theme import style_matplotlib_toolbar
        style_matplotlib_toolbar(self.toolbar)
            
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        # Tooltip Annotations
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
            bbox=dict(boxstyle="round", fc=BG_HEADER, ec=BORDER, alpha=0.9),
            arrowprops=dict(arrowstyle="->", color=TEXT_SECONDARY), color=TEXT_PRIMARY, fontsize=8, zorder=10)
        self.annot.set_visible(False)
        self.ax_vline = self.ax.axvline(x=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
        
        self.canvas.mpl_connect("motion_notify_event", self._on_hover_chart)
        self.canvas.mpl_connect("axes_leave_event", lambda e: self._hide_tooltip())
        
        self.current_data = []
        
        # Initial View
        self.empty_frame.pack(fill="both", expand=True)

    def _hide_tooltip(self):
        self.annot.set_visible(False)
        self.ax_vline.set_alpha(0.0)
        self.canvas.draw_idle()

    def _on_hover_chart(self, event):
        if event.inaxes == self.ax and self.current_data:
            x = int(round(event.xdata)) if event.xdata else None
            if x is not None and 0 <= x < len(self.current_data):
                self.ax_vline.set_xdata([x, x])
                self.ax_vline.set_alpha(0.8)
                d = self.current_data[x]
                txt = f"Time: {d.get('time', '').split(' ')[-1]}\nRisk: {d.get('failure_probability',0):.1f}%\nHealth: {d.get('health_score',0):.1f}%\nConf: {d.get('confidence',0):.1f}%"
                self.annot.xy = (x, event.ydata)
                self.annot.set_text(txt)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                self._hide_tooltip()
        else:
            self._hide_tooltip()

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
            
        crit_count = 0
        maint_count = 0
            
        for i, rec in enumerate(reversed(self.current_data)): # Newest first in table
            maint = "YES" if rec.get("maintenance_required") else "NO"
            status = rec.get("status", "NORMAL")
            
            if status == "CRITICAL": crit_count += 1
            if maint == "YES": maint_count += 1
            
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            
            # Determine status color tag
            status_tag = ""
            if status == "NORMAL": status_tag = "status_normal"
            elif status == "WARNING": status_tag = "status_warning"
            elif status == "CRITICAL": status_tag = "status_critical"
            
            self.tree.insert("", "end", values=(
                rec.get("time"),
                rec.get("equipment"),
                f"{rec.get('failure_probability', 0):.1f}",
                f"{rec.get('health_score', 100):.1f}",
                maint,
                status,
                f"{rec.get('confidence', 100):.1f}"
            ), tags=(tag, status_tag))
            
        # Update Stats
        stats = self.logger.get_summary_statistics(self.current_data)
        self.kpi_cards["total"].set_value(stats["total"])
        self.kpi_cards["avg_fail"].set_value(f"{stats['avg_failure']:.1f}%", color=CLR_WARNING if stats['avg_failure'] > 50 else CLR_NORMAL)
        self.kpi_cards["avg_hlth"].set_value(f"{stats['lowest_health']:.1f}%", color=CLR_CRITICAL if stats['lowest_health'] < 50 else CLR_NORMAL)
        self.kpi_cards["avg_conf"].set_value(f"{stats['avg_confidence']:.1f}%")
        self.kpi_cards["crit"].set_value(crit_count, color=CLR_CRITICAL if crit_count > 0 else TEXT_PRIMARY)
        self.kpi_cards["maint"].set_value(maint_count, color=CLR_WARNING if maint_count > 0 else TEXT_PRIMARY)
        
        # Manage Empty State & Chart
        if not self.current_data:
            self.plot_frame.pack_forget()
            self.empty_frame.pack(fill="both", expand=True)
        else:
            self.empty_frame.pack_forget()
            self.plot_frame.pack(fill="both", expand=True)
            self._update_chart()

    def _update_chart(self):
        self.ax.clear()
        
        # Chronological for chart
        data_asc = self.current_data
        
        times = [d.get("time", "") for d in data_asc]
        fails = [d.get("failure_probability", 0) for d in data_asc]
        healths = [d.get("health_score", 100) for d in data_asc]
        confs = [d.get("confidence", 100) for d in data_asc]
        
        x_idx = range(len(times))
        
        # Three colored traces: Failure Risk (Orange), Health (Green), Confidence (Blue)
        self.ax.plot(x_idx, fails, color="#f59e0b", label="Failure Risk %", linewidth=2)
        self.ax.plot(x_idx, healths, color="#10b981", label="Health %", linewidth=2)
        self.ax.plot(x_idx, confs, color="#3b82f6", label="Confidence %", linewidth=2)
        
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
        self.ax.set_title("AI Predictive Analytics over Time", color=TEXT_SECONDARY, fontsize=10)
        
        self.fig.tight_layout()
        
        # Re-attach tooltip elements to new axes instance
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
            bbox=dict(boxstyle="round", fc=BG_HEADER, ec=BORDER, alpha=0.9),
            arrowprops=dict(arrowstyle="->", color=TEXT_SECONDARY), color=TEXT_PRIMARY, fontsize=8, zorder=10)
        self.annot.set_visible(False)
        self.ax_vline = self.ax.axvline(x=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
        
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
