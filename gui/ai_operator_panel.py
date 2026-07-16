import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from analytics.ai.operator_assistant import AIAssessment
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, BG_SECONDARY

class AIOperatorPanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header Area
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header_frame, text="AI Operator Assistant", font=FONT_TITLE).pack(side=tk.LEFT)
        
        self.lbl_status = ttk.Label(header_frame, text="Status: UNKNOWN", font=FONT_SUBTITLE, foreground="#94a3b8")
        self.lbl_status.pack(side=tk.RIGHT)

        # Dashboard layout using PanedWindow or Frames
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left Column: Situation & Equipment Summary
        left_col = ttk.Frame(content)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self._build_situation_section(left_col)
        self._build_equipment_section(left_col)
        
        # Right Column: Recommendations
        right_col = ttk.Frame(content)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self._build_recommendations_section(right_col)
        
    def _build_situation_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Current Situation", padding=15)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.lbl_confidence = ttk.Label(frame, text="AI Confidence: --%", font=FONT_LABEL)
        self.lbl_confidence.pack(anchor=tk.W, pady=(0, 10))
        
        self.txt_situation = tk.Text(frame, height=6, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED, bd=0, highlightthickness=0)
        self.txt_situation.pack(fill=tk.BOTH, expand=True)

    def _build_equipment_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Equipment Summary", padding=15)
        frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # We will use a Treeview to list equipment health
        cols = ("equipment", "health", "status")
        self.tree_equip = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        self.tree_equip.heading("equipment", text="Equipment")
        self.tree_equip.heading("health", text="Health (%)")
        self.tree_equip.heading("status", text="Status")
        
        self.tree_equip.column("equipment", width=150)
        self.tree_equip.column("health", width=100, anchor=tk.CENTER)
        self.tree_equip.column("status", width=100, anchor=tk.CENTER)
        
        self.tree_equip.pack(fill=tk.BOTH, expand=True)

    def _build_recommendations_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Actionable Recommendations", padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Operations
        ttk.Label(frame, text="Operational Actions", font=FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 5))
        self.txt_op_recs = tk.Text(frame, height=5, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED, bd=0, highlightthickness=0)
        self.txt_op_recs.pack(fill=tk.X, pady=(0, 15))
        
        # Maintenance
        ttk.Label(frame, text="Maintenance Prioritization", font=FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 5))
        self.txt_maint_recs = tk.Text(frame, height=5, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED, bd=0, highlightthickness=0)
        self.txt_maint_recs.pack(fill=tk.X, pady=(0, 15))
        
        # Energy
        ttk.Label(frame, text="Energy Optimization", font=FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 5))
        self.txt_eng_recs = tk.Text(frame, height=5, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED, bd=0, highlightthickness=0)
        self.txt_eng_recs.pack(fill=tk.X)

    def _update_text(self, widget: tk.Text, items: list):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        if not items:
            widget.insert(tk.END, "• None\n")
        else:
            for item in items:
                widget.insert(tk.END, f"• {item}\n")
        widget.config(state=tk.DISABLED)

    def update_dashboard(self, assessment: AIAssessment):
        """Called by the main loop to update the panel."""
        self.lbl_status.config(text=f"Plant Status: {assessment.plant_status}")
        self.lbl_confidence.config(text=f"AI Confidence: {assessment.confidence_score:.1f}%")
        
        # Update Equipment Tree
        for item in self.tree_equip.get_children():
            self.tree_equip.delete(item)
            
        for eq_id, health in assessment.health_summary.items():
            status = "CRITICAL" if health.health_score < 40 else ("WARNING" if health.health_score < 75 else "NORMAL")
            self.tree_equip.insert("", tk.END, values=(eq_id, f"{health.health_score:.1f}", status))
            
        # Update Recommendations
        self._update_text(self.txt_op_recs, assessment.operational_recs)
        self._update_text(self.txt_maint_recs, assessment.maintenance_recs)
        self._update_text(self.txt_eng_recs, assessment.energy_opt_recs)
        
        # Synthesize a situation string
        situation = []
        if assessment.plant_status == "NORMAL":
            situation.append("Plant is operating within normal parameters.")
        elif assessment.plant_status == "WARNING":
            situation.append("Plant requires attention. Some equipment is degrading.")
        else:
            situation.append("CRITICAL: Immediate action required to prevent failure.")
            
        if assessment.alarm_explanations:
            situation.extend(assessment.alarm_explanations)
            
        self._update_text(self.txt_situation, situation)
