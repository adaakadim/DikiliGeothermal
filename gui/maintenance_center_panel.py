import tkinter as tk
from tkinter import ttk
from typing import List
from datetime import datetime

from analytics.ai.maintenance_engine import MaintenanceProfile
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, BG_SECONDARY, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL
from gui.components import StatusGauge

class PredictiveMaintenanceCenterPanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self._build_header()
        self._build_table()
        
    def _build_header(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header_frame, text="Predictive Maintenance Center", font=FONT_TITLE).pack(side=tk.LEFT)
        
        self.lbl_critical = ttk.Label(header_frame, text="Critical Assets: 0", font=FONT_SUBTITLE, foreground="#ef4444")
        self.lbl_critical.pack(side=tk.RIGHT, padx=10)
        
        self.lbl_avg_health = ttk.Label(header_frame, text="Avg Health: --%", font=FONT_SUBTITLE, foreground="#94a3b8")
        self.lbl_avg_health.pack(side=tk.RIGHT, padx=10)
        
    def _build_table(self):
        # Top area for gauges
        self.gauge_frame = ttk.Frame(self)
        self.gauge_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.gauges = {}
        # We will dynamically spawn gauges here in update_dashboard if needed, or just keep it textual. 
        # Actually, let's keep the table but add a single aggregate gauge on the top right
        self.aggregate_gauge = StatusGauge(self.gauge_frame, width=150, height=150, bg="#0f172a")
        self.aggregate_gauge.pack(side=tk.RIGHT, padx=20)
        
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        cols = ("equipment", "health", "rul", "failure_prob", "priority", "est_date", "recommendations")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        
        self.tree.heading("equipment", text="Equipment")
        self.tree.heading("health", text="Health Score (%)")
        self.tree.heading("rul", text="RUL (Days)")
        self.tree.heading("failure_prob", text="Failure Prob (%)")
        self.tree.heading("priority", text="Maintenance Priority")
        self.tree.heading("est_date", text="Est. Maintenance Date")
        self.tree.heading("recommendations", text="Top Recommendation")
        
        self.tree.column("equipment", width=150)
        self.tree.column("health", width=100, anchor=tk.CENTER)
        self.tree.column("rul", width=100, anchor=tk.CENTER)
        self.tree.column("failure_prob", width=100, anchor=tk.CENTER)
        self.tree.column("priority", width=120, anchor=tk.CENTER)
        self.tree.column("est_date", width=150, anchor=tk.CENTER)
        self.tree.column("recommendations", width=300)
        
        # Priority colors
        self.tree.tag_configure("CRITICAL", background="#450a0a", foreground="#fca5a5")
        self.tree.tag_configure("HIGH", background="#431407", foreground="#fdba74")
        self.tree.tag_configure("MEDIUM", background="#422006", foreground="#fde047")
        self.tree.tag_configure("LOW", background="#022c22", foreground="#6ee7b7")
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def update_dashboard(self, profiles: List[MaintenanceProfile]):
        """Called by main loop to refresh the dashboard."""
        
        # Update Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        critical_count = 0
        total_health = 0.0
        
        for p in profiles:
            total_health += p.health_score
            if p.priority in ["CRITICAL", "HIGH"]:
                critical_count += 1
                
            top_rec = p.recommendations[0] if p.recommendations else "None"
            
            vals = (
                p.equipment_id,
                f"{p.health_score:.1f}",
                p.rul_days,
                f"{p.failure_probability:.1f}",
                p.priority,
                p.estimated_date,
                top_rec
            )
            self.tree.insert("", "end", values=vals, tags=(p.priority,))
                
        # Update gauge
        avg_health = total_health / len(profiles) if profiles else 100.0
        self.lbl_avg_health.config(text=f"Avg Health: {avg_health:.1f}%")
        self.lbl_critical.config(text=f"Critical Assets: {critical_count}")
        
        gauge_color = CLR_NORMAL
        if avg_health < 50: gauge_color = CLR_CRITICAL
        elif avg_health < 75: gauge_color = CLR_WARNING
        self.aggregate_gauge.set_value(avg_health, gauge_color)
