"""
analytics/ai/rul/rul_history.py
===============================
Manages historical tracking of RUL estimates to provide trend data
for SCADA visualizations.
"""

from collections import deque
from typing import Dict, Any, List

class RULHistoryManager:
    def __init__(self, max_history_points: int = 100):
        # Dictionary mapping eq_id -> Dict of arrays for history
        self._history: Dict[str, Dict[str, deque]] = {}
        self.max_history_points = max_history_points
        
    def add_record(self, eq_id: str, rul_hours: float, health_index: float, failure_prob: float):
        """Add a new snapshot to the equipment's RUL history."""
        if eq_id not in self._history:
            self._history[eq_id] = {
                "rul": deque(maxlen=self.max_history_points),
                "health": deque(maxlen=self.max_history_points),
                "failure_prob": deque(maxlen=self.max_history_points)
            }
            
        self._history[eq_id]["rul"].append(rul_hours)
        self._history[eq_id]["health"].append(health_index)
        self._history[eq_id]["failure_prob"].append(failure_prob)
        
    def get_trend(self, eq_id: str) -> Dict[str, List[float]]:
        """Return the historical trend arrays for the given equipment."""
        if eq_id not in self._history:
            return {"rul": [], "health": [], "failure_prob": []}
            
        return {
            "rul": list(self._history[eq_id]["rul"]),
            "health": list(self._history[eq_id]["health"]),
            "failure_prob": list(self._history[eq_id]["failure_prob"])
        }
        
    def get_all_rul_trends(self) -> Dict[str, List[float]]:
        """Return just the RUL trend arrays for all equipment."""
        res = {}
        for eq_id, data in self._history.items():
            res[eq_id] = list(data["rul"])
        return res
