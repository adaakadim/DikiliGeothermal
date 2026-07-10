"""
digital_twin/layout_engine.py
=============================
Layout Engine for loading, parsing, and management of Digital Twin coordinates.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LayoutEngine:
    def __init__(self, layout_path: Optional[str] = None):
        self._equipment: Dict[str, Dict[str, Any]] = {}
        self._pipelines: List[Dict[str, Any]] = []
        self._layout_meta: Dict[str, Any] = {}
        
        if layout_path is None:
            # Fallback path relative to project root
            layout_path = os.path.join(os.path.dirname(__file__), "..", "layouts", "default_layout.json")
            
        self.load_layout(layout_path)

    def load_layout(self, layout_path: str):
        """Loads and validates a plant layout JSON file."""
        if not os.path.exists(layout_path):
            logger.error(f"Layout file not found: {layout_path}")
            # Load empty defaults
            self._equipment = {}
            self._pipelines = []
            return
            
        try:
            with open(layout_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._layout_meta = {
                "facility_id": data.get("facility_id", "unknown"),
                "version": data.get("version", "1.0.0"),
                "description": data.get("description", "")
            }
            
            # Load and validate equipment
            self._equipment.clear()
            for eq in data.get("equipment", []):
                eq_id = eq.get("id")
                if not eq_id:
                    logger.warning("Skipping layout equipment entry with missing ID.")
                    continue
                    
                if eq_id in self._equipment:
                    # Duplicate ID validation error
                    logger.error(f"Duplicate layout ID detected: '{eq_id}'. Overwriting previous entry.")
                    raise ValueError(f"Duplicate equipment ID in layout: {eq_id}")
                    
                self._equipment[eq_id] = eq
                
            # Load pipelines
            self._pipelines = data.get("pipelines", [])
            logger.info(f"Loaded layout: {self._layout_meta['facility_id']} (Version {self._layout_meta['version']})")
            
        except Exception as e:
            logger.error(f"Failed to parse layout file {layout_path}: {e}")
            raise

    def get_equipment(self, eq_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve coordinate configuration for a specific equipment ID."""
        if eq_id in self._equipment:
            return self._equipment[eq_id]
        
        # Graceful fallback logic for missing equipment
        logger.warning(f"Layout coordinates missing for equipment ID: '{eq_id}'. Using default fallback values.")
        return {
            "id": eq_id,
            "type": "box",
            "name": eq_id,
            "tag": f"interactive_{eq_id}",
            "x_factor": 0.5,
            "y_offset": 300.0,
            "rotation": 0.0,
            "scale": 1.0,
            "visibility": True,
            "layer": "sensor"
        }

    def get_all_equipment(self) -> List[Dict[str, Any]]:
        """Get all loaded equipment definitions."""
        return list(self._equipment.values())

    def get_all_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipeline layout paths."""
        return self._pipelines
