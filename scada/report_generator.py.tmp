"""
scada/report_generator.py
=========================
Generates daily or triggered operational reports.
Dumps CSV and JSON reports to the data/reports directory.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_report(
        self, 
        ai_result: Dict[str, Any], 
        health_indexes: Dict[str, float], 
        maint_rec: Dict[str, Any],
        alarm_summary: Dict[str, Any]
    ) -> str:
        """Generates the report and returns the file path."""
        timestamp = datetime.now()
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        report_data = {
            "Timestamp": timestamp.isoformat(),
            "AI_Pump_Failure_Risk_Pct": ai_result.get("Pump Failure Probability (%)", 0.0),
            "AI_Confidence_Pct": ai_result.get("Prediction Confidence (%)", 0.0),
            "Plant_Status": ai_result.get("Plant Status", "UNKNOWN"),
            "Overall_Plant_Health_Pct": health_indexes.get("Overall Plant Health", 0.0),
            "Pump_Health_Pct": health_indexes.get("Pump Health", 0.0),
            "Maintenance_Risk_Level": maint_rec.get("Risk Level", "LOW"),
            "Maintenance_Recommendations": maint_rec.get("Recommended Actions", []),
            "Active_Alarms_Count": alarm_summary.get("total_active", 0),
            "Critical_Alarms_Active": alarm_summary.get("critical", False)
        }

        # Save JSON
        json_path = os.path.join(self.output_dir, f"report_{ts_str}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)

        # Save CSV
        csv_path = os.path.join(self.output_dir, f"report_{ts_str}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(report_data.keys())
            
            # Convert lists to strings for CSV
            row_data = []
            for v in report_data.values():
                if isinstance(v, list):
                    row_data.append(" | ".join(v))
                else:
                    row_data.append(v)
            writer.writerow(row_data)

        return json_path
