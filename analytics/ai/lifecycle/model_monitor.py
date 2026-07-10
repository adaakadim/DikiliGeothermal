"""
analytics/ai/lifecycle/model_monitor.py
=======================================
Tracks real-time prediction performance and execution metrics.
"""

from typing import Dict, Any

class ModelMonitor:
    def __init__(self):
        self._stats: Dict[str, Dict[str, float]] = {}
        
    def record_prediction(self, model_id: str, success: bool, latency_ms: float, confidence: float):
        """Record statistics for a single prediction event."""
        if model_id not in self._stats:
            self._stats[model_id] = {
                "total_predictions": 0,
                "successful_predictions": 0,
                "failed_predictions": 0,
                "avg_latency_ms": 0.0,
                "avg_confidence": 0.0
            }
            
        stats = self._stats[model_id]
        n = stats["total_predictions"]
        
        # Update running averages
        stats["avg_latency_ms"] = (stats["avg_latency_ms"] * n + latency_ms) / (n + 1)
        stats["avg_confidence"] = (stats["avg_confidence"] * n + confidence) / (n + 1)
        
        # Update counts
        stats["total_predictions"] += 1
        if success:
            stats["successful_predictions"] += 1
        else:
            stats["failed_predictions"] += 1
            
    def get_stats(self, model_id: str) -> Dict[str, float]:
        return self._stats.get(model_id, {})
        
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        return self._stats
