"""
analytics/anomaly_detection/anomaly_engine.py
=============================================
Facade orchestrator for the anomaly detection pipeline.
Consumes live data + AI results → anomaly score → root cause → history → unified output.
"""

from typing import Dict, Any
from .anomaly_score import StatisticalAnomalyDetector
from .root_cause_analyzer import RootCauseAnalyzer
from .anomaly_history import AnomalyHistoryManager


class AnomalyEngine:
    def __init__(self):
        self.detector = StatisticalAnomalyDetector()
        self.rca = RootCauseAnalyzer()
        self.history = AnomalyHistoryManager()

    def evaluate(self, live_data: Dict[str, Any], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full anomaly detection pipeline.
        
        Parameters:
            live_data: Live SCADA sensor readings.
            ai_result: Output from Random Forest predictor.
            
        Returns:
            Unified anomaly assessment dictionary.
        """
        # 1. Calculate anomaly score
        anomaly_score, status = self.detector.score(live_data)

        # 2. Get per-parameter deviations for root cause analysis
        deviations = self.detector.get_deviations(live_data)

        # 3. Root cause analysis
        rca_result = self.rca.analyze(deviations, anomaly_score)

        # 4. Integrate with AI prediction for combined confidence
        failure_prob = ai_result.get("Pump Failure Probability (%)", 0.0)
        ai_conf = ai_result.get("Prediction Confidence (%)", 90.0)

        # Boost anomaly score if AI also predicts high risk
        combined_score = anomaly_score
        if failure_prob > 60.0:
            combined_score = min(100.0, anomaly_score * 1.15)
        elif failure_prob > 80.0:
            combined_score = min(100.0, anomaly_score * 1.3)

        # Re-evaluate status based on combined score
        if combined_score >= 75.0:
            combined_status = "Severe"
        elif combined_score >= 50.0:
            combined_status = "Moderate"
        elif combined_score >= 25.0:
            combined_status = "Minor"
        else:
            combined_status = "Normal"

        # 5. Generate recommendation
        recommendation = self._generate_recommendation(combined_status, rca_result)

        # 6. Record history
        self.history.add_record(
            anomaly_score=combined_score,
            status=combined_status,
            root_cause=rca_result["primary"],
            recommendation=recommendation
        )

        return {
            "Anomaly Score": round(combined_score, 1),
            "Status": combined_status,
            "Root Cause": rca_result,
            "Affected Equipment": self._identify_affected_equipment(deviations),
            "Confidence": round(ai_conf, 1),
            "Recommendation": recommendation,
            "Raw Score": round(anomaly_score, 1),
        }

    def _generate_recommendation(self, status: str, rca: Dict[str, Any]) -> str:
        """Generate engineering-grade recommendation based on anomaly status."""
        primary = rca.get("primary", "None")

        if status == "Normal":
            return "Continue normal operation. All parameters within expected ranges."
        elif status == "Minor":
            return f"Monitor {primary} closely. Minor deviation detected but no immediate action required."
        elif status == "Moderate":
            return f"Investigate {primary}. Consider diagnostic inspection within 24 hours."
        else:  # Severe
            return f"Immediate investigation of {primary} required. Anomalous behavior may indicate impending failure."

    def _identify_affected_equipment(self, deviations: Dict[str, float]) -> str:
        """Map high-deviation sensors to equipment IDs."""
        affected = set()
        for param, dev in deviations.items():
            if dev < 1.2:
                continue
            if "P-101" in param or "Motor" in param:
                affected.add("P-101")
            elif "HX-101" in param:
                affected.add("HX-101")
            elif "GW-01" in param or "Wellhead" in param:
                affected.add("GW-01")
            elif "Health" in param:
                affected.add("Plant-Wide")

        return ", ".join(sorted(affected)) if affected else "None"
