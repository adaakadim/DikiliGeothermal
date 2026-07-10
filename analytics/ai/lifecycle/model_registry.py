"""
analytics/ai/lifecycle/model_registry.py
========================================
Maintains information about every deployed AI model.
"""

from typing import Dict, Any, List
from datetime import datetime

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}
        
    def register_model(self, 
                       model_id: str, 
                       name: str, 
                       version: str, 
                       algorithm: str, 
                       status: str = "Production"):
        """Register a new model or update an existing one."""
        self._models[model_id] = {
            "id": model_id,
            "name": name,
            "version": version,
            "algorithm": algorithm,
            "status": status,
            "deployment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "training_date": "N/A",  # Could be pulled from metadata if available
            "dataset_version": "v1.0" # Mock for now
        }
        
    def update_model_status(self, model_id: str, status: str):
        if model_id in self._models:
            self._models[model_id]["status"] = status
            
    def get_model(self, model_id: str) -> Dict[str, Any]:
        return self._models.get(model_id, {})
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        return list(self._models.values())
