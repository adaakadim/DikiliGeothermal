"""
analytics/ai/random_forest/predictor.py
=======================================
Public API for real-time SCADA integration.
Accepts live sensor data and returns AI predictions, confidence scores,
and equipment health estimations using the latest cached models.
"""

import logging
try:
    import pandas as pd
except ImportError:
    class MockPandas:
        def DataFrame(self, *args, **kwargs): return None
    pd = MockPandas()
from datetime import datetime
from typing import Dict, Any

from analytics.ai.random_forest.model_loader import ModelCache

logger = logging.getLogger(__name__)

import time

from analytics.ai.random_forest.dataset_monitor import DataQualityMonitor
from analytics.ai.decision_analyzer import DecisionAnalyzer
from analytics.ai.decision_timeline_logger import DecisionTimelineLogger

_timeline_logger = DecisionTimelineLogger()

def predict_plant_state(live_features: Dict[str, Any], lifecycle_engine=None) -> Dict[str, Any]:
    """
    Real-time prediction API for SCADA integration.
    
    Args:
        live_features: A dictionary mapping exact feature column names to their current values.
        lifecycle_engine: Optional LifecycleEngine instance to record ML-Ops metrics.
                       
    Returns:
        Dict containing prediction results, probabilities, confidence scores, and timestamps.
    """
    # 0. Live Feature Monitor Intercept
    try:
        DataQualityMonitor.evaluate_live_stream(live_features)
    except Exception as e:
        logger.error(f"DataQualityMonitor intercept failed: {e}")

    start_time = time.perf_counter()
    pump_model = ModelCache.get_model("PumpFailure_RF")
    maint_model = ModelCache.get_model("Maintenance_RF")
    
    timestamp = datetime.now().isoformat()
    
    if not pump_model or not maint_model:
        logger.warning("AI Models not loaded. Returning default safe state.")
        return {
            "Pump Failure Probability (%)": 0.0,
            "Maintenance Required": False,
            "Equipment Health (%)": 100.0,
            "Plant Status": "UNKNOWN",
            "Prediction Confidence (%)": 0.0,
            "Prediction Timestamp": timestamp
        }

    # Force single-threaded inference to prevent joblib multiprocessing leaks in tkinter loops
    if hasattr(pump_model, "n_jobs"): pump_model.n_jobs = 1
    if hasattr(maint_model, "n_jobs"): maint_model.n_jobs = 1

    try:
        # Convert to DataFrame to ensure scikit-learn aligns column names properly
        # Fix missing features dynamically based on what the model expects
        if hasattr(pump_model, "feature_names_in_"):
            for col in pump_model.feature_names_in_:
                if col not in live_features:
                    # Handle encoding mismatches (e.g. Temperature (C) vs Temperature (°C))
                    alt_col = col.replace("", "°")
                    if alt_col in live_features:
                        live_features[col] = live_features[alt_col]
                    else:
                        live_features[col] = 0.0
                        
        df = pd.DataFrame([live_features])
        if hasattr(pump_model, "feature_names_in_"):
            # Ensure exact column order and subset
            df = df[list(pump_model.feature_names_in_)]
        
        # 1. Pump Failure Prediction
        pump_pred = int(pump_model.predict(df)[0])
        pump_probs = pump_model.predict_proba(df)[0]
        pump_fail_prob = float(pump_probs[1]) * 100.0
        pump_conf = float(max(pump_probs)) * 100.0
        
        # 2. Maintenance Prediction
        maint_pred = int(maint_model.predict(df)[0])
        maint_probs = maint_model.predict_proba(df)[0]
        maint_conf = float(max(maint_probs)) * 100.0
        
        # 3. Aggregated Health & Status
        overall_confidence = (pump_conf + maint_conf) / 2.0
        
        health_pct = 100.0 - pump_fail_prob
        if maint_pred == 1:
            health_pct -= 20.0
        health_pct = max(0.0, min(100.0, health_pct))
        
        if pump_pred == 1:
            status = "CRITICAL"
        elif maint_pred == 1 or pump_fail_prob > 30.0:
            status = "WARNING"
        else:
            status = "NORMAL"

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        if lifecycle_engine:
            lifecycle_engine.record_inference("PF_RF_01", True, latency_ms, pump_conf)
            lifecycle_engine.record_inference("Maint_RF_01", True, latency_ms, maint_conf)
            
        ModelCache.update_inference_stats("PumpFailure_RF", latency_ms, timestamp)
        ModelCache.update_inference_stats("Maintenance_RF", latency_ms, timestamp)

        prediction_result = {
            "Pump Failure Probability (%)": round(pump_fail_prob, 2),
            "Maintenance Required": bool(maint_pred == 1),
            "Equipment Health (%)": round(health_pct, 1),
            "Plant Status": status,
            "Prediction Confidence (%)": round(overall_confidence, 2),
            "Prediction Timestamp": timestamp
        }
        
        try:
            event = DecisionAnalyzer.analyze_decision(live_features, prediction_result)
            _timeline_logger.log_decision(event)
        except Exception as e:
            logger.error(f"Failed to log decision timeline: {e}")
            
        return prediction_result
        
    except Exception as e:
        logger.error(f"Error during AI Prediction: {e}")
        if lifecycle_engine:
            lifecycle_engine.record_inference("PF_RF_01", False, 0.0, 0.0)
            lifecycle_engine.record_inference("Maint_RF_01", False, 0.0, 0.0)
        return {
            "Pump Failure Probability (%)": 0.0,
            "Maintenance Required": False,
            "Equipment Health (%)": 0.0,
            "Plant Status": "ERROR",
            "Prediction Confidence (%)": 0.0,
            "Prediction Timestamp": timestamp
        }
