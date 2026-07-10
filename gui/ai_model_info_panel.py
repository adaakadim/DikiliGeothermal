"""
gui/ai_model_info_panel.py
==========================
Professional AI Model Information & Performance Center.
Displays metadata, versions, statuses, and performance metrics for loaded AI models.
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import json
import csv

from analytics.ai.random_forest.model_metadata import ModelMetadataIntrospector
from analytics.ai.random_forest.model_loader import ModelCache

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    FONT_LABEL, FONT_LABEL_SM, FONT_MONO_SM, FONT_TITLE, FONT_SUBTITLE, FONT_MONO_MD
)

class AIModelInfoPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        self.active_model_name = "PumpFailure_RF"
        self.models_available = ["PumpFailure_RF", "Maintenance_RF"]
        
        self._build_header()
        self._build_body()
        
        self._refresh_data()
        self.after(5000, self._periodic_refresh)

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 5))
        
        tk.Label(hdr, text="AI MODEL INFORMATION & PERFORMANCE CENTER", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(side="left", padx=10, pady=8)
        
        # Model Selector
        tk.Label(hdr, text="Select Model:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(side="left", padx=(20, 5))
        self.cb_model = ttk.Combobox(hdr, values=self.models_available, state="readonly", width=25)
        self.cb_model.current(0)
        self.cb_model.pack(side="left", padx=5)
        self.cb_model.bind("<<ComboboxSelected>>", self._on_model_select)
        
        # Export Buttons
        btn_json = tk.Button(hdr, text="Export JSON", bg="#374151", fg=TEXT_PRIMARY, relief="flat", command=lambda: self._export("json"))
        btn_json.pack(side="right", padx=(5, 10))
        btn_csv = tk.Button(hdr, text="Export CSV", bg="#10b981", fg="white", relief="flat", command=lambda: self._export("csv"))
        btn_csv.pack(side="right", padx=5)

    def _build_body(self):
        self.body = tk.Frame(self, bg=BG_PRIMARY)
        self.body.pack(fill="both", expand=True)
        
        self.body.columnconfigure(0, weight=1)
        self.body.columnconfigure(1, weight=1)
        self.body.rowconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)
        self.body.rowconfigure(2, weight=1)
        
        # 1. AI Model Information
        self.frame_info = self._create_card(self.body, "AI MODEL INFORMATION", 0, 0)
        self.lbls_info = self._create_keyval_grid(self.frame_info, [
            ("Name", "name"), ("Type", "type"), ("Algorithm", "algo"), 
            ("Active Version", "ver"), ("Training Date", "date"), 
            ("File Name", "file"), ("Status", "status")
        ])
        
        # 2. Performance Metrics
        self.frame_metrics = self._create_card(self.body, "MODEL PERFORMANCE METRICS", 0, 1)
        self.lbls_metrics = self._create_keyval_grid(self.frame_metrics, [
            ("Accuracy", "acc"), ("Precision", "prec"), ("Recall", "rec"),
            ("F1 Score", "f1"), ("ROC-AUC", "roc"), ("CV Score", "cv")
        ])
        
        # 3. Loading Status & Validation
        self.frame_status = self._create_card(self.body, "LOADING STATUS & VALIDATION", 1, 0)
        self.lbls_status = self._create_keyval_grid(self.frame_status, [
            ("Runtime Status", "run_stat"), ("Load Time (ms)", "load_ms"),
            ("Error Detail", "err"), ("Engine Ready", "eng_rdy"),
            ("Compatibility", "compat"), ("Overall Readiness", "ready")
        ])
        
        # 4. Version Management
        self.frame_versions = self._create_card(self.body, "MODEL VERSION MANAGEMENT", 1, 1)
        self.lbls_versions = self._create_keyval_grid(self.frame_versions, [
            ("Current Version", "cur_v"), ("Previous Version", "prev_v"),
            ("Archived Versions", "arch_v"), ("Description", "desc")
        ])
        
        # 5. Resource Information
        self.frame_res = self._create_card(self.body, "MODEL RESOURCE INFORMATION", 2, 0, colspan=2)
        self.lbls_res = self._create_keyval_grid(self.frame_res, [
            ("File Size", "size"), ("Total Predictions", "preds"),
            ("Average Inference (ms)", "avg_inf"), ("Last Prediction At", "last_ts")
        ])

    def _create_card(self, parent, title, row, col, colspan=1):
        f = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=4, pady=4)
        tk.Label(f, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).pack(anchor="w", padx=10, pady=(10, 5))
        return f

    def _create_keyval_grid(self, parent, fields):
        container = tk.Frame(parent, bg=BG_SECONDARY)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        container.columnconfigure(0, weight=1, minsize=150)
        container.columnconfigure(1, weight=1)
        
        labels = {}
        for i, (label_text, key) in enumerate(fields):
            tk.Label(container, text=label_text, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM).grid(row=i, column=0, sticky="w", pady=3)
            lbl_val = tk.Label(container, text="---", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM)
            lbl_val.grid(row=i, column=1, sticky="w", pady=3)
            labels[key] = lbl_val
        return labels

    def _on_model_select(self, event):
        self.active_model_name = self.cb_model.get()
        self._refresh_data()

    def _periodic_refresh(self):
        self._refresh_data()
        self.after(5000, self._periodic_refresh)

    def _refresh_data(self):
        meta = ModelMetadataIntrospector.inspect_model_versions(self.active_model_name)
        stats = ModelCache.get_model_stats(self.active_model_name)
        
        # Info
        self.lbls_info["name"].config(text=meta["model_name"])
        self.lbls_info["type"].config(text=meta["model_type"])
        self.lbls_info["algo"].config(text=meta["algorithm"])
        self.lbls_info["ver"].config(text=meta["current_version"])
        self.lbls_info["date"].config(text=meta["training_date"])
        self.lbls_info["file"].config(text=meta["file_name"])
        stat_color = CLR_NORMAL if meta["active"] else CLR_CRITICAL
        self.lbls_info["status"].config(text="Active" if meta["active"] else "Inactive", fg=stat_color)
        
        # Metrics
        mets = meta.get("metrics", {})
        self.lbls_metrics["acc"].config(text=mets.get("Accuracy", "Not Available"))
        self.lbls_metrics["prec"].config(text=mets.get("Precision", "Not Available"))
        self.lbls_metrics["rec"].config(text=mets.get("Recall", "Not Available"))
        self.lbls_metrics["f1"].config(text=mets.get("F1 Score", "Not Available"))
        self.lbls_metrics["roc"].config(text=mets.get("ROC-AUC", "Not Available"))
        self.lbls_metrics["cv"].config(text=mets.get("CV Score", "Not Available"))
        
        # Status
        load_st = stats.get("load_status", "Not Loaded")
        st_color = CLR_CRITICAL if load_st == "Error" else (CLR_NORMAL if load_st == "Ready" else CLR_WARNING)
        self.lbls_status["run_stat"].config(text=load_st, fg=st_color)
        self.lbls_status["load_ms"].config(text=f"{stats.get('load_time_ms', 0):.2f} ms")
        self.lbls_status["err"].config(text=stats.get("error") or "None", fg=CLR_CRITICAL if stats.get("error") else TEXT_PRIMARY)
        self.lbls_status["eng_rdy"].config(text="Yes" if load_st == "Ready" else "No", fg=st_color)
        self.lbls_status["compat"].config(text="Validated" if meta["active"] else "Check Needed", fg=CLR_NORMAL if meta["active"] else CLR_WARNING)
        self.lbls_status["ready"].config(text="100%" if load_st == "Ready" else "0%", fg=st_color)
        
        # Versions
        self.lbls_versions["cur_v"].config(text=meta["current_version"])
        self.lbls_versions["prev_v"].config(text=meta["previous_version"])
        self.lbls_versions["arch_v"].config(text=str(max(0, len(meta["versions_history"]) - 1)))
        self.lbls_versions["desc"].config(text="Production ready Random Forest Model")
        
        # Resources
        tot_preds = stats.get("total_predictions", 0)
        tot_time = stats.get("total_inference_ms", 0.0)
        avg = (tot_time / tot_preds) if tot_preds > 0 else 0.0
        
        self.lbls_res["size"].config(text=f"{meta['size_kb']:.1f} KB")
        self.lbls_res["preds"].config(text=str(tot_preds))
        self.lbls_res["avg_inf"].config(text=f"{avg:.2f} ms")
        self.lbls_res["last_ts"].config(text=stats.get("last_prediction_ts", "Never"))

    def _get_export_data(self):
        meta = ModelMetadataIntrospector.inspect_model_versions(self.active_model_name)
        stats = ModelCache.get_model_stats(self.active_model_name)
        return {
            "model_name": meta["model_name"],
            "version": meta["current_version"],
            "status": stats.get("load_status", "Unknown"),
            "file_size_kb": meta["size_kb"],
            "total_predictions": stats.get("total_predictions", 0),
            "average_inference_ms": stats.get("total_inference_ms", 0) / max(1, stats.get("total_predictions", 1)),
            "accuracy": meta.get("metrics", {}).get("Accuracy", "Not Available"),
            "f1_score": meta.get("metrics", {}).get("F1 Score", "Not Available")
        }

    def _export(self, format_type):
        data = self._get_export_data()
        
        if format_type == "json":
            fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if fp:
                try:
                    with open(fp, "w") as f:
                        json.dump(data, f, indent=4)
                    messagebox.showinfo("Export", "JSON Export Successful!")
                except Exception as e:
                    messagebox.showerror("Export", f"Export failed: {e}")
        elif format_type == "csv":
            fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if fp:
                try:
                    with open(fp, "w", newline="") as f:
                        w = csv.writer(f)
                        w.writerow(data.keys())
                        w.writerow(data.values())
                    messagebox.showinfo("Export", "CSV Export Successful!")
                except Exception as e:
                    messagebox.showerror("Export", f"Export failed: {e}")
