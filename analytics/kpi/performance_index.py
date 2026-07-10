"""
analytics/kpi/performance_index.py
Calculates maintenance readiness and alarm severity indices.
"""

class PerformanceIndexCalculator:
    def __init__(self):
        pass
        
    def calculate(self, live_data: dict, ai_result: dict, maint_rec: dict) -> dict:
        kpis = {}
        
        # 1. Maintenance Readiness Index
        # Based on how clear the recommendations are and health scores
        maint_action = maint_rec.get("action", "Unknown")
        if maint_action == "Schedule Maintenance (High Priority)":
            mri = 40.0
        elif maint_action == "Schedule Inspection":
            mri = 70.0
        elif maint_action == "Continue Monitoring":
            mri = 100.0
        else:
            mri = 85.0
            
        kpis["Maintenance Readiness Index (%)"] = mri
        
        # 2. Alarm Severity Index
        alarm_count = live_data.get("Alarm Count", 0)
        # Severity increases exponentially with alarm count
        severity = min(100.0, alarm_count * 20.0)
        kpis["Alarm Severity Index (%)"] = severity
        
        # 3. Prediction Confidence Average
        kpis["Prediction Confidence Average (%)"] = ai_result.get("Prediction Confidence (%)", 0.0)
        
        return kpis
