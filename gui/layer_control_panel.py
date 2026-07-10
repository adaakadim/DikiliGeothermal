import tkinter as tk
from core.configuration import config
from gui.theme import BG_SECONDARY, BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_LABEL, FONT_LABEL_SM, BORDER
from gui.i18n import tr

class LayerControlPanel(tk.Frame):
    """
    Dedicated sidebar for toggling visualization layers on the Digital Twin.
    Saves state to configuration.
    """
    def __init__(self, parent: tk.Widget, diagram=None, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
        self.diagram = diagram
        self.config = config
        
        self.layers = {
            "pipeline": "Pipeline Layer",
            "sensor": "Sensor Layer",
            "ai": "AI Layer",
            "alarm": "Alarm Layer",
            "maintenance": "Maintenance Layer",
            "thermal": "Thermal Layer"
        }
        
        self._vars = {}
        self._build_ui()
        
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=tr("LAYER CONTROL"), bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=(15, 10))
        
        # Checkbuttons
        content = tk.Frame(self, bg=BG_SECONDARY)
        content.pack(fill="both", expand=True, padx=15, pady=10)
        
        for layer_key, layer_name in self.layers.items():
            # Load from config, default True
            initial_state = self.config.get(f"ui.layers.{layer_key}", True)
            
            var = tk.BooleanVar(value=initial_state)
            self._vars[layer_key] = var
            
            cb = tk.Checkbutton(
                content, 
                text=tr(layer_name), 
                variable=var, 
                bg=BG_SECONDARY, 
                fg=TEXT_SECONDARY,
                selectcolor=BG_HEADER,
                activebackground=BG_SECONDARY,
                activeforeground=TEXT_PRIMARY,
                font=FONT_LABEL_SM,
                anchor="w",
                command=lambda k=layer_key: self._on_toggle(k)
            )
            cb.pack(fill="x", pady=8)
            
    def _on_toggle(self, layer_key: str):
        state = self._vars[layer_key].get()
        # Save to config
        self.config.set(f"ui.layers.{layer_key}", state)
        self.config.save()
        
        # Update Diagram
        if self.diagram:
            self.diagram.set_layer_visibility(layer_key, state)
