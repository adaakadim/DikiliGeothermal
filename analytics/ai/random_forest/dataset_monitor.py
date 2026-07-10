"""
analytics/ai/random_forest/dataset_monitor.py
=============================================
Singleton to intercept incoming live features and assess Data Quality
without blocking or modifying the main prediction loop.
"""

import math
from typing import Dict, Any

from analytics.ai.random_forest.dataset_metadata import DatasetIntrospector

class DataQualityMonitor:
    _instance = None
    _latest_evaluation = {}
    _latest_live_values = {}
    _schema = DatasetIntrospector.get_feature_schema()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataQualityMonitor, cls).__new__(cls)
            cls._latest_evaluation = cls._get_default_evaluation()
        return cls._instance

    @classmethod
    def _get_default_evaluation(cls):
        return {
            "score": 0.0,
            "missing_count": len(cls._schema),
            "missing_pct": 100.0,
            "invalid_count": 0,
            "duplicate_count": 0,
            "completeness": 0.0,
            "feature_availability": "0%",
            "compatibility": "Unknown",
            "missing_inputs": [],
            "unsupported_inputs": [],
            "live_status_map": {feat["name"]: "MISSING" for feat in cls._schema}
        }

    @classmethod
    def evaluate_live_stream(cls, live_features: Dict[str, Any]):
        """
        Asynchronously assesses the live dictionary against the strict schema.
        Called by the predictor before inference.
        """
        cls._latest_live_values = dict(live_features)
        
        missing_inputs = []
        invalid_count = 0
        live_status_map = {}
        
        schema_keys = [f["name"] for f in cls._schema]
        
        for feat in cls._schema:
            k = feat["name"]
            if k not in live_features:
                missing_inputs.append(k)
                live_status_map[k] = "MISSING"
                continue
                
            val = live_features[k]
            if val is None or (isinstance(val, float) and math.isnan(val)):
                invalid_count += 1
                live_status_map[k] = "INVALID"
                continue
                
            # Range check
            if isinstance(val, (int, float)):
                # If massive deviation, out of range
                if val > (feat["max"] * 2.0) or val < (feat["min"] - abs(feat["min"])):
                    live_status_map[k] = "OUT OF RANGE"
                else:
                    live_status_map[k] = "READY"
            else:
                live_status_map[k] = "READY"
                
        unsupported_inputs = [k for k in live_features.keys() if k not in schema_keys]
        
        missing_count = len(missing_inputs)
        total_expected = len(schema_keys)
        completeness = ((total_expected - missing_count) / total_expected) * 100.0 if total_expected > 0 else 0.0
        
        # Calculate DQ score
        penalty = (missing_count * 2) + (invalid_count * 3)
        score = max(0.0, min(100.0, completeness - penalty))
        
        cls._latest_evaluation = {
            "score": score,
            "missing_count": missing_count,
            "missing_pct": (missing_count / total_expected * 100) if total_expected else 0.0,
            "invalid_count": invalid_count,
            "duplicate_count": 0,  # Live stream doesn't have duplicates natively
            "completeness": completeness,
            "feature_availability": f"{(total_expected - missing_count)}/{total_expected}",
            "compatibility": "Optimal" if missing_count == 0 else ("Degraded" if missing_count < 5 else "Critical"),
            "missing_inputs": missing_inputs,
            "unsupported_inputs": unsupported_inputs,
            "live_status_map": live_status_map
        }

    @classmethod
    def get_latest_evaluation(cls):
        if not cls._latest_evaluation:
            return cls._get_default_evaluation()
        return cls._latest_evaluation
        
    @classmethod
    def get_latest_live_values(cls):
        return cls._latest_live_values
