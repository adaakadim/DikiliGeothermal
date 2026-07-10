"""
analytics/ai/lifecycle/drift_detector.py
========================================
Monitors incoming data features against expected training distributions.
"""

from typing import Dict, Any, List

class DriftDetector:
    def __init__(self):
        # In a real scenario, this would be loaded from a model profile.
        # We mock the expected ranges for key features based on typical SCADA values.
        self._expected_ranges = {
            "GW-01.Temperature": (130.0, 160.0),
            "GW-01.Pressure": (12.0, 18.0),
            "P-101.Flow Rate": (400.0, 600.0),
            "P-101.Motor Current": (180.0, 260.0)
        }
        
        # Track drift warnings
        self._drift_warnings: List[str] = []
        
    def detect_drift(self, ml_data: Dict[str, float]) -> List[str]:
        """
        Compare current input vector with expected distributions.
        Returns a list of active drift warnings.
        """
        self._drift_warnings.clear()
        
        for feature, (min_val, max_val) in self._expected_ranges.items():
            if feature in ml_data:
                val = ml_data[feature]
                
                # Simple threshold-based drift detection (in production this would use KS-tests, etc.)
                if val < min_val * 0.9 or val > max_val * 1.1:
                    warning = f"Data Drift Detected: '{feature}' ({val:.1f}) is significantly outside training distribution."
                    self._drift_warnings.append(warning)
                    
        return self._drift_warnings
        
    @property
    def has_drift(self) -> bool:
        return len(self._drift_warnings) > 0
