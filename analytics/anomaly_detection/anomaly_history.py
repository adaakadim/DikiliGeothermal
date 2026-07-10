"""
analytics/anomaly_detection/anomaly_history.py
==============================================
Stores timestamped anomaly records for historical trend visualization.
"""

from collections import deque
from typing import Dict, Any, List
from datetime import datetime


class AnomalyHistoryManager:
    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self._scores: deque = deque(maxlen=max_records)
        self._records: List[Dict[str, Any]] = []

    def add_record(self, anomaly_score: float, status: str, root_cause: str,
                   recommendation: str, equipment: str = "Plant-Wide"):
        """Append a timestamped anomaly record."""
        self._scores.append(anomaly_score)

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "equipment": equipment,
            "anomaly_score": anomaly_score,
            "status": status,
            "root_cause": root_cause,
            "recommendation": recommendation,
            "resolution": "Open"
        }
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

    def get_score_trend(self) -> List[float]:
        """Return the anomaly score trend array."""
        return list(self._scores)

    def get_recent_records(self, n: int = 20) -> List[Dict[str, Any]]:
        """Return the last n anomaly records."""
        return self._records[-n:]
