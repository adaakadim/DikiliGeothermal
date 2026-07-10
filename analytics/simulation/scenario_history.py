"""
analytics/simulation/scenario_history.py
========================================
Maintains a history of executed simulations.
"""

from typing import List, Dict, Any
from datetime import datetime

class ScenarioHistory:
    def __init__(self):
        self._history = []
        
    def log_scenario(self, name: str, overrides: Dict[str, Any], sim_ai: Dict[str, Any], impact: Dict[str, Any]):
        """Logs a completed simulation run."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "overrides": overrides,
            "sim_ai": sim_ai,
            "impact": impact
        }
        self._history.append(entry)
        
        if len(self._history) > 50:
            self._history.pop(0)
            
    def get_history(self) -> List[Dict[str, Any]]:
        return self._history
