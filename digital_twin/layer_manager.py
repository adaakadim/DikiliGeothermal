"""
digital_twin/layer_manager.py
=============================
Layer Manager coordinating active visibility states on the Digital Twin canvas.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard fallback layers to ensure backward compatibility and boot safety
DEFAULT_LAYERS_FALLBACK = [
    {"layer_name": "background", "default_visibility": True, "rendering_order": 1},
    {"layer_name": "pipeline", "default_visibility": True, "rendering_order": 2},
    {"layer_name": "equipment", "default_visibility": True, "rendering_order": 3},
    {"layer_name": "label", "default_visibility": True, "rendering_order": 4},
    {"layer_name": "sensor", "default_visibility": True, "rendering_order": 5},
    {"layer_name": "ai", "default_visibility": True, "rendering_order": 6},
    {"layer_name": "alarm", "default_visibility": True, "rendering_order": 7},
    {"layer_name": "maintenance", "default_visibility": True, "rendering_order": 8},
    {"layer_name": "thermal", "default_visibility": True, "rendering_order": 9}
]

class LayerManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LayerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, layers_path: Optional[str] = None):
        if self._initialized:
            return
            
        self._layers: Dict[str, Dict[str, Any]] = {}
        self._visibility_state: Dict[str, bool] = {}
        
        if layers_path is None:
            layers_path = os.path.join(os.path.dirname(__file__), "..", "layouts", "layers.json")
            
        self.load_layers(layers_path)
        self._initialized = True

    def load_layers(self, layers_path: str):
        """Loads and parses layer configurations from external JSON."""
        if not os.path.exists(layers_path):
            logger.warning(f"Layers configuration file not found at {layers_path}. Loading standard fallback layers.")
            self._load_fallback_defaults()
            return

        try:
            with open(layers_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._layers.clear()
            self._visibility_state.clear()
            
            # Sort layers based on rendering order
            layer_entries = data.get("layers", [])
            layer_entries.sort(key=lambda x: x.get("rendering_order", 99))
            
            for entry in layer_entries:
                name = entry.get("layer_name")
                if not name:
                    continue
                self._layers[name] = entry
                self._visibility_state[name] = entry.get("default_visibility", True)
                
            logger.info(f"Loaded {len(self._layers)} visualization layers from JSON config.")
            
        except Exception as e:
            logger.error(f"Failed to load layers from {layers_path}: {e}. Loading fallbacks.")
            self._load_fallback_defaults()

    def _load_fallback_defaults(self):
        """Initializes internal structures with backward compatible default templates."""
        self._layers.clear()
        self._visibility_state.clear()
        for entry in DEFAULT_LAYERS_FALLBACK:
            name = entry["layer_name"]
            self._layers[name] = entry
            self._visibility_state[name] = entry["default_visibility"]

    def show_layer(self, layer_name: str) -> bool:
        """Enable a visualization layer."""
        if layer_name in self._visibility_state:
            self._visibility_state[layer_name] = True
            logger.info(f"Layer '{layer_name}' set to visible.")
            return True
        return False

    def hide_layer(self, layer_name: str) -> bool:
        """Disable a visualization layer."""
        if layer_name in self._visibility_state:
            self._visibility_state[layer_name] = False
            logger.info(f"Layer '{layer_name}' set to hidden.")
            return True
        return False

    def toggle_layer(self, layer_name: str) -> bool:
        """Toggle layer visibility state."""
        if layer_name in self._visibility_state:
            self._visibility_state[layer_name] = not self._visibility_state[layer_name]
            logger.info(f"Layer '{layer_name}' visibility toggled to {self._visibility_state[layer_name]}.")
            return self._visibility_state[layer_name]
        return False

    def is_layer_visible(self, layer_name: str) -> bool:
        """Query visibility status of a layer."""
        return self._visibility_state.get(layer_name, True)

    def get_visible_layers(self) -> List[str]:
        """Get a list of all currently enabled layer names."""
        return [k for k, v in self._visibility_state.items() if v]

    def get_all_layers(self) -> List[Dict[str, Any]]:
        """List all loaded layers details sorted by rendering order."""
        return list(self._layers.values())

    def reset_to_defaults(self):
        """Reset visibility state to the loaded configuration default values."""
        for name, entry in self._layers.items():
            self._visibility_state[name] = entry.get("default_visibility", True)
        logger.info("Reset all visualization layers to default configuration states.")
