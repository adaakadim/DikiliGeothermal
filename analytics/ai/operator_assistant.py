from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

from simulation.sensors import SensorReading
from analytics.fault_detector import SystemHealth, FaultReport
from scada.event_engine import event_engine, EventType, EventSeverity
from scada.incident_engine import incident_engine

@dataclass
class AIAssessment:
    timestamp: float = field(default_factory=time.time)
    plant_status: str = "NORMAL"
    health_summary: Dict[str, SystemHealth] = field(default_factory=dict)
    operational_recs: List[str] = field(default_factory=list)
    maintenance_recs: List[str] = field(default_factory=list)
    energy_opt_recs: List[str] = field(default_factory=list)
    alarm_explanations: List[str] = field(default_factory=list)
    confidence_score: float = 95.0

class AIOperatorAssistant:
    """AI Assistant that continuously monitors plant state and provides recommendations."""
    
    def __init__(self):
        self._last_assessment = AIAssessment()
        self._last_recommendations: set = set()

    def evaluate(self, readings: List[SensorReading], fault_reports: Dict[str, FaultReport]) -> AIAssessment:
        assessment = AIAssessment()
        
        # 1. Health Summary
        for wid, rpt in fault_reports.items():
            assessment.health_summary[wid] = rpt.health
            
            # 2. Operational & Maintenance Recommendations based on Faults
            if rpt.risk_score > 60:
                assessment.maintenance_recs.append(f"Monitor {wid} vibration. High risk of failure.")
            elif rpt.risk_score > 30:
                assessment.maintenance_recs.append(f"{wid} efficiency slightly decreasing. Schedule check.")

        # 3. Process Readings for Operational & Energy Recommendations
        total_flow = 0.0
        avg_temp = 0.0
        if readings:
            total_flow = sum(r.flow_m3h for r in readings)
            avg_temp = sum(r.temperature_c for r in readings) / len(readings)

        # Operational Heuristics
        for r in readings:
            # Example heuristic: if temperature is dropping but flow is high, thermal drawdown
            if r.temperature_c < 80.0 and r.flow_m3h > 150.0:
                assessment.operational_recs.append(f"Thermal drawdown on {r.well_id}. Reduce flow to recover temperature.")
            # Example heuristic: if flow is very low, it's approaching limits
            if r.flow_m3h < 60.0:
                assessment.operational_recs.append(f"Production flow {r.well_id} approaching advisory minimum level.")

        # Energy Optimization Heuristics
        if total_flow > 250.0 and avg_temp > 100.0:
            assessment.energy_opt_recs.append("High flow and temperature detected. District heating demand increasing.")
            assessment.energy_opt_recs.append("Consider throttling bypass to optimize heat exchanger efficiency.")

        # 4. Alarm Explanations from Incidents
        active_incidents = incident_engine.get_active_incidents()
        for inc in active_incidents:
            if inc.severity in [EventSeverity.CRITICAL, EventSeverity.FATAL]:
                assessment.plant_status = "CRITICAL"
                assessment.alarm_explanations.append(f"Incident {inc.incident_id} ({inc.equipment}) is driving critical state. Check timeline.")
            elif inc.severity == EventSeverity.WARNING and assessment.plant_status != "CRITICAL":
                assessment.plant_status = "WARNING"
                
        if not active_incidents and all(h == SystemHealth.GOOD for h in assessment.health_summary.values()):
            assessment.plant_status = "NOMINAL"
            assessment.confidence_score = 98.0
        else:
            assessment.confidence_score = max(50.0, 95.0 - (len(active_incidents) * 5.0))

        self._broadcast_new_recommendations(assessment)
        self._last_assessment = assessment
        return assessment

    def _broadcast_new_recommendations(self, assessment: AIAssessment):
        """Broadcasts only new recommendations to the Event Engine."""
        current_recs = set(
            assessment.operational_recs + 
            assessment.maintenance_recs + 
            assessment.energy_opt_recs + 
            assessment.alarm_explanations
        )
        
        new_recs = current_recs - self._last_recommendations
        
        for rec in new_recs:
            event_engine.log_event(
                EventType.AI_RECOMMENDATION, 
                "AI_ASSISTANT", 
                rec, 
                EventSeverity.INFO,
                metadata={"confidence": assessment.confidence_score}
            )
            
        self._last_recommendations = current_recs

    @property
    def last_assessment(self) -> AIAssessment:
        return self._last_assessment

# Global Instance
ai_assistant = AIOperatorAssistant()
