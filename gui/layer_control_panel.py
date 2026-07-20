import tkinter as tk
from core.configuration import config
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, FONT_LABEL, FONT_LABEL_SM, BORDER
from gui.i18n import tr
from gui.widgets import ToggleSwitch

class LayerControlPanel(tk.Frame):
    """
    Dedicated sidebar for toggling visualization layers on the Digital Twin.
    """
    def __init__(self, parent: tk.Widget, diagram=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
        self.diagram = diagram
        self.config = config
        
        self.layers = {
            "pipeline": ("Pipeline Network", "Show process pipes and fluid flow"),
            "sensor": ("Sensor Telemetry", "Overlay live pressure, temp, flow data"),
            "ai": ("AI Predictions", "Show predictive health and fault markers"),
            "alarm": ("Active Alarms", "Highlight zones with triggered thresholds"),
            "maintenance": ("Maintenance Schedule", "Show equipment due for service"),
            "thermal": ("Thermal Imaging", "Overlay heat maps on critical nodes")
        }
        
        self._vars = {}
        self._build_ui()
        
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=tr("OPERATOR LAYER MANAGER"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=(15, 10))
        
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=15, pady=10)
        
        for layer_key, (layer_name, desc) in self.layers.items():
            initial_state = self.config.get(f"ui.layers.{layer_key}", True)
            self._vars[layer_key] = initial_state
            
            row = tk.Frame(content, bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=6)
            
            left = tk.Frame(row, bg=BG_TERTIARY)
            left.pack(side="left", fill="both", expand=True, padx=10, pady=8)
            
            tk.Label(left, text=tr(layer_name), bg=BG_TERTIARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w").pack(fill="x")
            tk.Label(left, text=tr(desc), bg=BG_TERTIARY, fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="w").pack(fill="x")
            
            def make_cmd(key=layer_key):
                return lambda state: self._on_toggle(key, state)
                
            ts = ToggleSwitch(row, is_on=initial_state, command=make_cmd(), width=44, height=22)
            ts.pack(side="right", padx=15)
            
    def _on_toggle(self, layer_key: str, state: bool):
        self._vars[layer_key] = state
        self.config.set(f"ui.layers.{layer_key}", state)
        self.config.save()
        
        if self.diagram:
            self.diagram.set_layer_visibility(layer_key, state)
