"""
analytics/ai/trend_analysis.py
==============================
Historical degradation analysis module. Tracks rolling averages of key metrics
and evaluates whether equipment condition is improving, stable, or degrading.
"""

from collections import deque
from typing import Dict, Any

class TrendAnalyzer:
    def __init__(self, window_size: int = 20):
        # We store past health indexes here
        self._window_size = window_size
        self._history = deque(maxlen=window_size)
        
    def add_record(self, health_indexes: Dict[str, float]):
        """Adds a new snapshot to the sliding window."""
        self._history.append(health_indexes)
        
    def analyze_trends(self, current_health: float, metric_name: str = "Overall Plant Health") -> Dict[str, Any]:
        """
        Compares the current metric against its historical moving average.
        """
        if len(self._history) < 2:
            return {
                "Current": current_health,
                "Previous Average": current_health,
                "Change": 0.0,
                "Assessment": "Insufficient data for trend analysis"
            }
            
        # Calculate average over the window (excluding the absolute newest if we want true "previous")
        # For simplicity, we just average what's in the queue
        past_values = [h.get(metric_name, 100.0) for h in self._history]
        prev_avg = sum(past_values) / len(past_values)
        
        delta = current_health - prev_avg
        
        assessment = "Equipment condition is stable"
        if delta <= -5.0:
            assessment = "Equipment condition is rapidly degrading"
        elif delta <= -2.0:
            assessment = "Equipment condition is gradually degrading"
        elif delta >= 2.0:
            assessment = "Equipment condition has improved"
            
        return {
            "Current": round(current_health, 1),
            "Previous Average": round(prev_avg, 1),
            "Change": round(delta, 1),
            "Assessment": assessment
        }
