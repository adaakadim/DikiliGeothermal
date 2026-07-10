"""
digital_twin/asset_registry.py
==============================
Asset Registry managing Digital Twin equipment engineering metadata.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AssetRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AssetRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, metadata_path: Optional[str] = None):
        if self._initialized:
            return
            
        self._assets: Dict[str, Dict[str, Any]] = {}
        
        if metadata_path is None:
            metadata_path = os.path.join(os.path.dirname(__file__), "..", "assets", "equipment_metadata.json")
            
        self.load_metadata(metadata_path)
        self._initialized = True

    def load_metadata(self, metadata_path: str):
        """Loads and parses the equipment metadata JSON database."""
        if not os.path.exists(metadata_path):
            logger.error(f"Asset metadata file not found: {metadata_path}")
            self._assets = {}
            return

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._assets.clear()
            for asset in data.get("assets", []):
                asset_id = asset.get("id")
                if not asset_id:
                    logger.warning("Skipping asset entry with missing ID.")
                    continue
                    
                if asset_id in self._assets:
                    logger.error(f"Duplicate asset ID validation error: '{asset_id}'.")
                    raise ValueError(f"Duplicate asset ID in registry: {asset_id}")
                    
                self._assets[asset_id] = asset
                
            logger.info(f"Loaded {len(self._assets)} assets into Digital Twin Asset Registry.")
            
        except Exception as e:
            logger.error(f"Failed to parse metadata file {metadata_path}: {e}")
            raise

    def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Query metadata for a specific asset ID.
        Provides a graceful fallback with default empty strings if not registered.
        """
        if asset_id in self._assets:
            return self._assets[asset_id]
            
        logger.warning(f"Metadata missing for asset ID: '{asset_id}'. Returning default empty template.")
        return {
            "id": asset_id,
            "name": asset_id,
            "type": "unknown",
            "area": "unknown",
            "description": f"Asset {asset_id} metadata fallback.",
            "manufacturer": "N/A",
            "model": "N/A",
            "serial_number": "N/A",
            "installation_date": "N/A",
            "commissioning_date": "N/A",
            "criticality": "MEDIUM",
            "maintenance_interval_hours": 0.0,
            "plc_tag": "",
            "scada_tag": "",
            "ai_enabled": False,
            "alarm_enabled": False,
            "historian_enabled": False,
            "visibility": True,
            "notes": ""
        }

    def list_assets(self) -> List[Dict[str, Any]]:
        """List all registered plant assets."""
        return list(self._assets.values())

    def filter_assets(
        self, 
        asset_type: Optional[str] = None, 
        area: Optional[str] = None, 
        criticality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter assets dynamically by type, area, and criticality."""
        results = []
        for asset in self._assets.values():
            if asset_type and asset.get("type") != asset_type:
                continue
            if area and asset.get("area") != area:
                continue
            if criticality and asset.get("criticality") != criticality.upper():
                continue
            results.append(asset)
        return results
