"""
gui/simulation_panel.py
=======================
What-If Scenario Analysis dashboard.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_INFO,
    FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM, FONT_HEADER_BAR
)
from gui.i18n import tr

class SimulationPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, on_simulate_cb: Callable = None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.on_simulate_cb = on_simulate_cb
        self.live_data = {}
        self.live_ai = {}
        self._build_ui()
        
    def _build_ui(self):
        # 1. Header
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")
        tk.Label(header, text=tr("WHAT-IF SIMULATION & SCENARIO ANALYSIS"),
                 bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(pady=15, padx=20, anchor="w")
                 
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left Panel (Controls)
        left_panel = tk.Frame(content, bg=BG_PRIMARY, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # Right Panel (Results)
        right_panel = tk.Frame(content, bg=BG_PRIMARY)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # --- LEFT PANEL ---
        controls_frame = tk.LabelFrame(left_panel, text=tr("Simulation Parameters"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        controls_frame.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        
        self.sliders = {}
        
        params = [
            ("Flow Rate (m3/h)", 0, 200, 100),
            ("Heat Exchanger Efficiency", 50, 100, 85),
            ("Temperature (°C)", 80, 120, 100),
            ("Pump Operating Hours", 0, 10000, 2500)
        ]
        
        for i, (name, min_val, max_val, default_val) in enumerate(params):
            tk.Label(controls_frame, text=name, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w", pady=(10, 0))
            
            var = tk.DoubleVar(value=default_val)
            slider = ttk.Scale(controls_frame, from_=min_val, to=max_val, variable=var, orient="horizontal")
            slider.pack(fill="x", pady=2)
            
            val_lbl = tk.Label(controls_frame, textvariable=var, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM)
            val_lbl.pack(anchor="e")
            
            self.sliders[name] = var
            
        # Simulate Button
        btn_frame = tk.Frame(left_panel, bg=BG_PRIMARY)
        btn_frame.pack(fill="x", pady=20)
        
        self.btn_sim = tk.Button(btn_frame, text="RUN SIMULATION", bg="#2563eb", fg="white", font=FONT_SUBTITLE, bd=0, command=self._run_simulation)
        self.btn_sim.pack(fill="x", ipady=10)
        
        # --- RIGHT PANEL ---
        res_frame = tk.LabelFrame(right_panel, text=tr("Impact Analysis"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        res_frame.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        
        # Comparison Table
        style = ttk.Style()
        style.configure("Sim.Treeview", rowheight=35)
        
        cols = ("Metric", "Current (Live)", "Simulated", "Delta")
        self.tree = ttk.Treeview(res_frame, columns=cols, show="headings", height=6, style="Sim.Treeview")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150, anchor="center")
        self.tree.column("Metric", width=250, anchor="w")
        self.tree.pack(fill="x", padx=10, pady=10)
        
        # Add initial placeholder rows so the table is never completely empty
        initial_metrics = [
            "Pump Failure Probability (%)", 
            "Equipment Health (%)", 
            "Remaining Useful Life (Hours)", 
            "Thermal Power (MW)"
        ]
        for m in initial_metrics:
            self.tree.insert("", "end", values=(m, "Awaiting Sim.", "-", "-"))
        
        # Recommendation text
        rec_frame = tk.LabelFrame(right_panel, text=tr("Engineering Recommendation"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, bd=0, highlightthickness=1, highlightbackground=BORDER_LIGHT)
        rec_frame.pack(fill="both", expand=True, ipadx=10, ipady=10)
        
        self.lbl_rec = tk.Label(rec_frame, text="Run a simulation to see recommendations.", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "italic"), wraplength=800, justify="left")
        self.lbl_rec.pack(anchor="w", padx=10, pady=10)
        
    def set_live_state(self, live_data: Dict[str, Any], live_ai: Dict[str, Any]):
        """Called every tick by main_window to keep the baseline updated."""
        self.live_data = live_data
        self.live_ai = live_ai
        
    def _run_simulation(self):
        if not self.on_simulate_cb: return
        
        overrides = {name: var.get() for name, var in self.sliders.items()}
        sim_ai, impact = self.on_simulate_cb(self.live_data, overrides)
        
        self._update_results(sim_ai, impact)
        
    def _update_results(self, sim_ai: Dict[str, Any], impact: Dict[str, Any]):
        self.tree.delete(*self.tree.get_children())
        
        metrics = [
            ("Pump Failure Probability (%)", "Failure Risk Delta", "%"),
            ("Equipment Health (%)", "Health Delta", "%"),
            ("Remaining Useful Life (Hours)", "RUL Delta", "h"),
            ("Thermal Power (MW)", "Power Delta", "MW")
        ]
        
        for k, d_key, unit in metrics:
            live_val = self.live_ai.get(k, 0.0)
            sim_val = sim_ai.get(k, 0.0)
            delta = impact.get(d_key, 0.0)
            
            delta_str = f"+{delta:.1f} {unit}" if delta > 0 else f"{delta:.1f} {unit}"
            if delta == 0: delta_str = "-"
            
            self.tree.insert("", "end", values=(
                k,
                f"{live_val:.1f} {unit}",
                f"{sim_val:.1f} {unit}",
                delta_str
            ))
            
        self.lbl_rec.config(text=impact.get("Recommendation", ""))
