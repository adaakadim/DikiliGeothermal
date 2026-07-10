"""
hmi/overview/overview_panel.py
==============================
Main process overview screen for the HMI.
Embeds the Digital Twin Process Diagram and provides dedicated animation ticks.
"""

import tkinter as tk
import logging
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_SUBTITLE
from gui.widgets import KPICard
from gui.i18n import tr
from digital_twin.visualization.diagram import ProcessDiagram
from gui.search_bar import EquipmentSearchBar

logger = logging.getLogger(__name__)

class OverviewPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, well_ids: list, on_equip_click=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        header = tk.Frame(self, bg=BG_HEADER)
        header.grid(row=0, column=0, sticky="ew")
        
        self.lbl_title = tk.Label(header, text=tr("Plant Overview"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        self.lbl_title.pack(side="left", padx=10)
        
        # Add Search Bar
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
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(1, weight=1)
        
        # We wrap the existing Process Diagram and center it
        self.diagram = ProcessDiagram(self, on_equip_click=on_equip_click)
        self.diagram.grid(row=1, column=0, sticky="nsew")
        
        from gui.layer_control_panel import LayerControlPanel
        self.layer_panel = LayerControlPanel(self, diagram=self.diagram)
        self.layer_panel.grid(row=1, column=1, sticky="ns", padx=(0, 0))
        
        self._current_facility = None

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
