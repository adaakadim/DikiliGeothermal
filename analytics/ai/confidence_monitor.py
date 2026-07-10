"""
analytics/ai/confidence_monitor.py
==================================
Monitors the real-time reliability of the AI engine by tracking confidence scores.
"""

from collections import deque
from typing import Dict, Any

class ConfidenceMonitor:
    def __init__(self, window_size: int = 100, warning_threshold: float = 70.0):
        self._history = deque(maxlen=window_size)
        self._threshold = warning_threshold
        
    def add_confidence(self, confidence: float):
        self._history.append(confidence)
        
    @property
    def current(self) -> float:
        return self._history[-1] if self._history else 100.0
        
    @property
    def average(self) -> float:
        if not self._history:
            return 100.0
        return sum(self._history) / len(self._history)
        
    @property
    def minimum(self) -> float:
        return min(self._history) if self._history else 100.0
        
    @property
    def maximum(self) -> float:
        return max(self._history) if self._history else 100.0
        
    @property
    def reliability_status(self) -> str:
        """Returns GOOD or WARNING based on the warning threshold."""
        if self.current < self._threshold or self.average < self._threshold:
            return "WARNING"
        return "GOOD"
        
    def get_summary(self) -> Dict[str, Any]:
        return {
            "current": round(self.current, 1),
            "average": round(self.average, 1),
            "min": round(self.minimum, 1),
            "max": round(self.maximum, 1),
            "status": self.reliability_status
        }
