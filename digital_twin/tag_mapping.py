"""
digital_twin/tag_mapping.py
===========================
PLC Tag Mapping Manager for abstraction of industrial device addresses.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class TagMappingManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TagMappingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, mapping_path: Optional[str] = None):
        if self._initialized:
            return
            
        self._mappings: Dict[str, Dict[str, Any]] = {}
        self._plc_tag_lookup: Dict[str, str] = {}
        self._scada_tag_lookup: Dict[str, str] = {}
        
        if mapping_path is None:
            mapping_path = os.path.join(os.path.dirname(__file__), "..", "assets", "plc_tags.json")
            
        self.load_mappings(mapping_path)
        self._initialized = True

    def load_mappings(self, mapping_path: str):
        """Loads and parses the external tag mappings JSON database."""
        if not os.path.exists(mapping_path):
            logger.warning(f"Tag mapping file not found: {mapping_path}")
            self._mappings = {}
            return

        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._mappings.clear()
            self._plc_tag_lookup.clear()
            self._scada_tag_lookup.clear()
            
            for map_entry in data.get("mappings", []):
                eq_id = map_entry.get("equipment_id")
                plc_tag = map_entry.get("plc_tag")
                scada_tag = map_entry.get("scada_tag")
                
                if not eq_id:
                    logger.warning("Skipping tag mapping entry with missing equipment ID.")
                    continue
                    
                if eq_id in self._mappings:
                    logger.error(f"Duplicate mapping equipment ID: '{eq_id}'.")
                    raise ValueError(f"Duplicate equipment ID in tag mappings: {eq_id}")
                    
                if plc_tag and plc_tag in self._plc_tag_lookup:
                    logger.error(f"Duplicate PLC tag detected: '{plc_tag}'.")
                    raise ValueError(f"Duplicate PLC tag mapping: {plc_tag}")
                    
                if scada_tag and scada_tag in self._scada_tag_lookup:
                    logger.error(f"Duplicate SCADA tag detected: '{scada_tag}'.")
                    raise ValueError(f"Duplicate SCADA tag mapping: {scada_tag}")
                    
                self._mappings[eq_id] = map_entry
                if plc_tag:
                    self._plc_tag_lookup[plc_tag] = eq_id
                if scada_tag:
                    self._scada_tag_lookup[scada_tag] = eq_id
                    
            logger.info(f"Loaded {len(self._mappings)} tag mappings into Tag Mapping Manager.")
            
        except Exception as e:
            logger.error(f"Failed to parse mapping file {mapping_path}: {e}")
            raise

    def get_plc_tag(self, eq_id: str) -> str:
        """Query PLC tag address for equipment ID."""
        if eq_id in self._mappings:
            return self._mappings[eq_id].get("plc_tag", "")
        return f"PLC.{eq_id}.Value"

    def get_scada_tag(self, eq_id: str) -> str:
        """Query SCADA tag address for equipment ID."""
        if eq_id in self._mappings:
            return self._mappings[eq_id].get("scada_tag", "")
        return f"SCADA.{eq_id}.Value"

    def get_equipment_by_tag(self, tag: str) -> Optional[str]:
        """Look up equipment ID matching a PLC or SCADA tag."""
        if tag in self._plc_tag_lookup:
            return self._plc_tag_lookup[tag]
        if tag in self._scada_tag_lookup:
            return self._scada_tag_lookup[tag]
        return None

    def list_tags(self) -> List[Dict[str, Any]]:
        """List all loaded mapping definitions."""
        return list(self._mappings.values())
