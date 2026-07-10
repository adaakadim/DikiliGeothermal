"""
analytics/trend_analyzer.py
Rolling trend analysis — moving averages, rate-of-change, anomaly detection.
"""

import collections
import logging
import statistics
import time
from typing import Deque, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TrendBuffer:
    """Fixed-length circular buffer for a single tag's history."""

    def __init__(self, maxlen: int = 300):
        self._buf: Deque[Tuple[float, float]] = collections.deque(maxlen=maxlen)

    def push(self, value: float):
        self._buf.append((time.time(), value))

    @property
    def values(self) -> list[float]:
        return [v for _, v in self._buf]

    @property
    def timestamps(self) -> list[float]:
        return [t for t, _ in self._buf]

    def moving_average(self, window: int = 10) -> Optional[float]:
        vals = self.values[-window:]
        return round(statistics.mean(vals), 3) if len(vals) >= 2 else None

    def rate_of_change(self) -> Optional[float]:
        """Derivative: (last - prev) / dt  [units/s]"""
        if len(self._buf) < 2:
            return None
        (t0, v0), (t1, v1) = self._buf[-2], self._buf[-1]
        dt = t1 - t0
        return round((v1 - v0) / dt, 4) if dt > 0 else None

    def std_dev(self, window: int = 30) -> Optional[float]:
        vals = self.values[-window:]
        return round(statistics.stdev(vals), 4) if len(vals) >= 2 else None

    def is_anomaly(self, current: float, threshold_sigma: float = 3.0) -> bool:
        """Returns True if current value is more than N sigma from rolling mean."""
        vals = self.values[-50:]
        if len(vals) < 10:
            return False
        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals)
        return stdev > 0 and abs(current - mean) > threshold_sigma * stdev


class TrendAnalyzer:
    """
    Maintains rolling trend buffers for selected process tags.
    Provides moving averages, rate-of-change, and anomaly flags.
    """

    MONITORED_TAGS = [
        "W-01.TEMP", "W-02.TEMP", "W-03.TEMP",
        "HX.SEC_SUPPLY", "HX.SEC_RETURN", "HX.THERMAL_POWER",
        "DH.TOTAL_FLOW", "DH.SUPPLY_PRES", "DH.DELTA_T",
        "PLANT.TOTAL_POWER",
    ]

    def __init__(self, db, buffer_len: int = 300):
        self.db = db
        self._buffers: Dict[str, TrendBuffer] = {
            tag: TrendBuffer(buffer_len) for tag in self.MONITORED_TAGS
        }

    def update(self):
        """Push current tag values into trend buffers. Call once per tick."""
        for tag_id, buf in self._buffers.items():
            value = self.db.read_value(tag_id)
            if value is not None:
                buf.push(float(value))

    def get_summary(self, tag_id: str) -> dict:
        buf = self._buffers.get(tag_id)
        if not buf:
            return {}
        current = self.db.read_value(tag_id)
        return {
            "tag_id": tag_id,
            "current": current,
            "ma_10": buf.moving_average(10),
            "ma_30": buf.moving_average(30),
            "roc": buf.rate_of_change(),
            "std_dev": buf.std_dev(30),
            "anomaly": buf.is_anomaly(current) if current is not None else False,
        }

    def all_summaries(self) -> dict:
        return {tag: self.get_summary(tag) for tag in self.MONITORED_TAGS}

    def anomalies(self) -> list[str]:
        return [
            tag for tag in self.MONITORED_TAGS
            if self.get_summary(tag).get("anomaly", False)
        ]
