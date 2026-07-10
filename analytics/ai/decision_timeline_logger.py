"""
analytics/ai/decision_timeline_logger.py
========================================
Handles persisting enriched decision events to a JSONL file.
Supports adding operator notes post-prediction.
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ai", "history")
JSONL_PATH = os.path.join(HISTORY_DIR, "decision_timeline.jsonl")

class DecisionTimelineLogger:
    def __init__(self):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(JSONL_PATH):
            with open(JSONL_PATH, "w", encoding="utf-8") as f:
                pass

    def log_decision(self, decision_event: Dict[str, Any]) -> str:
        """
        Appends a new decision event to the JSONL log. 
        Returns the unique ID generated for this decision.
        """
        event_id = str(uuid.uuid4())
        decision_event["event_id"] = event_id
        decision_event["operator_notes"] = ""
        
        try:
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(decision_event) + "\n")
        except Exception as e:
            logger.error(f"Failed to log decision to JSONL: {e}")
            
        return event_id

    def update_operator_note(self, event_id: str, note: str):
        """
        Updates the operator note for a specific decision by reading, modifying, and rewriting.
        """
        events = self.get_timeline()
        updated = False
        
        for ev in events:
            if ev.get("event_id") == event_id:
                ev["operator_notes"] = note
                updated = True
                break
                
        if updated:
            try:
                with open(JSONL_PATH, "w", encoding="utf-8") as f:
                    for ev in events:
                        f.write(json.dumps(ev) + "\n")
            except Exception as e:
                logger.error(f"Failed to rewrite JSONL for operator notes: {e}")

    def get_timeline(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Returns the most recent decision events."""
        events = []
        if not os.path.exists(JSONL_PATH):
            return events
            
        try:
            with open(JSONL_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read decision timeline: {e}")
            
        return events[-limit:]

    def get_confidence_stats(self) -> Dict[str, Any]:
        """Calculates statistics on prediction confidence over the timeline."""
        events = self.get_timeline()
        if not events:
            return {"trend": 0.0, "high": 0.0, "low": 0.0, "avg": 0.0}
            
        confidences = []
        for ev in events:
            pred = ev.get("prediction", {})
            conf = pred.get("Prediction Confidence (%)", pred.get("confidence", 0.0))
            confidences.append(float(conf))
            
        avg_conf = sum(confidences) / len(confidences)
        high_conf = max(confidences)
        low_conf = min(confidences)
        
        # Calculate trend (last vs avg of previous)
        trend = 0.0
        if len(confidences) > 1:
            recent_avg = sum(confidences[-3:]) / len(confidences[-3:])
            older_avg = sum(confidences[:-3]) / len(confidences[:-3]) if len(confidences) > 3 else confidences[0]
            trend = recent_avg - older_avg

        return {
            "trend": round(trend, 2),
            "high": round(high_conf, 1),
            "low": round(low_conf, 1),
            "avg": round(avg_conf, 1)
        }
