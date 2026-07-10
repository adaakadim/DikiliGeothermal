"""
gui/ai_decision_timeline_panel.py
=================================
Provides a chronological view of AI decisions, risk deltas, engineering summaries,
and future SHAP placeholder sections.
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import csv
import json

from analytics.ai.decision_timeline_logger import DecisionTimelineLogger
from gui.decision_comparison_dialog import DecisionComparisonDialog

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    FONT_LABEL, FONT_LABEL_SM, FONT_MONO_SM, FONT_SUBTITLE, FONT_MONO_MD
)

class AIDecisionTimelinePanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.logger = DecisionTimelineLogger()
        self._selected_event_id = None
        
        self._build_header()
        self._build_body()
        
        self._refresh_data()
        self.after(3000, self._periodic_refresh)

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 5))
        
        tk.Label(hdr, text="AI DECISION EXPLANATION TIMELINE", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(side="left", padx=10, pady=8)
        
        btn_pdf = tk.Button(hdr, text="Export PDF", bg="#ef4444", fg="white", relief="flat", command=lambda: self._export("pdf"))
        btn_pdf.pack(side="right", padx=(5, 10), pady=8)

        btn_excel = tk.Button(hdr, text="Export Excel", bg="#059669", fg="white", relief="flat", command=lambda: self._export("excel"))
        btn_excel.pack(side="right", padx=5, pady=8)

        btn_csv = tk.Button(hdr, text="Export CSV", bg="#10b981", fg="white", relief="flat", command=lambda: self._export("csv"))
        btn_csv.pack(side="right", padx=5, pady=8)
        
        btn_comp = tk.Button(hdr, text="Compare Selected", bg="#6366f1", fg="white", relief="flat", command=self._compare_selected)
        btn_comp.pack(side="right", padx=20, pady=8)

    def _build_body(self):
        self.body = tk.Frame(self, bg=BG_PRIMARY)
        self.body.pack(fill="both", expand=True)
        
        self.body.columnconfigure(0, weight=3) # Timeline List
        self.body.columnconfigure(1, weight=7) # Details Panel
        self.body.rowconfigure(0, weight=1)
        
        self._build_timeline_pane(self.body, row=0, col=0)
        self._build_detail_pane(self.body, row=0, col=1)

    def _build_timeline_pane(self, parent, row, col):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        
        tk.Label(f, text="DECISION TIMELINE", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=10, pady=5)
        
        cols = ("time", "status", "risk")
        style = ttk.Style()
        style.configure("Timeline.Treeview", rowheight=35)
        self.tree_tl = ttk.Treeview(f, columns=cols, show="headings", selectmode="extended", style="Timeline.Treeview")
        self.tree_tl.heading("time", text="Timestamp")
        self.tree_tl.heading("status", text="Status")
        self.tree_tl.heading("risk", text="Risk %")
        
        self.tree_tl.column("time", width=220, anchor="center")
        self.tree_tl.column("status", width=120, anchor="center")
        self.tree_tl.column("risk", width=90, anchor="center")
        
        vsb = ttk.Scrollbar(f, orient="vertical", command=self.tree_tl.yview)
        self.tree_tl.configure(yscrollcommand=vsb.set)
        
        self.tree_tl.pack(side="left", fill="both", expand=True, padx=(10,0), pady=(0, 10))
        vsb.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        
        self.tree_tl.tag_configure("NORMAL", foreground=CLR_NORMAL)
        self.tree_tl.tag_configure("WARNING", foreground=CLR_WARNING)
        self.tree_tl.tag_configure("CRITICAL", foreground=CLR_CRITICAL)
        
        self.tree_tl.bind("<<TreeviewSelect>>", self._on_timeline_select)

    def _build_detail_pane(self, parent, row, col):
        f = tk.Frame(parent, bg=BG_PRIMARY)
        f.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1) # KPIs & Summary
        f.rowconfigure(1, weight=2) # Sensors
        f.rowconfigure(2, weight=1) # SHAP Stub & Notes

        # --- Top Section: Reason, Deltas & Confidence ---
        top_f = tk.Frame(f, bg=BG_PRIMARY)
        top_f.grid(row=0, column=0, columnspan=2, sticky="nsew")
        top_f.columnconfigure(0, weight=2)
        top_f.columnconfigure(1, weight=1)
        top_f.columnconfigure(2, weight=1)
        
        # Summary Area
        sum_f = tk.Frame(top_f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        sum_f.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        tk.Label(sum_f, text="ENGINEERING DECISION SUMMARY", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        self.txt_summary = tk.Text(sum_f, height=4, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, wrap="word", relief="flat")
        self.txt_summary.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Deltas
        delta_f = tk.Frame(top_f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        delta_f.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        tk.Label(delta_f, text="CHANGE ANALYSIS", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        self.lbl_risk_delta = tk.Label(delta_f, text="Risk Delta: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_risk_delta.pack(anchor="w", padx=10, pady=2)
        self.lbl_health_delta = tk.Label(delta_f, text="Health Delta: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_health_delta.pack(anchor="w", padx=10, pady=2)
        self.lbl_conf_delta = tk.Label(delta_f, text="Conf Delta: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_conf_delta.pack(anchor="w", padx=10, pady=2)

        # Confidence Stats
        conf_f = tk.Frame(top_f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        conf_f.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        tk.Label(conf_f, text="CONFIDENCE EVOLUTION", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        self.lbl_conf_avg = tk.Label(conf_f, text="Average: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_conf_avg.pack(anchor="w", padx=10, pady=1)
        self.lbl_conf_high = tk.Label(conf_f, text="Highest: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_conf_high.pack(anchor="w", padx=10, pady=1)
        self.lbl_conf_low = tk.Label(conf_f, text="Lowest: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_conf_low.pack(anchor="w", padx=10, pady=1)
        self.lbl_conf_trend = tk.Label(conf_f, text="Trend: --", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
        self.lbl_conf_trend.pack(anchor="w", padx=10, pady=1)

        # --- Middle Section: Sensor Changes ---
        sens_f = tk.Frame(f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        sens_f.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)
        tk.Label(sens_f, text="SIGNIFICANT SENSOR CHANGES (Vs Previous Cycle)", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        
        style = ttk.Style()
        style.configure("Sensors.Treeview", rowheight=25)
        cols = ("feat", "old", "new", "diff", "pct")
        self.tree_sens = ttk.Treeview(sens_f, columns=cols, show="headings", style="Sensors.Treeview")
        self.tree_sens.heading("feat", text="Feature")
        self.tree_sens.heading("old", text="Old Val")
        self.tree_sens.heading("new", text="New Val")
        self.tree_sens.heading("diff", text="Diff")
        self.tree_sens.heading("pct", text="Change %")
        self.tree_sens.column("feat", width=250)
        self.tree_sens.column("old", width=80, anchor="e")
        self.tree_sens.column("new", width=80, anchor="e")
        self.tree_sens.column("diff", width=80, anchor="e")
        self.tree_sens.column("pct", width=80, anchor="e")
        self.tree_sens.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Confidence Evolution & Future SHAP Placeholder
        bot_f = tk.Frame(f, bg=BG_PRIMARY)
        bot_f.grid(row=2, column=0, columnspan=2, sticky="nsew")
        bot_f.columnconfigure(0, weight=1)
        bot_f.columnconfigure(1, weight=1)
        bot_f.columnconfigure(2, weight=1)
        
        # Operator Notes
        notes_f = tk.Frame(bot_f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        notes_f.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        nh = tk.Frame(notes_f, bg=BG_SECONDARY)
        nh.pack(fill="x")
        tk.Label(nh, text="OPERATOR NOTES", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=5, pady=2)
        btn_save = tk.Button(nh, text="Save Note", bg="#4f46e5", fg="white", font=("Segoe UI", 7), relief="flat", command=self._save_note)
        btn_save.pack(side="right", padx=5, pady=2)
        
        self.txt_notes = tk.Text(notes_f, height=3, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, wrap="word", relief="flat")
        self.txt_notes.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Confidence Chart
        chart_f = tk.Frame(bot_f, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        chart_f.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        tk.Label(chart_f, text="CONFIDENCE EVOLUTION", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.fig = Figure(figsize=(3, 1.5), dpi=80, facecolor=BG_SECONDARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_PRIMARY)
        self.ax.tick_params(colors=TEXT_SECONDARY, labelsize=7)
        for spine in self.ax.spines.values(): spine.set_color(BORDER)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # Future SHAP Placeholder
        shap_f = tk.Frame(bot_f, bg="#1e1e2f", highlightbackground="#4c1d95", highlightthickness=1)
        shap_f.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        tk.Label(shap_f, text="EXPLAINABLE AI (XAI) - FUTURE", bg="#1e1e2f", fg="#a78bfa", font=FONT_LABEL_SM).pack(anchor="w", padx=5, pady=2)
        tk.Label(shap_f, text="[ Feature Importance Placeholder ]", bg="#1e1e2f", fg=TEXT_MUTED, font=FONT_MONO_SM).pack(pady=(10,0))
        tk.Label(shap_f, text="[ SHAP Force Plot Placeholder ]", bg="#1e1e2f", fg=TEXT_MUTED, font=FONT_MONO_SM).pack(pady=5)

    def _on_timeline_select(self, event):
        sel = self.tree_tl.selection()
        if not sel: return
        
        item = self.tree_tl.item(sel[0])
        self._selected_event_id = item["tags"][0] # ID is stored in tag index 0
        
        self._populate_details(self._selected_event_id)

    def _populate_details(self, event_id):
        events = self.logger.get_timeline()
        target = next((e for e in events if e.get("event_id") == event_id), None)
        if not target: return
        
        # Summary
        self.txt_summary.delete("1.0", "end")
        self.txt_summary.insert("end", target.get("reason_summary", "No summary available."))
        
        # Deltas
        deltas = target.get("deltas", {})
        rd = deltas.get("risk", 0.0)
        hd = deltas.get("health", 0.0)
        cd = deltas.get("confidence", 0.0)
        
        self.lbl_risk_delta.config(
            text=f"Risk Delta: {rd:+.2f}%", 
            fg=CLR_CRITICAL if rd > 0 else (CLR_NORMAL if rd < 0 else TEXT_PRIMARY)
        )
        self.lbl_health_delta.config(
            text=f"Health Delta: {hd:+.2f}%",
            fg=CLR_NORMAL if hd > 0 else (CLR_WARNING if hd < 0 else TEXT_PRIMARY)
        )
        self.lbl_conf_delta.config(text=f"Conf Delta: {cd:+.2f}%")
        
        # Sensors
        for item in self.tree_sens.get_children():
            self.tree_sens.delete(item)
            
        changes = target.get("sensor_changes", [])
        for ch in changes:
            self.tree_sens.insert("", "end", values=(
                ch.get("feature"),
                ch.get("old"),
                ch.get("new"),
                ch.get("diff"),
                ch.get("pct")
            ))
            
        # Notes
        self.txt_notes.delete("1.0", "end")
        self.txt_notes.insert("end", target.get("operator_notes", ""))
        
        # Plot Confidence Evolution
        self.ax.clear()
        self.ax.set_facecolor(BG_PRIMARY)
        
        # Get up to 20 past events for the chart
        past_events = events[-20:]
        y_vals = [e.get("prediction", {}).get("Prediction Confidence (%)", 0.0) for e in past_events]
        x_vals = range(len(y_vals))
        
        if y_vals:
            self.ax.plot(x_vals, y_vals, color="#3b82f6", marker="o", markersize=3, linewidth=1.5)
            self.ax.fill_between(x_vals, y_vals, alpha=0.2, color="#3b82f6")
            self.ax.set_ylim(0, 105)
            self.ax.set_xticks([])
            self.ax.grid(True, linestyle=":", alpha=0.3)
        
        self.canvas.draw()

    def _save_note(self):
        if not self._selected_event_id:
            messagebox.showwarning("Warning", "Select a timeline event first.")
            return
            
        note_text = self.txt_notes.get("1.0", "end-1c")
        self.logger.update_operator_note(self._selected_event_id, note_text)
        messagebox.showinfo("Saved", "Operator note saved successfully.")

    def _refresh_data(self):
        events = self.logger.get_timeline()
        
        # Update confidence stats
        c_stats = self.logger.get_confidence_stats()
        self.lbl_conf_avg.config(text=f"Average: {c_stats['avg']:.1f}%")
        self.lbl_conf_high.config(text=f"Highest: {c_stats['high']:.1f}%")
        self.lbl_conf_low.config(text=f"Lowest: {c_stats['low']:.1f}%")
        trd = c_stats['trend']
        self.lbl_conf_trend.config(
            text=f"Trend: {trd:+.1f}%",
            fg=CLR_CRITICAL if trd < -5 else (CLR_NORMAL if trd > 5 else TEXT_PRIMARY)
        )
        
        events.reverse() # Newest first
        
        # Save selection
        sel_id = self._selected_event_id
        
        for item in self.tree_tl.get_children():
            self.tree_tl.delete(item)
            
        for ev in events:
            pred = ev.get("prediction", {})
            status = pred.get("Plant Status", "UNKNOWN")
            iid = self.tree_tl.insert("", "end", values=(
                ev.get("timestamp"),
                status,
                f"{pred.get('Pump Failure Probability (%)', 0.0):.1f}"
            ), tags=(ev.get("event_id"), status))
            
            if sel_id and sel_id == ev.get("event_id"):
                self.tree_tl.selection_set(iid)

    def _periodic_refresh(self):
        self._refresh_data()
        self.after(3000, self._periodic_refresh)

    def _export(self, format_type):
        events = self.logger.get_timeline()
        if not events: return
        
        ext = f".{format_type}" if format_type != "excel" else ".xlsx"
        if format_type == "pdf":
            ext = ".html" # Use HTML as PDF fallback without external libs
            
        ftypes = [(f"{format_type.upper()} Files", f"*{ext}")]
        fp = filedialog.asksaveasfilename(defaultextension=ext, filetypes=ftypes)
        
        if not fp: return
        
        try:
            if format_type == "csv":
                with open(fp, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["Event ID", "Timestamp", "Risk", "Health", "Confidence", "Summary", "Operator Notes"])
                    for ev in events:
                        pred = ev.get("prediction", {})
                        w.writerow([
                            ev.get("event_id"), ev.get("timestamp"),
                            pred.get("Pump Failure Probability (%)", 0.0),
                            pred.get("Equipment Health (%)", 0.0),
                            pred.get("Prediction Confidence (%)", 0.0),
                            ev.get("reason_summary", ""), ev.get("operator_notes", "")
                        ])
            elif format_type == "excel":
                try:
                    import pandas as pd
                    data = []
                    for ev in events:
                        pred = ev.get("prediction", {})
                        data.append({
                            "Event ID": ev.get("event_id"),
                            "Timestamp": ev.get("timestamp"),
                            "Risk": pred.get("Pump Failure Probability (%)", 0.0),
                            "Health": pred.get("Equipment Health (%)", 0.0),
                            "Confidence": pred.get("Prediction Confidence (%)", 0.0),
                            "Summary": ev.get("reason_summary", ""),
                            "Operator Notes": ev.get("operator_notes", "")
                        })
                    df = pd.DataFrame(data)
                    df.to_excel(fp, index=False)
                except ImportError:
                    messagebox.showwarning("Pandas missing", "Pandas or openpyxl missing. Saving as CSV instead.")
                    self._export("csv")
                    return
            elif format_type == "pdf":
                # Writing an HTML report acting as a PDF export (without external PDF libraries)
                with open(fp, "w", encoding="utf-8") as f:
                    f.write("<html><head><title>AI Decision Timeline Report</title></head><body>")
                    f.write("<h1>AI Decision Timeline Report</h1><table border='1'><tr><th>Timestamp</th><th>Risk</th><th>Health</th><th>Summary</th></tr>")
                    for ev in events:
                        pred = ev.get("prediction", {})
                        f.write(f"<tr><td>{ev.get('timestamp')}</td><td>{pred.get('Pump Failure Probability (%)', 0.0)}</td>")
                        f.write(f"<td>{pred.get('Equipment Health (%)', 0.0)}</td><td>{ev.get('reason_summary', '')}</td></tr>")
                    f.write("</table></body></html>")
                    
            messagebox.showinfo("Export", f"Timeline exported successfully to {fp}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _compare_selected(self):
        sel = self.tree_tl.selection()
        if len(sel) != 2:
            messagebox.showwarning("Comparison", "Please select exactly two timeline events to compare.")
            return
            
        id1 = self.tree_tl.item(sel[0])["tags"][0]
        id2 = self.tree_tl.item(sel[1])["tags"][0]
        
        events = self.logger.get_timeline()
        ev1 = next((e for e in events if e.get("event_id") == id1), None)
        ev2 = next((e for e in events if e.get("event_id") == id2), None)
        
        if ev1 and ev2:
            DecisionComparisonDialog(self, ev1, ev2)
