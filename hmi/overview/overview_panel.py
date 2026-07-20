"""
hmi/overview/overview_panel.py
==============================
Main process overview screen for the HMI.
Embeds the Digital Twin Process Diagram, KPI Cards, and AI Insights.
"""

import tkinter as tk
import tkinter.ttk as ttk
import logging
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM, FONT_MONO_MD, FONT_TITLE, CLR_NORMAL, CLR_WARNING, CLR_CRITICAL
from gui.widgets import KPICard
from gui.i18n import tr
from digital_twin.visualization.diagram import ProcessDiagram
from gui.search_bar import EquipmentSearchBar
from gui.widgets import ToggleSwitch

logger = logging.getLogger(__name__)

class DashboardKPICard(tk.Frame):
    def __init__(self, parent, title, initial_value="-", unit="", icon="■", **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
        self.pack_propagate(False)
        self.config(height=115)
        
        def on_enter(e):
            self.config(highlightbackground="#3b82f6", highlightthickness=1)
            self.lbl_title.config(fg=TEXT_PRIMARY)
        def on_leave(e):
            self.config(highlightbackground=BORDER, highlightthickness=1)
            self.lbl_title.config(fg=TEXT_SECONDARY)
            
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        
        hdr = tk.Frame(self, bg=BG_SECONDARY)
        hdr.pack(side="top", fill="x", padx=12, pady=(10, 0))
        
        icon_lbl = tk.Label(hdr, text=icon, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        icon_lbl.pack(side="left", padx=(0, 6))
        
        self.lbl_title = tk.Label(hdr, text=title, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, anchor="w")
        self.lbl_title.pack(side="left", fill="x", expand=True)
        
        self.lbl_trend = tk.Label(hdr, text="► Stable", bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_LABEL_SM)
        self.lbl_trend.pack(side="right")
        
        val_frame = tk.Frame(self, bg=BG_SECONDARY)
        val_frame.pack(side="top", fill="both", expand=True, padx=12, pady=(4, 10))
        
        self.lbl_val = tk.Label(val_frame, text=initial_value, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Consolas", 20, "bold"), anchor="sw")
        self.lbl_val.pack(side="left", anchor="sw")
        
        self.lbl_unit = tk.Label(val_frame, text=unit, bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_LABEL_SM, anchor="sw")
        self.lbl_unit.pack(side="left", padx=(6, 0), pady=(0, 6), anchor="sw")

        for child in [hdr, icon_lbl, self.lbl_title, self.lbl_trend, val_frame, self.lbl_val, self.lbl_unit]:
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def set_value(self, val, color=None, trend=None, trend_color=None):
        self.lbl_val.config(text=str(val))
        if color: self.lbl_val.config(fg=color)
        else: self.lbl_val.config(fg=TEXT_PRIMARY)
        if trend: self.lbl_trend.config(text=trend)
        if trend_color: self.lbl_trend.config(fg=trend_color)

class OverviewPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, well_ids: list, on_equip_click=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        # ── Header ──
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(side="top", fill="x")
        
        self.lbl_title = tk.Label(header, text=tr("Plant Overview"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        self.lbl_title.pack(side="left", padx=15, pady=10)
        
        # Center search bar using expand/fill or careful packing
        self.search_bar = EquipmentSearchBar(
            header,
            facility_provider=self._get_facility,
            on_select=self._on_search_select
        )
        self.search_bar.pack(side="left", padx=(100, 20), pady=12)
        
        sim_frame = tk.Frame(header, bg=BG_HEADER)
        sim_frame.pack(side="right", padx=20, pady=12)
        tk.Label(sim_frame, text="SIMULATION MODE", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(side="left", padx=10)
        
        self.sim_var = tk.BooleanVar(value=False)
        self.chk_sim = ToggleSwitch(sim_frame, is_on=False, command=self._on_sim_toggle, width=44, height=22)
        self.chk_sim.pack(side="left")
        self.on_sim_toggle_cb = None
        
        # ── Main Content Area ──
        main_content = tk.Frame(self, bg=BG_PRIMARY)
        main_content.pack(side="top", fill="both", expand=True, padx=20, pady=15)
        
        # Grid layout for main content
        main_content.columnconfigure(0, weight=1) # Digital Twin (Flexible)
        main_content.columnconfigure(1, weight=0, minsize=300) # AI Insights (Fixed 300px)
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
        kpi_specs = [
            ("Production", "t/h", "📦"),
            ("Steam Flow", "t/h", "💨"),
            ("Temperature", "°C", "🌡️"),
            ("Pressure", "bar", "⏱️"),
            ("Power", "MW", "⚡"),
            ("Efficiency", "%", "⚙️"),
            ("Active Alarms", "", "⚠️"),
            ("AI Status", "", "🧠")
        ]
        
        for i, (name, unit, icon) in enumerate(kpi_specs):
            self.kpi_bar.columnconfigure(i, weight=1, uniform="kpi")
            card = DashboardKPICard(self.kpi_bar, name, unit=unit, icon=icon)
            card.grid(row=0, column=i, sticky="nsew", padx=15, pady=4)
            self.kpis[name] = card

        # Right Side (AI Insights + Layer Control)
        right_frame = tk.Frame(main_content, bg=BG_PRIMARY, width=300)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        right_frame.grid_propagate(False)
        right_frame.pack_propagate(False)
        
        self._build_ai_insights_panel(right_frame)
        
        # Collapsible Layer Control
        self._build_layer_control(right_frame)
        
        self._current_facility = None

    def _build_ai_insights_panel(self, parent):
        insights_panel = tk.Frame(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        insights_panel.pack(side="top", fill="both", expand=True)
        
        lbl_ai_title = tk.Label(insights_panel, text="Enterprise AI Insights", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE, anchor="w", padx=15, pady=12)
        lbl_ai_title.pack(side="top", fill="x")
        
        self.cards_frame = tk.Frame(insights_panel, bg=BG_PRIMARY)
        self.cards_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.cards_frame.columnconfigure(0, weight=1)
            
        self.ai_cards = {}
        
        self._add_ai_card("Overall AI Status", "System Status", 0)
        self._add_ai_card("Risk Score", "Current failure risk", 1, with_progress=True)
        self._add_ai_card("Confidence Score", "Model confidence", 2, with_progress=True)
        self._add_ai_card("Equipment Health", "Remaining health", 3, with_progress=True)
        self._add_ai_card("Remaining Useful Life", "Estimated by AI", 4, with_progress=True)
        self._add_ai_card("AI Prediction", "Predicted outcome", 5)
        self._add_ai_card("Recommendation", "Prescriptive actions", 6, rowspan=2, val_font=FONT_LABEL)
        
        self.cards_frame.rowconfigure(6, weight=1)

    def _add_ai_card(self, title, desc, row, with_progress=False, rowspan=1, val_font=None):
        card = tk.Frame(self.cards_frame, bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=row, column=0, rowspan=rowspan, sticky="nsew", padx=4, pady=4)
        
        def on_enter(e): card.config(highlightbackground="#64748b")
        def on_leave(e): card.config(highlightbackground=BORDER)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        top = tk.Frame(card, bg=BG_TERTIARY)
        top.pack(fill="x", padx=12, pady=(8, 2))
        
        lbl_title = tk.Label(top, text=title, bg=BG_TERTIARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        lbl_title.pack(side="left")
        
        lbl_desc = tk.Label(top, text=desc, bg=BG_TERTIARY, fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="e")
        lbl_desc.pack(side="right")
        
        v_font = val_font if val_font else (FONT_MONO_MD if not title in ["Current Prediction", "Recommendation"] else FONT_LABEL)
        val = tk.Label(card, text="-", bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=v_font, anchor="w", justify="left")
        val.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        
        def _on_resize(event, label=val):
            label.config(wraplength=max(50, event.width - 24))
            
        card.bind("<Configure>", _on_resize)
        
        self.ai_cards[title] = {"lbl": val, "body": card, "card": card}
        
        if with_progress:
            canvas = tk.Canvas(card, bg=BG_SECONDARY, height=6, highlightthickness=0)
            canvas.pack(side="bottom", fill="x", padx=12, pady=(0, 8))
            self.ai_cards[title]["canvas"] = canvas
            
        for child in [top, lbl_title, lbl_desc, val]:
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

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
        
    def _on_sim_toggle(self, is_sim: bool):
        self.sim_var.set(is_sim)
        if is_sim:
            self.lbl_title.config(text=tr("Plant Overview (SIMULATION)"), fg="#f59e0b")
        else:
            self.lbl_title.config(text=tr("Plant Overview"), fg=TEXT_PRIMARY)
            
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
                trend_txt = "► Stable"
                trend_col = TEXT_MUTED
                
                if k == "Active Alarms":
                    color = CLR_CRITICAL if int(v) > 0 else CLR_NORMAL
                    trend_txt = f"{v} Active" if int(v) > 0 else "All Clear"
                    trend_col = color
                elif k == "AI Status":
                    color = CLR_CRITICAL if v in ["CRITICAL", "FAILURE"] else (CLR_WARNING if v == "WARNING" else CLR_NORMAL)
                    trend_txt = v
                    trend_col = color
                
                self.kpis[k].set_value(v, color, trend_txt, trend_col)
                
        # Update AI Insights
        if "Overall AI Status" in ai_insights:
            status_val = ai_insights["Overall AI Status"]
            if status_val == "NORMAL": status_disp = "Healthy"
            elif status_val == "WARNING": status_disp = "Warning"
            elif status_val in ["CRITICAL", "FAILURE"]: status_disp = "Critical"
            else: status_disp = status_val
            color = CLR_CRITICAL if status_disp == "Critical" else (CLR_WARNING if status_disp == "Warning" else CLR_NORMAL)
            self.ai_cards["Overall AI Status"]["lbl"].config(text=f"● {status_disp.upper()}", fg=color)

        if "Risk Score" in ai_insights:
            risk = float(ai_insights["Risk Score"])
            if risk > 70: color = CLR_CRITICAL
            elif risk > 50: color = "#f97316"
            elif risk > 30: color = CLR_WARNING
            else: color = CLR_NORMAL
            self.ai_cards["Risk Score"]["lbl"].config(text=f"{risk:.1f}%", fg=color)
            if "canvas" in self.ai_cards["Risk Score"]:
                cvs = self.ai_cards["Risk Score"]["canvas"]
                cvs.delete("all")
                w = cvs.winfo_width()
                if w <= 1: w = 150
                cvs.create_rectangle(0, 0, w, 6, fill=BG_SECONDARY, outline="")
                cvs.create_rectangle(0, 0, w * (risk/100.0), 6, fill=color, outline="")

        if "Confidence" in ai_insights:
            conf = float(ai_insights["Confidence"])
            self.ai_cards["Confidence Score"]["lbl"].config(text=f"{conf:.1f}%", fg=TEXT_PRIMARY)
            if "canvas" in self.ai_cards["Confidence Score"]:
                cvs = self.ai_cards["Confidence Score"]["canvas"]
                cvs.delete("all")
                w = cvs.winfo_width()
                if w <= 1: w = 150
                cvs.create_rectangle(0, 0, w, 6, fill=BG_SECONDARY, outline="")
                cvs.create_rectangle(0, 0, w * (conf/100.0), 6, fill="#3b82f6", outline="")
            
        if "Equipment Health" in ai_insights:
            hlth = float(ai_insights["Equipment Health"])
            h_col = CLR_NORMAL if hlth > 80 else (CLR_WARNING if hlth > 50 else CLR_CRITICAL)
            self.ai_cards["Equipment Health"]["lbl"].config(text=f"{hlth:.0f}%", fg=h_col)
            if "canvas" in self.ai_cards["Equipment Health"]:
                cvs = self.ai_cards["Equipment Health"]["canvas"]
                cvs.delete("all")
                w = cvs.winfo_width()
                if w <= 1: w = 150
                cvs.create_rectangle(0, 0, w, 6, fill=BG_SECONDARY, outline="")
                cvs.create_rectangle(0, 0, w * (hlth/100.0), 6, fill=h_col, outline="")
            
        if "RUL" in ai_insights:
            rul = float(ai_insights["RUL"])
            # Assuming RUL is 0-100% or similar. If it's hours, we need a max to scale against.
            # Let's assume max is 100 for simplicity of progress bar.
            r_col = CLR_NORMAL if rul > 50 else (CLR_WARNING if rul > 20 else CLR_CRITICAL)
            self.ai_cards["Remaining Useful Life"]["lbl"].config(text=f"{rul:.0f} hrs", fg=r_col)
            if "canvas" in self.ai_cards["Remaining Useful Life"]:
                cvs = self.ai_cards["Remaining Useful Life"]["canvas"]
                cvs.delete("all")
                w = cvs.winfo_width()
                if w <= 1: w = 150
                cvs.create_rectangle(0, 0, w, 6, fill=BG_SECONDARY, outline="")
                # Cap RUL at 100 for progress bar drawing
                fill_pct = min(1.0, rul / 100.0)
                cvs.create_rectangle(0, 0, w * fill_pct, 6, fill=r_col, outline="")
                
        if "Prediction" in ai_insights:
            self.ai_cards["AI Prediction"]["lbl"].config(text=str(ai_insights["Prediction"]), fg=CLR_CRITICAL if "Failure" in str(ai_insights["Prediction"]) else TEXT_PRIMARY)
            
        if "Recommendation" in ai_insights:
            rec_raw = str(ai_insights["Recommendation"])
            sentences = [s.strip() for s in rec_raw.split('.') if s.strip()]
            if len(sentences) > 1:
                rec_text = "\n".join(f"• {s}." for s in sentences)
            else:
                rec_text = rec_raw
            self.ai_cards["Recommendation"]["lbl"].config(text=rec_text, fg=TEXT_PRIMARY)
