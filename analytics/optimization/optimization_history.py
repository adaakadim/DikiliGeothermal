"""
analytics/optimization/optimization_history.py
==============================================
Tracks efficiency KPIs and optimization metrics over time.
"""

from collections import deque
from typing import Dict, List

class OptimizationHistoryManager:
    def __init__(self, max_history_points: int = 100):
        self.max_history_points = max_history_points
        self._history: Dict[str, deque] = {
            "overall_efficiency": deque(maxlen=max_history_points),
            "pump_efficiency": deque(maxlen=max_history_points),
            "hx_efficiency": deque(maxlen=max_history_points),
            "plant_load": deque(maxlen=max_history_points)
        }
        
    def add_record(self, kpis: Dict[str, float]):
        """Append a new KPI snapshot."""
        self._history["overall_efficiency"].append(kpis.get("Overall Plant Efficiency (%)", 0.0))
        self._history["pump_efficiency"].append(kpis.get("Pump Efficiency (%)", 0.0))
        self._history["hx_efficiency"].append(kpis.get("Heat Exchanger Efficiency (%)", 0.0))
        self._history["plant_load"].append(kpis.get("Plant Load (%)", 0.0))
        
    def get_trend(self, metric: str) -> List[float]:
        """Return the historical trend array for a given metric."""
        if metric in self._history:
            return list(self._history[metric])
        return []
