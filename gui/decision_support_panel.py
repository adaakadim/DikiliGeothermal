"""
gui/decision_support_panel.py
=============================
Executive Decision Support Dashboard.
Displays the unified AI assessment and prioritized maintenance actions.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_INFO,
    FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM, FONT_HEADER_BAR
)
from gui.i18n import tr

class DecisionSupportPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, on_navigate=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.on_navigate = on_navigate
        self._build_ui()
        
    def _build_ui(self):
        # 1. Header
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        tk.Label(header, text=tr("UNIFIED AI DECISION SUPPORT"),
                 bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(pady=15, padx=20, anchor="w")
                 
        # Content Container
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Right Panel (Action List) - Now at the Top
        right_panel = tk.Frame(content, bg=BG_PRIMARY)
        right_panel.pack(side="top", fill="both", expand=True, pady=(0, 15))

        # Left Panel (Critical Assessment) - Now at the Bottom
        left_panel = tk.Frame(content, bg=BG_PRIMARY)
        left_panel.pack(side="bottom", fill="x", expand=False)
        
        # --- LEFT PANEL ---
        # 1. Highest Priority Equipment
        self.lbl_crit_eq = tk.LabelFrame(left_panel, text=tr("Highest Priority Equipment Assessment"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        self.lbl_crit_eq.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        
        self.lbl_eq_name = tk.Label(self.lbl_crit_eq, text="N/A", font=("Segoe UI", 24, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY)
        self.lbl_eq_name.pack(anchor="w", pady=(5, 10))
        
        # Grid for assessment attributes
        self.attr_frame = tk.Frame(self.lbl_crit_eq, bg=BG_SECONDARY)
        self.attr_frame.pack(fill="x", expand=True)
        
        self.vars = {}
        attrs = [
            "Overall Risk", "Equipment Health", "Remaining Useful Life",
            "Maintenance Priority", "Estimated Maintenance Window",
            "Recommended Action", "Primary Root Cause", "Overall AI Confidence"
        ]
        for i, attr in enumerate(attrs):
            tk.Label(self.attr_frame, text=f"{attr}:", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 20))
            var = tk.StringVar(value="---")
            self.vars[attr] = var
            tk.Label(self.attr_frame, textvariable=var, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM, wraplength=300, justify="left").grid(row=i, column=1, sticky="w", pady=4)
            
        # --- RIGHT PANEL ---
        # Prioritized Actions
        act_frame = tk.LabelFrame(right_panel, text=tr("Prioritized Engineering Actions"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        act_frame.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.configure("Actions.Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=40, font=FONT_LABEL_SM)
        style.map("Actions.Treeview", background=[("selected", BORDER)])
        
        cols = ("Priority", "Equipment", "Action", "Impact", "Source")
        self.tree = ttk.Treeview(act_frame, columns=cols, show="headings", style="Actions.Treeview")
        
        self.tree.heading("Priority", text="Priority")
        self.tree.column("Priority", width=80, anchor="center", stretch=True)
        
        self.tree.heading("Equipment", text="Equipment")
        self.tree.column("Equipment", width=100, anchor="center", stretch=True)
        
        self.tree.heading("Action", text="Action")
        self.tree.column("Action", width=450, anchor="w", stretch=True)
        
        self.tree.heading("Impact", text="Impact")
        self.tree.column("Impact", width=250, anchor="w", stretch=True)
        
        self.tree.heading("Source", text="Source System")
        self.tree.column("Source", width=150, anchor="center", stretch=True)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Configure>", self._on_tree_resize)
        
    def _on_tree_resize(self, event):
        if event.width > 50:
            w = event.width
            self.tree.column("Priority", width=int(w * 0.08))
            self.tree.column("Equipment", width=int(w * 0.10))
            self.tree.column("Action", width=int(w * 0.42))
            self.tree.column("Impact", width=int(w * 0.25))
            self.tree.column("Source", width=int(w * 0.15))

    def _on_tree_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0], "values")
        if len(item) > 1:
            eq_id = item[1]  # Equipment ID is column 1
            if self.on_navigate:
                self.on_navigate(eq_id)
        
    def update_dashboard(self, assessments: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """Update the dashboard with fused AI data."""
        # Find highest priority equipment
        crit_eq = "None"
        max_score = -1
        crit_assessment = None
        
        for eq_id, ass in assessments.items():
            risk = ass.get("Overall Risk", "LOW")
            score = 100 if risk == "CRITICAL" else (75 if risk == "HIGH" else (50 if risk == "MODERATE" else 0))
            if score > max_score:
                max_score = score
                crit_eq = eq_id
                crit_assessment = ass
                
        if crit_assessment:
            self.lbl_eq_name.config(text=crit_eq, fg=CLR_CRITICAL if max_score >= 75 else CLR_WARNING if max_score == 50 else CLR_NORMAL)
            for k, v in crit_assessment.items():
                if k in self.vars:
                    self.vars[k].set(str(v))
        else:
            self.lbl_eq_name.config(text="SYSTEM NORMAL", fg=CLR_NORMAL)
            for k in self.vars:
                self.vars[k].set("---")
                
        # Update Treeview
        self.tree.delete(*self.tree.get_children())
        for rec in recommendations:
            self.tree.insert("", "end", values=(
                rec.get("priority"),
                rec.get("equipment"),
                rec.get("action"),
                rec.get("impact"),
                rec.get("source")
            ))
