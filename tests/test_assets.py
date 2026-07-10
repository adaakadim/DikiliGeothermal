"""
tests/test_assets.py
====================
Automated unit tests for the Digital Twin Asset Registry & Equipment Metadata.
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
from digital_twin.asset_registry import AssetRegistry
from digital_twin.equipment.models import Pump

@pytest.fixture
def temp_metadata(tmp_path):
    metadata = {
        "assets": [
            {
                "id": "GW-01",
                "name": "Production Well GW-01",
                "type": "well",
                "area": "Extraction Field",
                "criticality": "HIGH",
                "visibility": True
            },
            {
                "id": "P-101",
                "name": "Production Pump P-101",
                "type": "pump",
                "area": "Extraction Field",
                "criticality": "HIGH",
                "visibility": True
            }
        ]
    }
    f_path = tmp_path / "test_assets.json"
    with open(f_path, "w") as f:
        json.dump(metadata, f)
    return str(f_path)

def test_asset_registry_load(temp_metadata):
    # Clear registry singleton initializer for tests
    AssetRegistry._instance = None
    
    registry = AssetRegistry(temp_metadata)
    asset = registry.get_asset("GW-01")
    assert asset["id"] == "GW-01"
    assert asset["type"] == "well"
    assert asset["criticality"] == "HIGH"

def test_asset_registry_filtering(temp_metadata):
    AssetRegistry._instance = None
    registry = AssetRegistry(temp_metadata)
    
    # Filter by type
    pumps = registry.filter_assets(asset_type="pump")
    assert len(pumps) == 1
    assert pumps[0]["id"] == "P-101"
    
    # Filter by area
    area_assets = registry.filter_assets(area="Extraction Field")
    assert len(area_assets) == 2

def test_duplicate_asset_id(tmp_path):
    metadata = {
        "assets": [
            {"id": "GW-01", "type": "well"},
            {"id": "GW-01", "type": "pump"} # Duplicate
        ]
    }
    f_path = tmp_path / "duplicate_assets.json"
    with open(f_path, "w") as f:
        json.dump(metadata, f)
        
    AssetRegistry._instance = None
    with pytest.raises(ValueError, match="Duplicate asset ID"):
        AssetRegistry(str(f_path))

def test_missing_asset_fallback():
    AssetRegistry._instance = None
    registry = AssetRegistry("non_existent_file.json")
    
    # Retrieve non-registered asset
    fallback = registry.get_asset("TEST-PUMP-99")
    assert fallback["id"] == "TEST-PUMP-99"
    assert fallback["manufacturer"] == "N/A"

def test_equipment_metadata_integration(temp_metadata):
    AssetRegistry._instance = None
    AssetRegistry(temp_metadata)
    
    # Instantiate Pump
    pump = Pump(id="P-101", name="Production Pump", type="PUMP")
    
    # Verify metadata is loaded in post_init
    assert hasattr(pump, "metadata")
    assert pump.metadata["id"] == "P-101"
    assert pump.metadata["criticality"] == "HIGH"
