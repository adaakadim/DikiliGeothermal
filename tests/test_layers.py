"""
tests/test_layers.py
====================
Automated unit tests for the Digital Twin Layer Management Framework.
"""

import sys
from unittest.mock import MagicMock

# Mock optional packages to run tests without HMI plotting requirements
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['matplotlib.animation'] = MagicMock()
sys.modules['matplotlib.gridspec'] = MagicMock()
sys.modules['matplotlib.lines'] = MagicMock()
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import os
import json
import pytest
from digital_twin.layer_manager import LayerManager

@pytest.fixture
def temp_layers(tmp_path):
    layer_data = {
        "layers": [
            {
                "layer_name": "background",
                "display_name": "Background",
                "default_visibility": True,
                "rendering_order": 1,
                "description": "Bg"
            },
            {
                "layer_name": "sensor",
                "display_name": "Sensors",
                "default_visibility": False,
                "rendering_order": 2,
                "description": "Sensors layer"
            }
        ]
    }
    f_path = tmp_path / "test_layers.json"
    with open(f_path, "w") as f:
        json.dump(layer_data, f)
    return str(f_path)

def test_layer_manager_load(temp_layers):
    LayerManager._instance = None
    manager = LayerManager(temp_layers)
    
    assert manager.is_layer_visible("background") is True
    assert manager.is_layer_visible("sensor") is False
    
    layers = manager.get_all_layers()
    assert len(layers) == 2
    # Sorted by rendering order
    assert layers[0]["layer_name"] == "background"
    assert layers[1]["layer_name"] == "sensor"

def test_layer_manager_visibility_apis(temp_layers):
    LayerManager._instance = None
    manager = LayerManager(temp_layers)
    
    # Show
    manager.show_layer("sensor")
    assert manager.is_layer_visible("sensor") is True
    assert "sensor" in manager.get_visible_layers()
    
    # Hide
    manager.hide_layer("background")
    assert manager.is_layer_visible("background") is False
    
    # Toggle
    manager.toggle_layer("sensor")
    assert manager.is_layer_visible("sensor") is False
    
    # Reset
    manager.reset_to_defaults()
    assert manager.is_layer_visible("background") is True
    assert manager.is_layer_visible("sensor") is False

def test_missing_layers_file_fallback():
    LayerManager._instance = None
    manager = LayerManager("non_existent_layers_file.json")
    
    # Should fallback gracefully and load default layers
    assert manager.is_layer_visible("background") is True
    assert manager.is_layer_visible("ai") is True
    assert len(manager.get_all_layers()) == 9
