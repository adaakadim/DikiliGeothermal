"""
analytics/anomaly_detection/anomaly_score.py
============================================
Anomaly scoring module with abstract base class for future algorithm flexibility
and a concrete statistical (z-score) anomaly detector.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import math

class BaseAnomalyDetector(ABC):
    """
    Abstract interface for anomaly detection algorithms.
    Future implementations: Isolation Forest, LOF, One-Class SVM.
    """
    @abstractmethod
    def score(self, live_data: Dict[str, Any]) -> Tuple[float, str]:
        """
        Returns (anomaly_score 0-100, status_string).
        """
        pass


class StatisticalAnomalyDetector(BaseAnomalyDetector):
    """
    Z-score based multivariate anomaly detector.
    Maintains running mean/std of monitored parameters and flags deviations.
    """

    # Nominal operating ranges for Dikili plant sensors
    NOMINAL_RANGES = {
        "Wellhead Temperature (°C)":    (155.0, 170.0),
        "Wellhead Pressure (bar)":      (8.0, 14.0),
        "GW-01 Flow Rate (t/h)":        (80.0, 120.0),
        "P-101 Motor Current (A)":      (180.0, 260.0),
        "P-101 Motor Power (kW)":       (100.0, 200.0),
        "P-101 Discharge Pressure (bar)": (12.0, 20.0),
        "HX-101 Primary Inlet Temp (°C)": (140.0, 170.0),
        "HX-101 Primary Outlet Temp (°C)": (70.0, 95.0),
        "HX-101 Secondary Inlet Temp (°C)": (50.0, 70.0),
        "HX-101 Secondary Outlet Temp (°C)": (95.0, 125.0),
        "Health Score":                 (70.0, 100.0),
    }

    STATUS_THRESHOLDS = [
        (25.0, "Normal"),
        (50.0, "Minor"),
        (75.0, "Moderate"),
        (100.1, "Severe"),
    ]

    def __init__(self):
        self._history_count = 0
        self._running_mean: Dict[str, float] = {}
        self._running_m2: Dict[str, float] = {}   # for Welford's online variance

    def _update_stats(self, key: str, value: float):
        """Welford's online algorithm for running mean and variance."""
        if key not in self._running_mean:
            self._running_mean[key] = value
            self._running_m2[key] = 0.0
            return

        old_mean = self._running_mean[key]
        self._running_mean[key] += (value - old_mean) / (self._history_count + 1)
        self._running_m2[key] += (value - old_mean) * (value - self._running_mean[key])

    def _get_std(self, key: str) -> float:
        if self._history_count < 2:
            return 1.0
        variance = self._running_m2.get(key, 1.0) / max(1, self._history_count - 1)
        return max(0.01, math.sqrt(variance))

    def score(self, live_data: Dict[str, Any]) -> Tuple[float, str]:
        self._history_count += 1

        z_scores: Dict[str, float] = {}

        for param, (lo, hi) in self.NOMINAL_RANGES.items():
            value = live_data.get(param, None)
            if value is None:
                continue

            nominal_mid = (lo + hi) / 2.0
            nominal_spread = (hi - lo) / 2.0

            # Update running stats
            self._update_stats(param, value)

            # Calculate z-score relative to nominal range
            running_std = self._get_std(param)
            deviation = abs(value - nominal_mid)

            # Blend nominal-range deviation with statistical deviation
            range_z = deviation / max(0.01, nominal_spread)
            stat_z = deviation / running_std

            # Weighted blend: emphasise range deviation early, statistical later
            blend = min(1.0, self._history_count / 50.0)
            combined_z = range_z * (1.0 - blend * 0.5) + stat_z * (blend * 0.5)
            z_scores[param] = combined_z

        if not z_scores:
            return 0.0, "Normal"

        # Aggregate: RMS of top-3 z-scores for robustness
        sorted_z = sorted(z_scores.values(), reverse=True)
        top_n = sorted_z[:3]
        rms = math.sqrt(sum(z ** 2 for z in top_n) / len(top_n))

        # Map RMS to 0-100 score (z=0 → 0, z≥3 → 100)
        anomaly_score = min(100.0, max(0.0, (rms / 3.0) * 100.0))

        status = "Normal"
        for threshold, label in self.STATUS_THRESHOLDS:
            if anomaly_score < threshold:
                status = label
                break

        return anomaly_score, status

    def get_deviations(self, live_data: Dict[str, Any]) -> Dict[str, float]:
        """Return per-parameter deviation magnitudes for root cause analysis."""
        deviations = {}
        for param, (lo, hi) in self.NOMINAL_RANGES.items():
            value = live_data.get(param, None)
            if value is None:
                continue
            nominal_mid = (lo + hi) / 2.0
            nominal_spread = (hi - lo) / 2.0
            deviations[param] = abs(value - nominal_mid) / max(0.01, nominal_spread)
        return deviations
