"""
analytics/decision_support/risk_fusion.py
=========================================
Combines multiple AI signals into a single unified risk score.
"""

from typing import Dict, Any

class RiskFusionEngine:
    def fuse_risk(self, eq_id: str, ai_result: dict, rul_data: dict, health_idx: float, anomaly_score: float) -> str:
        """
        Calculates an overall risk category based on multiple AI engines.
        Returns: "LOW", "MODERATE", "HIGH", or "CRITICAL"
        """
        risk_level = "LOW"
        
        # 1. Base Failure Probability (Random Forest)
        rf_prob = ai_result.get("Pump Failure Probability (%)", 0.0)
        
        # 2. Remaining Useful Life (RUL Engine)
        rul_hours = rul_data.get("Remaining Useful Life (Hours)", 10000.0)
        
        # 3. Anomaly Isolation Forest
        anom_score = anomaly_score
        
        # 4. Equipment Health
        health = health_idx
        
        # Fusion Logic
        if rf_prob > 80.0 or rul_hours < 48.0 or health < 40.0:
            risk_level = "CRITICAL"
        elif rf_prob > 50.0 or rul_hours < 168.0 or health < 60.0 or anom_score > 75.0:
            risk_level = "HIGH"
        elif rf_prob > 20.0 or rul_hours < 720.0 or health < 85.0 or anom_score > 40.0:
            risk_level = "MODERATE"
            
        return risk_level
