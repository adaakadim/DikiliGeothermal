"""
hmi/overview/overview_panel.py
==============================
Main process overview screen for the HMI.
Embeds the Digital Twin Process Diagram, KPI Cards, and AI Insights.
"""

import tkinter as tk
import tkinter.ttk as ttk
import logging
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, FONT_SUBTITLE, FONT_LABEL_SM, FONT_MONO_MD, FONT_TITLE, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL
from gui.widgets import KPICard
from gui.i18n import tr
from digital_twin.visualization.diagram import ProcessDiagram
from gui.search_bar import EquipmentSearchBar

logger = logging.getLogger(__name__)

class DashboardKPICard(tk.Frame):
    def __init__(self, parent, title, initial_value="-", **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
        self.lbl_title = tk.Label(self, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w")
        self.lbl_title.pack(side="top", fill="x", padx=10, pady=(10, 2))
        self.lbl_val = tk.Label(self, text=initial_value, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Segoe UI", 16, "bold"), anchor="w")
        self.lbl_val.pack(side="top", fill="x", padx=10, pady=(0, 10))

    def set_value(self, val, color=None):
        self.lbl_val.config(text=str(val))
        if color:
            self.lbl_val.config(fg=color)
        else:
            self.lbl_val.config(fg=TEXT_PRIMARY)

class OverviewPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, well_ids: list, on_equip_click=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        # ── Header ──
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(side="top", fill="x")
        
        self.lbl_title = tk.Label(header, text=tr("Plant Overview"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        self.lbl_title.pack(side="left", padx=15, pady=10)
        
        self.search_bar = EquipmentSearchBar(
            header,
            facility_provider=self._get_facility,
            on_select=self._on_search_select
        )
        self.search_bar.pack(side="left", padx=40, pady=5)
        
        self.sim_var = tk.BooleanVar(value=False)
        self.chk_sim = tk.Checkbutton(
            header, text="SIMULATION MODE", variable=self.sim_var, 
            bg=BG_HEADER, fg=TEXT_PRIMARY, selectcolor=BG_SECONDARY, font=FONT_SUBTITLE,
            command=self._on_sim_toggle
        )
        self.chk_sim.pack(side="right", padx=20)
        self.on_sim_toggle_cb = None
        
        # ── Main Content Area ──
        main_content = tk.Frame(self, bg=BG_PRIMARY)
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Grid layout for main content
        main_content.columnconfigure(0, weight=7) # Digital Twin (70%)
        main_content.columnconfigure(1, weight=3) # AI Insights (30%)
        main_content.rowconfigure(0, weight=1)
        
        # Left Side (Twin + KPIs)
        left_frame = tk.Frame(main_content, bg=BG_PRIMARY)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Digital Twin
        twin_frame = tk.Frame(left_frame, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        twin_frame.pack(side="top", fill="both", expand=True)
        
        self.diagram = ProcessDiagram(twin_frame, on_equip_click=on_equip_click)
        self.diagram.pack(fill="both", expand=True)
        
        # KPI Bar (Bottom of Left Frame)
        self.kpi_bar = tk.Frame(left_frame, bg=BG_PRIMARY)
        self.kpi_bar.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Create KPI Cards
        self.kpis = {}
        kpi_names = ["Production", "Steam Flow", "Temperature", "Pressure", "Power", "Efficiency", "Energy", "Active Alarms", "AI Status"]
        
        # Using a grid inside kpi_bar to distribute cards equally
        for i, name in enumerate(kpi_names):
            self.kpi_bar.columnconfigure(i, weight=1)
            card = DashboardKPICard(self.kpi_bar, name)
            card.grid(row=0, column=i, sticky="nsew", padx=2)
            self.kpis[name] = card

        # Right Side (AI Insights + Layer Control)
        right_frame = tk.Frame(main_content, bg=BG_PRIMARY)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        self._build_ai_insights_panel(right_frame)
        
        # Collapsible Layer Control
        self._build_layer_control(right_frame)
        
        self._current_facility = None

    def _build_ai_insights_panel(self, parent):
        insights_panel = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        insights_panel.pack(side="top", fill="both", expand=True)
        
        lbl_ai_title = tk.Label(insights_panel, text="Enterprise AI Insights", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, anchor="w", padx=15, pady=10)
        lbl_ai_title.pack(side="top", fill="x")
        
        self.cards_frame = tk.Frame(insights_panel, bg=BG_PRIMARY)
        self.cards_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        for i in range(2):
            self.cards_frame.columnconfigure(i, weight=1, uniform="col")
        for i in range(4):
            self.cards_frame.rowconfigure(i, weight=1, uniform="row")
            
        self.ai_cards = {}
        
        self._add_ai_card("Overall AI Status", 0, 0)
        
        # Risk Score with Canvas
        self._add_ai_card("Risk Score", 0, 1)
        self.risk_canvas = tk.Canvas(self.ai_cards["Risk Score"]["body"], bg=BG_TERTIARY, height=6, highlightthickness=0)
        self.risk_canvas.pack(side="bottom", fill="x", pady=(5,0))
        
        self._add_ai_card("Confidence Score", 1, 0)
        self._add_ai_card("Equipment Health", 1, 1)
        self._add_ai_card("Remaining Useful Life", 2, 0)
        self._add_ai_card("Top Features (SHAP)", 2, 1)
        self._add_ai_card("Current Prediction", 3, 0)
        self._add_ai_card("Recommendation", 3, 1)
        
        self.ai_cards["Top Features (SHAP)"]["lbl"].config(
            text="Explainable AI module will display the most influential features.",
            font=FONT_LABEL_SM, fg=TEXT_MUTED
        )

    def _add_ai_card(self, title, r, c, rowspan=1, colspan=1):
        card = tk.Frame(self.cards_frame, bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=r, column=c, rowspan=rowspan, columnspan=colspan, sticky="nsew", padx=4, pady=4)
        card.pack_propagate(False)
        
        lbl = tk.Label(card, text=title, bg=BG_TERTIARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w")
        lbl.pack(side="top", fill="x", padx=8, pady=(6, 2))
        
        body = tk.Frame(card, bg=BG_TERTIARY)
        body.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 6))
        
        val = tk.Label(body, text="-", bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"), anchor="nw", justify="left", wraplength=140)
        val.pack(side="top", fill="both", expand=True)
        
        self.ai_cards[title] = {"lbl": val, "body": body, "card": card}

    def _build_layer_control(self, parent):
        layer_frame = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        layer_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.layer_visible = tk.BooleanVar(value=False)
        
        header = tk.Frame(layer_frame, bg=BG_HEADER)
        header.pack(fill="x")
        
        self.btn_layer_toggle = tk.Button(header, text="▶ Layer Control", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, 
                                          relief="flat", anchor="w", command=self._toggle_layer_control, cursor="hand2")
        self.btn_layer_toggle.pack(fill="x", padx=5, pady=5)
        
        self.layer_content = tk.Frame(layer_frame, bg=BG_SECONDARY)
        
        from gui.layer_control_panel import LayerControlPanel
        self.layer_panel = LayerControlPanel(self.layer_content, diagram=self.diagram)
        self.layer_panel.pack(fill="both", expand=True)

    def _toggle_layer_control(self):
        if self.layer_visible.get():
            self.layer_visible.set(False)
            self.layer_content.pack_forget()
            self.btn_layer_toggle.config(text="▶ Layer Control")
        else:
            self.layer_visible.set(True)
            self.layer_content.pack(fill="both", expand=True)
            self.btn_layer_toggle.config(text="▼ Layer Control")

    def _get_facility(self):
        return self._current_facility

    def _on_search_select(self, eq_id: str):
        if self._current_facility and self._current_facility.get_equipment(eq_id):
            self.diagram.focus_equipment(eq_id)
        
    def _on_sim_toggle(self):
        is_sim = self.sim_var.get()
        if is_sim:
            self.lbl_title.config(text=tr("Plant Overview [SIMULATION MODE]"), fg="#f59e0b")
            self.chk_sim.config(fg="#f59e0b")
        else:
            self.lbl_title.config(text=tr("Plant Overview"), fg=TEXT_PRIMARY)
            self.chk_sim.config(fg=TEXT_PRIMARY)
            
        if self.on_sim_toggle_cb:
            self.on_sim_toggle_cb(is_sim)
        
    def update_from_twin(self, facility):
        self._current_facility = facility
        self.diagram.update_from_twin(facility)

    def update_dashboard_data(self, kpis: dict, ai_insights: dict):
        # Update KPIs
        for k, v in kpis.items():
            if k in self.kpis:
                color = None
                if k == "Active Alarms":
                    color = CLR_CRITICAL if int(v) > 0 else CLR_NORMAL
                elif k == "AI Status":
                    color = CLR_CRITICAL if v in ["CRITICAL", "FAILURE"] else (CLR_WARNING if v == "WARNING" else CLR_NORMAL)
                
                self.kpis[k].set_value(v, color)
                
        # Update AI Insights
        # Overall AI Status
        if "Overall AI Status" in ai_insights:
            status_val = ai_insights["Overall AI Status"]
            # Map NORMAL to Healthy
            if status_val == "NORMAL": status_disp = "Healthy"
            elif status_val == "WARNING": status_disp = "Warning"
            elif status_val in ["CRITICAL", "FAILURE"]: status_disp = "Critical"
            else: status_disp = status_val
            
            color = CLR_CRITICAL if status_disp == "Critical" else (CLR_WARNING if status_disp == "Warning" else CLR_NORMAL)
            self.ai_cards["Overall AI Status"]["lbl"].config(text=status_disp, fg=color)

        # Risk Score
        if "Risk Score" in ai_insights:
            risk = float(ai_insights["Risk Score"])
            if risk > 70:
                color = "#ef4444" # Red
                sev = "Red"
            elif risk > 50:
                color = "#f97316" # Orange
                sev = "Orange"
            elif risk > 30:
                color = "#eab308" # Yellow
                sev = "Yellow"
            else:
                color = "#10b981" # Green
                sev = "Green"
            
            self.ai_cards["Risk Score"]["lbl"].config(text=f"{risk:.1f}% ({sev})", fg=color)
            
            self.risk_canvas.delete("all")
            w = self.risk_canvas.winfo_width()
            if w <= 1: w = 150 # fallback
            self.risk_canvas.create_rectangle(0, 0, w, 6, fill=BG_SECONDARY, outline="")
            self.risk_canvas.create_rectangle(0, 0, w * (risk/100.0), 6, fill=color, outline="")

        # Confidence Score
        if "Confidence" in ai_insights:
            conf = float(ai_insights["Confidence"])
            self.ai_cards["Confidence Score"]["lbl"].config(text=f"{conf:.1f}%", fg=TEXT_PRIMARY)
            
        # Equipment Health
        if "Equipment Health" in ai_insights:
            hlth = float(ai_insights["Equipment Health"])
            h_str = "Healthy" if hlth > 80 else ("Warning" if hlth > 50 else "Critical")
            h_col = CLR_NORMAL if hlth > 80 else (CLR_WARNING if hlth > 50 else CLR_CRITICAL)
            self.ai_cards["Equipment Health"]["lbl"].config(text=f"{hlth:.0f}% - {h_str}", fg=h_col)
            
        # Remaining Useful Life
        if "RUL" in ai_insights:
            rul = float(ai_insights["RUL"])
            if rul > 0:
                self.ai_cards["Remaining Useful Life"]["lbl"].config(text=f"{rul:.0f} hrs", fg=TEXT_PRIMARY)
            else:
                self.ai_cards["Remaining Useful Life"]["lbl"].config(text="Not available", fg=TEXT_MUTED)
                
        # Current Prediction
        if "Prediction" in ai_insights:
            self.ai_cards["Current Prediction"]["lbl"].config(text=str(ai_insights["Prediction"]), fg=TEXT_PRIMARY)
            
        # Recommendation
        if "Recommendation" in ai_insights:
            self.ai_cards["Recommendation"]["lbl"].config(text=str(ai_insights["Recommendation"]), fg=TEXT_PRIMARY)
