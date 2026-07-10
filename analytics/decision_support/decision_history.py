"""
analytics/decision_support/decision_history.py
==============================================
Logs and stores high-level AI assessments.
"""

from typing import List, Dict, Any
from datetime import datetime
import json
import os

class DecisionHistory:
    def __init__(self, log_file: str = "data/ai/decision_log.json"):
        self.log_file = log_file
        self._history = []
        
        # Create directory if needed
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log_decision(self, eq_id: str, assessment: dict):
        """Log a major decision to history."""
        # Only log CRITICAL or HIGH risk shifts to avoid spamming
        risk = assessment.get("Overall Risk", "LOW")
        if risk in ["CRITICAL", "HIGH"]:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "equipment": eq_id,
                "overall_risk": risk,
                "recommended_action": assessment.get("Recommended Action", ""),
                "priority": assessment.get("Maintenance Priority", ""),
                "operator_ack": False,
                "resolution_status": "OPEN"
            }
            self._history.append(entry)
            
            # Keep last 100
            if len(self._history) > 100:
                self._history.pop(0)
                
    def get_recent_critical_decisions(self) -> List[Dict[str, Any]]:
        return [d for d in self._history if d.get("resolution_status") == "OPEN"]
