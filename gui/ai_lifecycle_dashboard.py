"""
gui/ai_lifecycle_dashboard.py
=============================
Executive Dashboard for ML-Ops and AI Lifecycle Management.
Displays model registry, performance, data quality, and drift status.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM, FONT_MONO_MD
)
from gui.i18n import tr
from gui.widgets import KPICard

class AILifecycleDashboard(tk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self._build_ui()
        
    def _build_ui(self):
        # 1. Header
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        tk.Label(header, text=tr("ADAPTIVE AI & MODEL LIFECYCLE MANAGEMENT"),
                 bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(pady=15, padx=20, anchor="w")
                 
        # Content Container
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left Panel (Registry & Stats)
        left_panel = tk.Frame(content, bg=BG_PRIMARY)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right Panel (Data Quality & Drift)
        right_panel = tk.Frame(content, bg=BG_PRIMARY)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # --- LEFT PANEL ---
        # 1. Model Registry
        reg_frame = tk.LabelFrame(left_panel, text=tr("Model Registry (Deployed)"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        reg_frame.pack(fill="x", pady=(0, 15))
        
        # Simple Treeview for registry
        style = ttk.Style()
        style.configure("Registry.Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=30)
        style.map("Registry.Treeview", background=[("selected", BORDER)])
        
        cols = ("Name", "Version", "Algorithm", "Status")
        self.tree = ttk.Treeview(reg_frame, columns=cols, show="headings", height=4, style="Registry.Treeview")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="x", padx=10, pady=10)
        
        # 2. Performance Monitoring
        perf_frame = tk.LabelFrame(left_panel, text=tr("Live Inference Statistics"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        perf_frame.pack(fill="both", expand=True)
        
        self.stats_cards = {}
        # We'll dynamically create labels for each model's stats
        self.stats_container = tk.Frame(perf_frame, bg=BG_SECONDARY)
        self.stats_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- RIGHT PANEL ---
        # 1. Dataset Quality
        qual_frame = tk.LabelFrame(right_panel, text=tr("Real-Time Dataset Quality"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        qual_frame.pack(fill="x", pady=(0, 15))
        
        qual_inner = tk.Frame(qual_frame, bg=BG_SECONDARY)
        qual_inner.pack(pady=10)
        
        self.lbl_quality_score = tk.Label(qual_inner, text="100.0%", fg=CLR_NORMAL, bg=BG_SECONDARY, font=("Segoe UI", 32, "bold"))
        self.lbl_quality_score.pack()
        tk.Label(qual_inner, text="Data Quality Score", fg=TEXT_SECONDARY, bg=BG_SECONDARY, font=FONT_LABEL).pack()
        
        self.lbl_quality_issues = tk.Label(qual_frame, text="No issues detected.", fg=TEXT_PRIMARY, bg=BG_SECONDARY, font=FONT_LABEL_SM, justify="left")
        self.lbl_quality_issues.pack(anchor="w", padx=15, pady=(0, 10))
        
        # 2. Data Drift Detector
        drift_frame = tk.LabelFrame(right_panel, text=tr("Data Drift Detection"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        drift_frame.pack(fill="both", expand=True)
        
        self.lbl_drift_status = tk.Label(drift_frame, text="NO DRIFT DETECTED", fg=CLR_NORMAL, bg=BG_SECONDARY, font=("Segoe UI", 16, "bold"))
        self.lbl_drift_status.pack(pady=10)
        
        self.txt_drift_warnings = tk.Text(drift_frame, height=8, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_LABEL, bd=0, highlightthickness=1, highlightbackground=BORDER)
        self.txt_drift_warnings.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def _update_tree(self, models):
        self.tree.delete(*self.tree.get_children())
        for m in models:
            self.tree.insert("", "end", values=(m.get("name"), m.get("version"), m.get("algorithm"), m.get("status")))
            
    def _update_stats(self, stats):
        # Clear old stats
        for widget in self.stats_container.winfo_children():
            widget.destroy()
            
        for model_id, st in stats.items():
            row = tk.Frame(self.stats_container, bg=BG_SECONDARY)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=model_id, fg=TEXT_PRIMARY, bg=BG_SECONDARY, font=FONT_LABEL, width=15, anchor="w").pack(side="left")
            
            lat = st.get("avg_latency_ms", 0.0)
            conf = st.get("avg_confidence", 0.0)
            succ = st.get("successful_predictions", 0)
            
            tk.Label(row, text=f"Latency: {lat:.1f}ms", fg=TEXT_SECONDARY, bg=BG_SECONDARY, font=FONT_LABEL, width=15).pack(side="left")
            tk.Label(row, text=f"Conf: {conf:.1f}%", fg=TEXT_SECONDARY, bg=BG_SECONDARY, font=FONT_LABEL, width=15).pack(side="left")
            tk.Label(row, text=f"Success: {succ}", fg=TEXT_SECONDARY, bg=BG_SECONDARY, font=FONT_LABEL, width=15).pack(side="left")
            
    def update_dashboard(self, lifecycle_data: Dict[str, Any]):
        """Update dashboard with data from LifecycleEngine."""
        if not lifecycle_data: return
        
        # Registry
        self._update_tree(lifecycle_data.get("models", []))
        
        # Stats
        self._update_stats(lifecycle_data.get("stats", {}))
        
        # Quality
        score = lifecycle_data.get("quality_score", 100.0)
        color = CLR_NORMAL if score > 90 else (CLR_WARNING if score > 70 else CLR_CRITICAL)
        self.lbl_quality_score.config(text=f"{score:.1f}%", fg=color)
        
        issues = lifecycle_data.get("quality_issues", [])
        if issues:
            self.lbl_quality_issues.config(text="\n".join(issues[:3])) # Show top 3
        else:
            self.lbl_quality_issues.config(text="No issues detected.")
            
        # Drift
        warnings = lifecycle_data.get("drift_warnings", [])
        if warnings:
            self.lbl_drift_status.config(text="DRIFT DETECTED", fg=CLR_WARNING)
            self.txt_drift_warnings.delete("1.0", tk.END)
            for w in warnings:
                self.txt_drift_warnings.insert(tk.END, f"[WARNING] {w}\n")
        else:
            self.lbl_drift_status.config(text="NO DRIFT DETECTED", fg=CLR_NORMAL)
            self.txt_drift_warnings.delete("1.0", tk.END)
            self.txt_drift_warnings.insert(tk.END, "Training distribution matches real-time distribution.\nNo action required.")
