"""
tests/test_layout.py
====================
Automated unit tests for the Digital Twin Layout Engine.
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
from digital_twin.layout_engine import LayoutEngine

@pytest.fixture
def temp_layout(tmp_path):
    layout_data = {
        "facility_id": "test_facility",
        "version": "1.0.0",
        "description": "Test Layout",
        "equipment": [
            {
                "id": "GW-01",
                "type": "box",
                "name": "Production Well",
                "tag": "interactive_GW-01",
                "x_factor": 0.5,
                "y_offset": 100.0,
                "rotation": 0.0,
                "scale": 1.0,
                "visibility": True,
                "layer": "sensor"
            }
        ],
        "pipelines": []
    }
    # Save to tmp path
    f_path = tmp_path / "test_layout.json"
    with open(f_path, "w") as f:
        json.dump(layout_data, f)
    return str(f_path)

def test_layout_load(temp_layout):
    engine = LayoutEngine(temp_layout)
    eq = engine.get_equipment("GW-01")
    assert eq is not None
    assert eq["id"] == "GW-01"
    assert eq["y_offset"] == 100.0

def test_duplicate_equipment_id(tmp_path):
    layout_data = {
        "facility_id": "test_facility",
        "version": "1.0.0",
        "equipment": [
            {"id": "GW-01", "type": "box", "x_factor": 0.5, "y_offset": 100.0},
            {"id": "GW-01", "type": "pump", "x_factor": 0.5, "y_offset": 200.0} # Duplicate
        ]
    }
    f_path = tmp_path / "duplicate_layout.json"
    with open(f_path, "w") as f:
        json.dump(layout_data, f)
        
    with pytest.raises(ValueError, match="Duplicate equipment ID"):
        LayoutEngine(str(f_path))

def test_fallback_for_missing_entry():
    # Load using empty layout path (file does not exist)
    engine = LayoutEngine("non_existent_layout_file.json")
    
    # Should fallback gracefully without crashing
    eq = engine.get_equipment("MISSING-EQ")
    assert eq is not None
    assert eq["id"] == "MISSING-EQ"
    assert eq["y_offset"] == 300.0
