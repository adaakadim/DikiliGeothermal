"""
analytics/ai/prediction_history.py
==================================
Logs and retrieves historical AI predictions.
Stores data in a persistent CSV file while keeping a circular buffer
of the last 100 predictions for live SCADA dashboard charting.
"""

import os
import csv
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ai", "history")
CSV_PATH = os.path.join(HISTORY_DIR, "predictions.csv")

class PredictionHistoryLogger:
    def __init__(self, max_memory_records: int = 1000):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        self._memory = deque(maxlen=max_memory_records)
        self._ensure_csv_headers()
        self._load_recent_from_csv()

    def _ensure_csv_headers(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "time",
                    "equipment",
                    "failure_probability",
                    "maintenance_required",
                    "health_score",
                    "confidence",
                    "status",
                    "model",
                    "top_positive_feature",
                    "top_negative_feature",
                    "ai_explanation"
                ])
            logger.info(f"Created new AI history database: {CSV_PATH}")

    def _load_recent_from_csv(self):
        """Loads the most recent records from the CSV into memory."""
        if not os.path.exists(CSV_PATH):
            return
            
        try:
            with open(CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                for row in rows[-self._memory.maxlen:]:
                    try:
                        record = {
                            "time": row.get("time", ""),
                            "equipment": row.get("equipment", "UNKNOWN"),
                            "failure_probability": float(row.get("failure_probability", 0.0)),
                            "maintenance_required": row.get("maintenance_required", "False") == "True",
                            "health_score": float(row.get("health_score", 100.0)),
                            "confidence": float(row.get("confidence", 0.0)),
                            "status": row.get("status", "UNKNOWN"),
                            "model": row.get("model", "UNKNOWN"),
                            "top_positive_feature": row.get("top_positive_feature", ""),
                            "top_negative_feature": row.get("top_negative_feature", ""),
                            "ai_explanation": row.get("ai_explanation", "")
                        }
                        self._memory.append(record)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to load recent history from CSV: {e}")

    def log_prediction(self, prediction: Dict[str, Any], shap_res: Dict[str, Any] = None, equipment: str = "PLANT", model: str = "RandomForest"):
        """
        Extracts relevant keys from the prediction output and logs them along with XAI.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        pos_feat = shap_res.get("positive_factors", [""])[0] if shap_res and shap_res.get("positive_factors") else ""
        neg_feat = shap_res.get("negative_factors", [""])[0] if shap_res and shap_res.get("negative_factors") else ""
        expl_text = shap_res.get("explanation_text", "") if shap_res else ""
        
        record = {
            "time": now,
            "equipment": equipment,
            "failure_probability": prediction.get("Pump Failure Probability (%)", 0.0),
            "maintenance_required": prediction.get("Maintenance Required", False),
            "health_score": prediction.get("Equipment Health (%)", 100.0),
            "confidence": prediction.get("Prediction Confidence (%)", 100.0),
            "status": prediction.get("Plant Status", "NORMAL"),
            "model": model,
            "top_positive_feature": pos_feat,
            "top_negative_feature": neg_feat,
            "ai_explanation": expl_text
        }
        
        # 1. Append to in-memory buffer
        self._memory.append(record)
        
        # 2. Append to persistent CSV
        try:
            with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    record["time"],
                    record["equipment"],
                    record["failure_probability"],
                    record["maintenance_required"],
                    record["health_score"],
                    record["confidence"],
                    record["status"],
                    record["model"],
                    record["top_positive_feature"],
                    record["top_negative_feature"],
                    record["ai_explanation"]
                ])
        except Exception as e:
            logger.error(f"Failed to write prediction history to CSV: {e}")

    def get_recent_history(self) -> List[Dict[str, Any]]:
        """Returns the circular buffer of recent predictions (up to max_memory_records)."""
        return list(self._memory)

    def filter_history(self, 
                      equipment: str = "All", 
                      status: str = "All", 
                      min_conf: float = 0.0, 
                      search_term: str = "") -> List[Dict[str, Any]]:
        """
        Filters the in-memory history based on criteria.
        """
        results = []
        search_term = search_term.lower()
        
        for record in self._memory:
            if equipment != "All" and record.get("equipment") != equipment:
                continue
            if status != "All" and record.get("status") != status:
                continue
            if record.get("confidence", 0.0) < min_conf:
                continue
                
            if search_term:
                text_blob = f"{record.get('equipment','')} {record.get('status','')} {record.get('model','')} {record.get('ai_explanation','')}".lower()
                maint_str = "action required" if record.get("maintenance_required") else "no action"
                text_blob += f" {maint_str}"
                
                if search_term not in text_blob:
                    continue
                    
            results.append(record)
            
        return results

    def get_summary_statistics(self, filtered_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates statistics on a set of records."""
        total = len(filtered_records)
        if total == 0:
            return {
                "total": 0,
                "avg_failure": 0.0,
                "highest_risk": 0.0,
                "lowest_health": 100.0,
                "avg_confidence": 0.0
            }
            
        fail_probs = [r.get("failure_probability", 0.0) for r in filtered_records]
        health_scores = [r.get("health_score", 100.0) for r in filtered_records]
        confidences = [r.get("confidence", 0.0) for r in filtered_records]
        
        return {
            "total": total,
            "avg_failure": sum(fail_probs) / total,
            "highest_risk": max(fail_probs),
            "lowest_health": min(health_scores),
            "avg_confidence": sum(confidences) / total
        }

    def export_to_csv(self, filepath: str, filtered_records: List[Dict[str, Any]]) -> bool:
        """Exports the provided records to a CSV file."""
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                if not filtered_records:
                    return True
                
                writer = csv.DictWriter(f, fieldnames=filtered_records[0].keys())
                writer.writeheader()
                writer.writerows(filtered_records)
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False

    def export_to_excel(self, filepath: str, filtered_records: List[Dict[str, Any]]) -> bool:
        """Exports to Excel if pandas/openpyxl is available, else falls back to CSV."""
        try:
            import pandas as pd
            df = pd.DataFrame(filtered_records)
            df.to_excel(filepath, index=False)
            return True
        except ImportError:
            logger.warning("Pandas or openpyxl missing. Falling back to CSV export instead of Excel.")
            fallback_path = filepath.replace(".xlsx", ".csv")
            return self.export_to_csv(fallback_path, filtered_records)
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")
            return False
