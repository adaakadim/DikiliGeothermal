import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, BG_SECONDARY, TEXT_PRIMARY
from gui.components import KPICard

class MissionControlPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        # Main Layout
        self._build_header()
        
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Rows
        self.row1 = ttk.Frame(self.content_frame)
        self.row1.pack(fill=tk.X, pady=10)
        
        self.row2 = ttk.Frame(self.content_frame)
        self.row2.pack(fill=tk.X, pady=10)
        
        self.row3 = ttk.Frame(self.content_frame)
        self.row3.pack(fill=tk.X, pady=10)
        
        # Dictionaries to store dynamic labels
        self.cards = {}
        
        # Build specific cards
        self._build_status_row()
        self._build_metrics_row()
        self._build_diagnostics_row()

    def _build_header(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        ttk.Label(header_frame, text="MISSION CONTROL", font=FONT_TITLE).pack(side=tk.LEFT)

    def _create_card(self, parent, key: str, title: str, default_val: str, unit: str = ""):
        card = KPICard(parent, title=title, unit=unit, default_val=default_val)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.cards[key] = card

    def _build_status_row(self):
        self._create_card(self.row1, "plant_status", "Plant Status", "NORMAL")
        self._create_card(self.row1, "health", "Overall Plant Health", "100%")
        self._create_card(self.row1, "ai_conf", "AI Confidence", "100%")
        self._create_card(self.row1, "op_mode", "Operating Mode", "WINTER")

    def _build_metrics_row(self):
        self._create_card(self.row2, "prod_flow", "Production Flow", "0.0", "kg/s")
        self._create_card(self.row2, "heat_out", "Heat Output", "0.0", "MW")
        self._create_card(self.row2, "energy_prod", "Energy Production", "0.0", "MWh")
        self._create_card(self.row2, "dh_demand", "DH Demand", "0.0", "MW")
        self._create_card(self.row2, "inj_flow", "Injection Flow", "0.0", "kg/s")

    def _build_diagnostics_row(self):
        self._create_card(self.row3, "risk_equip", "Highest Risk Equipment", "None")
        self._create_card(self.row3, "maint_due", "Maintenance Due", "None")
        self._create_card(self.row3, "alarms", "Active Alarms", "0")
        self._create_card(self.row3, "incidents", "Recent Incidents", "0")

    def _update_card_color(self, key: str, severity: str):
        # We don't need this anymore since KPICard manages its own color update
        pass

    def update_dashboard(self, snapshot: Dict[str, Any]):
        """Update all cards using a snapshot dictionary."""
        
        def set_val(key: str, val: Any, color: str = None):
            if key in self.cards:
                try:
                    num_val = float(val) if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.','',1).isdigit()) else 0
                except ValueError:
                    num_val = 0
                self.cards[key].update_value(num_val, str(val), color or TEXT_PRIMARY)

        # Smart color helper
        def get_color(val, thresholds, inverse=False):
            """Returns color based on thresholds (warn, crit)."""
            adv, warn, crit = thresholds
            if not inverse:
                if val >= crit: return "#ef4444"
                if val >= warn: return "#f97316"
                if val >= adv: return "#eab308"
                return "#10b981"
            else:
                if val <= crit: return "#ef4444"
                if val <= warn: return "#f97316"
                if val <= adv: return "#eab308"
                return "#10b981"

        # --- Status Row ---
        status = snapshot.get("plant_status", "NORMAL")
        status_clr = "#10b981"
        if status == "WARNING": status_clr = "#f97316"
        elif status == "CRITICAL": status_clr = "#ef4444"
        set_val("plant_status", status, status_clr)
        
        health = snapshot.get("health", 100.0)
        set_val("health", f"{health:.1f}", get_color(health, (90, 75, 50), inverse=True))
        
        conf = snapshot.get("ai_conf", 100.0)
        set_val("ai_conf", f"{conf:.1f}", get_color(conf, (85, 70, 50), inverse=True))
        
        set_val("op_mode", snapshot.get("op_mode", "UNKNOWN"))

        # --- Metrics Row ---
        set_val("prod_flow", f"{snapshot.get('prod_flow', 0):.1f}")
        set_val("heat_out", f"{snapshot.get('heat_out', 0):.1f}")
        set_val("energy_prod", f"{snapshot.get('energy_prod', 0):.1f}")
        set_val("dh_demand", f"{snapshot.get('dh_demand', 0):.1f}")
        set_val("inj_flow", f"{snapshot.get('inj_flow', 0):.1f}")

        # --- Diagnostics Row ---
        risk_equip = snapshot.get("risk_equip", "None")
        risk_level = snapshot.get("risk_level", "LOW")
        risk_clr = "#10b981"
        if risk_level == "MEDIUM": risk_clr = "#eab308"
        elif risk_level == "HIGH": risk_clr = "#f97316"
        elif risk_level == "CRITICAL": risk_clr = "#ef4444"
        set_val("risk_equip", risk_equip, risk_clr)
        
        maint_due = snapshot.get("maint_due", "None")
        set_val("maint_due", maint_due)
        
        alarms = snapshot.get("alarms", 0)
        alarm_clr = "#ef4444" if alarms > 0 else "#10b981"
        set_val("alarms", alarms, alarm_clr)
        
        incidents = snapshot.get("incidents", 0)
        inc_clr = "#f97316" if incidents > 0 else "#10b981"
        set_val("incidents", incidents, inc_clr)
