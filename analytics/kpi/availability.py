"""
analytics/kpi/availability.py
Calculates equipment and plant availability.
"""

class AvailabilityCalculator:
    def __init__(self):
        self._uptime_ticks = 0
        self._total_ticks = 0
        
    def calculate(self, live_data: dict, ai_result: dict) -> dict:
        kpis = {}
        
        self._total_ticks += 1
        # Consider plant "available" if pump is running or healthy
        if live_data.get("Pump Running (0/1)", 0) == 1 or ai_result.get("Pump Failure Probability (%)", 0) < 80:
            self._uptime_ticks += 1
            
        uptime_pct = (self._uptime_ticks / self._total_ticks) * 100.0 if self._total_ticks > 0 else 100.0
        
        kpis["Equipment Availability (%)"] = uptime_pct
        kpis["Plant Availability (%)"] = uptime_pct # Simplified
        
        return kpis
