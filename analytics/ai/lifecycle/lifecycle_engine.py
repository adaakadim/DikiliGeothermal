"""
analytics/ai/lifecycle/lifecycle_engine.py
==========================================
Central orchestrator for AI Lifecycle Management.
Aggregates registry, monitor, drift, and validation data.
"""

from typing import Dict, Any, List
from .model_registry import ModelRegistry
from .model_monitor import ModelMonitor
from .drift_detector import DriftDetector
from .dataset_validator import DatasetValidator

class LifecycleEngine:
    def __init__(self):
        self.registry = ModelRegistry()
        self.monitor = ModelMonitor()
        self.drift_detector = DriftDetector()
        self.validator = DatasetValidator()
        
        self.quality_score = 100.0
        self.quality_issues = []
        self.active_drift_warnings = []
        
    def initialize_defaults(self):
        """Populate registry with known deployed models for Phase 5.5.5."""
        self.registry.register_model(
            model_id="PF_RF_01",
            name="PumpFailure_RF",
            version="1.2",
            algorithm="Random Forest",
            status="Production"
        )
        self.registry.register_model(
            model_id="Maint_RF_01",
            name="Maintenance_RF",
            version="1.1",
            algorithm="Random Forest",
            status="Production"
        )
        self.registry.register_model(
            model_id="AD_ISO_01",
            name="Anomaly_IsolationForest",
            version="2.0",
            algorithm="Isolation Forest",
            status="Production"
        )

    def evaluate(self, ml_data: Dict[str, float]):
        """
        Evaluate real-time dataset for quality and drift.
        (Called synchronously or asynchronously from the main tick loop).
        """
        if not ml_data:
            return
            
        # 1. Dataset Quality
        self.quality_score, self.quality_issues = self.validator.validate(ml_data)
        
        # 2. Data Drift Detection
        self.active_drift_warnings = self.drift_detector.detect_drift(ml_data)
        
    def record_inference(self, model_id: str, success: bool, latency_ms: float, confidence: float):
        """Allow predictor engines to report their execution metrics back here."""
        self.monitor.record_prediction(model_id, success, latency_ms, confidence)
        
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Aggregate data for the GUI AI Lifecycle Dashboard."""
        return {
            "models": self.registry.get_all_models(),
            "stats": self.monitor.get_all_stats(),
            "quality_score": self.quality_score,
            "quality_issues": self.quality_issues,
            "drift_warnings": self.active_drift_warnings
        }
