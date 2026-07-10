"""
gui/ai_dataset_panel.py
=======================
Dataset Intelligence & Data Quality Center.
Displays dataset schema, real-time data quality scores, and compatibility statuses.
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import json
import csv

from analytics.ai.random_forest.dataset_metadata import DatasetIntrospector
from analytics.ai.random_forest.dataset_monitor import DataQualityMonitor

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    FONT_LABEL, FONT_LABEL_SM, FONT_MONO_SM, FONT_SUBTITLE, FONT_MONO_MD
)

class AIDatasetPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        self.schema = DatasetIntrospector.get_feature_schema()
        
        self._build_header()
        self._build_body()
        
        self._refresh_data()
        self.after(2000, self._periodic_refresh)

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 5))
        
        tk.Label(hdr, text="DATASET INTELLIGENCE & DATA QUALITY CENTER", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(side="left", padx=10, pady=8)
        
        # Export Buttons
        btn_json = tk.Button(hdr, text="Export JSON", bg="#374151", fg=TEXT_PRIMARY, relief="flat", command=lambda: self._export("json"))
        btn_json.pack(side="right", padx=(5, 10))
        btn_csv = tk.Button(hdr, text="Export CSV", bg="#10b981", fg="white", relief="flat", command=lambda: self._export("csv"))
        btn_csv.pack(side="right", padx=5)

    def _build_body(self):
        self.body = tk.Frame(self, bg=BG_PRIMARY)
        self.body.pack(fill="both", expand=True)
        
        self.body.columnconfigure(0, weight=2)
        self.body.columnconfigure(1, weight=8)
        self.body.rowconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)
        self.body.rowconfigure(2, weight=3)
        
        # 1. Dataset Overview
        self.frame_ov = self._create_card(self.body, "DATASET OVERVIEW", 0, 0, rowspan=2)
        self.lbls_ov = self._create_keyval_grid(self.frame_ov, [
            ("Dataset Name", "name"), ("Dataset Version", "ver"),
            ("Total Samples", "samples"), ("Features", "features"),
            ("Target Classes", "classes"), ("Creation Date", "cdate"),
            ("Last Training", "tdate"), ("Source", "source")
        ])
        
        # 2. Data Quality Summary
        self.frame_dq = self._create_card(self.body, "DATA QUALITY SUMMARY", 0, 1)
        
        dq_grid = tk.Frame(self.frame_dq, bg=BG_SECONDARY)
        dq_grid.pack(fill="both", expand=True, padx=5, pady=5)
        for c in range(4): dq_grid.columnconfigure(c, weight=1)
        
        self.lbls_dq = {}
        self._build_dq_box(dq_grid, "Overall DQ Score", "score", 0, 0)
        self._build_dq_box(dq_grid, "Missing Value %", "missing_pct", 0, 1)
        self._build_dq_box(dq_grid, "Invalid Values", "invalid", 0, 2)
        self._build_dq_box(dq_grid, "Duplicate Records", "dup", 0, 3)
        self._build_dq_box(dq_grid, "Completeness %", "comp", 1, 0)
        self._build_dq_box(dq_grid, "Feature Availability", "avail", 1, 1)
        self._build_dq_box(dq_grid, "Missing Features", "missing_feat", 1, 2)
        self._build_dq_box(dq_grid, "Compatibility", "compat", 1, 3)

        # 3. Feature Information & Monitor (Treeview)
        self.frame_feat = self._create_card(self.body, "FEATURE INFORMATION & LIVE MONITOR", 2, 0, colspan=2)
        
        # Filter
        filter_bar = tk.Frame(self.frame_feat, bg=BG_SECONDARY)
        filter_bar.pack(fill="x", padx=10, pady=(0, 5))
        tk.Label(filter_bar, text="Search Feature:", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_tree())
        ttk.Entry(filter_bar, textvariable=self.search_var, width=30).pack(side="left", padx=5)

        style = ttk.Style()
        style.configure("Dataset.Treeview", rowheight=30)
        
        cols = ("name", "desc", "unit", "type", "min", "max", "avg", "std", "live", "status")
        self.tree = ttk.Treeview(self.frame_feat, columns=cols, show="headings", selectmode="browse", style="Dataset.Treeview")
        
        self.tree.heading("name", text="Feature Name")
        self.tree.heading("desc", text="Description")
        self.tree.heading("unit", text="Unit")
        self.tree.heading("type", text="Type")
        self.tree.heading("min", text="Min")
        self.tree.heading("max", text="Max")
        self.tree.heading("avg", text="Avg")
        self.tree.heading("std", text="Std")
        self.tree.heading("live", text="Live Value")
        self.tree.heading("status", text="Monitor Status")
        
        self.tree.column("name", width=200, anchor="w")
        self.tree.column("desc", width=250, anchor="w")
        self.tree.column("unit", width=60, anchor="center")
        self.tree.column("type", width=60, anchor="center")
        self.tree.column("min", width=60, anchor="center")
        self.tree.column("max", width=60, anchor="center")
        self.tree.column("avg", width=60, anchor="center")
        self.tree.column("std", width=60, anchor="center")
        self.tree.column("live", width=80, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        vsb = ttk.Scrollbar(self.frame_feat, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=(0, 10))
        vsb.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))

        # Tag configuration for monitor status colors
        self.tree.tag_configure("READY", foreground=CLR_NORMAL)
        self.tree.tag_configure("MISSING", foreground=CLR_CRITICAL)
        self.tree.tag_configure("INVALID", foreground=CLR_WARNING)
        self.tree.tag_configure("OUT OF RANGE", foreground="#f97316") # Orange

    def _create_card(self, parent, title, row, col, rowspan=1, colspan=1):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, sticky="nsew", padx=4, pady=4)
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=10, pady=(10, 5))
        return f

    def _create_keyval_grid(self, parent, fields):
        container = tk.Frame(parent, bg=BG_SECONDARY)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        container.columnconfigure(0, weight=1, minsize=140)
        container.columnconfigure(1, weight=1)
        
        labels = {}
        for i, (label_text, key) in enumerate(fields):
            tk.Label(container, text=label_text, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).grid(row=i, column=0, sticky="w", pady=3)
            lbl_val = tk.Label(container, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
            lbl_val.grid(row=i, column=1, sticky="w", pady=3)
            labels[key] = lbl_val
        return labels

    def _build_dq_box(self, parent, title, key, row, col):
        f = tk.Frame(parent, bg=BG_PRIMARY, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        tk.Label(f, text=title, bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(pady=(5, 0))
        lbl = tk.Label(f, text="--", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        lbl.pack(pady=(0, 5))
        self.lbls_dq[key] = lbl

    def _filter_tree(self):
        self._refresh_tree()

    def _refresh_tree(self):
        eval_data = DataQualityMonitor.get_latest_evaluation()
        live_vals = DataQualityMonitor.get_latest_live_values()
        status_map = eval_data.get("live_status_map", {})
        
        search_term = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for feat in self.schema:
            if search_term and search_term not in feat["name"].lower():
                continue
                
            fname = feat["name"]
            status = status_map.get(fname, "UNKNOWN")
            
            # Format live value
            lval = live_vals.get(fname, "N/A")
            if isinstance(lval, float):
                lval_str = f"{lval:.2f}"
            else:
                lval_str = str(lval)
                
            self.tree.insert("", "end", values=(
                fname,
                feat["desc"],
                feat["unit"],
                feat["type"],
                feat["min"],
                feat["max"],
                feat["avg"],
                feat["std"],
                lval_str,
                status
            ), tags=(status,))

    def _periodic_refresh(self):
        self._refresh_data()
        self.after(2000, self._periodic_refresh)

    def _refresh_data(self):
        # Overview
        ov = DatasetIntrospector.get_dataset_overview()
        self.lbls_ov["name"].config(text=ov.get("Dataset Name"))
        self.lbls_ov["ver"].config(text=ov.get("Dataset Version"))
        self.lbls_ov["samples"].config(text=ov.get("Total Samples"))
        self.lbls_ov["features"].config(text=ov.get("Number of Features"))
        self.lbls_ov["classes"].config(text=ov.get("Number of Target Classes"))
        self.lbls_ov["cdate"].config(text=ov.get("Dataset Creation Date"))
        self.lbls_ov["tdate"].config(text=ov.get("Last Training Date"))
        self.lbls_ov["source"].config(text=ov.get("Dataset Source"))
        
        # DQ Summary
        eval_data = DataQualityMonitor.get_latest_evaluation()
        score = eval_data.get("score", 0.0)
        sc_col = CLR_NORMAL if score >= 90 else (CLR_WARNING if score >= 70 else CLR_CRITICAL)
        
        self.lbls_dq["score"].config(text=f"{score:.1f}%", fg=sc_col)
        self.lbls_dq["missing_pct"].config(text=f"{eval_data.get('missing_pct', 0.0):.1f}%")
        self.lbls_dq["invalid"].config(text=str(eval_data.get("invalid_count", 0)))
        self.lbls_dq["dup"].config(text=str(eval_data.get("duplicate_count", 0)))
        self.lbls_dq["comp"].config(text=f"{eval_data.get('completeness', 0.0):.1f}%")
        self.lbls_dq["avail"].config(text=eval_data.get("feature_availability", "0/0"))
        
        missing = eval_data.get("missing_count", 0)
        self.lbls_dq["missing_feat"].config(text=str(missing), fg=CLR_CRITICAL if missing > 0 else TEXT_PRIMARY)
        
        compat = eval_data.get("compatibility", "Unknown")
        cmp_col = CLR_NORMAL if compat == "Optimal" else (CLR_CRITICAL if compat == "Critical" else CLR_WARNING)
        self.lbls_dq["compat"].config(text=compat, fg=cmp_col)
        
        self._refresh_tree()

    def _export(self, format_type):
        ov = DatasetIntrospector.get_dataset_overview()
        schema = self.schema
        
        if format_type == "json":
            fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if fp:
                try:
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump({"overview": ov, "schema": schema}, f, indent=4)
                    messagebox.showinfo("Export", "JSON Dataset Metadata Export Successful!")
                except Exception as e:
                    messagebox.showerror("Export", f"Export failed: {e}")
        elif format_type == "csv":
            fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if fp:
                try:
                    with open(fp, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        # Overview block
                        w.writerow(["--- DATASET OVERVIEW ---"])
                        for k, v in ov.items():
                            w.writerow([k, v])
                        w.writerow([])
                        # Schema block
                        w.writerow(["--- FEATURE SCHEMA ---"])
                        if schema:
                            w.writerow(schema[0].keys())
                            for row in schema:
                                w.writerow(row.values())
                    messagebox.showinfo("Export", "CSV Dataset Metadata Export Successful!")
                except Exception as e:
                    messagebox.showerror("Export", f"Export failed: {e}")
