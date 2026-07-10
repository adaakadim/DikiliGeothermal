"""
tests/test_tags.py
===================
Automated unit tests for the PLC Tag Mapping Framework.
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
from digital_twin.tag_mapping import TagMappingManager

@pytest.fixture
def temp_tags(tmp_path):
    tag_data = {
      "mappings": [
        {
          "equipment_id": "GW-01",
          "plc_tag": "PLC.Wells.Prod_01.Temp",
          "scada_tag": "SCADA.Wells.GW01.Temp",
          "signal_type": "Analog",
          "permission": "Read-Only",
          "unit": "Celsius"
        },
        {
          "equipment_id": "P-101",
          "plc_tag": "PLC.Pumps.P101.Speed",
          "scada_tag": "SCADA.Pumps.P101.Hz",
          "signal_type": "Analog",
          "permission": "Read-Write",
          "unit": "Hz"
        }
      ]
    }
    f_path = tmp_path / "test_tags.json"
    with open(f_path, "w") as f:
        json.dump(tag_data, f)
    return str(f_path)

def test_tag_mapping_load(temp_tags):
    TagMappingManager._instance = None
    manager = TagMappingManager(temp_tags)
    
    assert manager.get_plc_tag("GW-01") == "PLC.Wells.Prod_01.Temp"
    assert manager.get_scada_tag("P-101") == "SCADA.Pumps.P101.Hz"
    
    # Bi-directional lookup
    assert manager.get_equipment_by_tag("PLC.Wells.Prod_01.Temp") == "GW-01"
    assert manager.get_equipment_by_tag("SCADA.Pumps.P101.Hz") == "P-101"

def test_duplicate_equipment_in_mappings(tmp_path):
    tag_data = {
      "mappings": [
        {"equipment_id": "GW-01", "plc_tag": "PLC.T1"},
        {"equipment_id": "GW-01", "plc_tag": "PLC.T2"} # Duplicate equipment ID
      ]
    }
    f_path = tmp_path / "duplicate_eq.json"
    with open(f_path, "w") as f:
        json.dump(tag_data, f)
        
    TagMappingManager._instance = None
    with pytest.raises(ValueError, match="Duplicate equipment ID"):
        TagMappingManager(str(f_path))

def test_duplicate_tags_in_mappings(tmp_path):
    tag_data = {
      "mappings": [
        {"equipment_id": "GW-01", "plc_tag": "PLC.DuplicateTag"},
        {"equipment_id": "P-101", "plc_tag": "PLC.DuplicateTag"} # Duplicate PLC tag
      ]
    }
    f_path = tmp_path / "duplicate_tag.json"
    with open(f_path, "w") as f:
        json.dump(tag_data, f)
        
    TagMappingManager._instance = None
    with pytest.raises(ValueError, match="Duplicate PLC tag"):
        TagMappingManager(str(f_path))

def test_missing_tag_fallback():
    TagMappingManager._instance = None
    manager = TagMappingManager("non_existent_file.json")
    
    # Fallbacks should generate standard tag paths automatically
    assert manager.get_plc_tag("P-999") == "PLC.P-999.Value"
    assert manager.get_scada_tag("P-999") == "SCADA.P-999.Value"
