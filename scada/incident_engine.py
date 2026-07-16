import time
import uuid
import csv
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

from scada.event_engine import PlantEvent, EventType, EventSeverity, event_engine

class IncidentStatus(Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

@dataclass
class Incident:
    incident_id: str
    start_time: float
    equipment: str
    severity: EventSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    end_time: Optional[float] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    timeline: List[PlantEvent] = field(default_factory=list)
    operator_actions: List[str] = field(default_factory=list)
    ai_recommendations: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

class IncidentEngine:
    """Groups related events into Incidents."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IncidentEngine, cls).__new__(cls)
            cls._instance._incidents = {}
            cls._instance._history = []
            Path("data/exports").mkdir(parents=True, exist_ok=True)
            # Subscribe to the event engine
            event_engine.subscribe(cls._instance._process_event)
        return cls._instance

    def _process_event(self, event: PlantEvent):
        # Determine if we should create a new incident or append to an existing one
        equipment = event.equipment
        
        # We group incidents by equipment. If an incident is active for this equipment, append to it.
        if equipment in self._incidents:
            incident = self._incidents[equipment]
            incident.timeline.append(event)
            
            # Upgrade severity if needed
            if event.severity.value == "FATAL":
                incident.severity = EventSeverity.FATAL
            elif event.severity.value == "CRITICAL" and incident.severity.value not in ["FATAL", "CRITICAL"]:
                incident.severity = EventSeverity.CRITICAL
                
            if event.event_type == EventType.AI_RECOMMENDATION:
                incident.ai_recommendations.append(event.description)
                
            # If the event implies resolution, we can optionally auto-resolve (e.g. MAINTENANCE_FINISHED)
            if event.event_type == EventType.MAINTENANCE_FINISHED or event.event_type == EventType.ALARM_CLEARED:
                # We won't automatically close, but maybe flag it. For now, keep it simple.
                pass
                
        else:
            # Should we start an incident?
            # Typically alarms or failures start incidents.
            if event.event_type in [EventType.ALARM_GENERATED, EventType.PUMP_STOPPED, EventType.MAINTENANCE_STARTED]:
                if event.severity in [EventSeverity.WARNING, EventSeverity.CRITICAL, EventSeverity.FATAL]:
                    incident = Incident(
                        incident_id=f"INC-{str(uuid.uuid4())[:8].upper()}",
                        start_time=event.timestamp,
                        equipment=equipment,
                        severity=event.severity
                    )
                    incident.timeline.append(event)
                    self._incidents[equipment] = incident

    def resolve_incident(self, equipment: str, root_cause: str, resolution: str):
        if equipment in self._incidents:
            incident = self._incidents.pop(equipment)
            incident.status = IncidentStatus.RESOLVED
            incident.end_time = time.time()
            incident.root_cause = root_cause
            incident.resolution = resolution
            self._history.append(incident)
            
            event_engine.log_event(
                EventType.GENERIC, 
                equipment, 
                f"Incident {incident.incident_id} resolved: {resolution}", 
                EventSeverity.INFO
            )

    def get_active_incidents(self) -> List[Incident]:
        return list(self._incidents.values())

    def get_history(self) -> List[Incident]:
        return self._history

    def export_incidents_csv(self) -> str:
        filepath = Path("data/exports") / f"incident_report_{int(time.time())}.csv"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Incident ID", "Status", "Equipment", "Severity", "Start Time", "Duration (s)", "Root Cause", "Resolution"])
            from datetime import datetime
            all_incidents = list(self._incidents.values()) + self._history
            for inc in all_incidents:
                ts = datetime.fromtimestamp(inc.start_time).strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    inc.incident_id, 
                    inc.status.value, 
                    inc.equipment, 
                    inc.severity.value, 
                    ts, 
                    round(inc.duration_seconds, 1),
                    inc.root_cause or "N/A",
                    inc.resolution or "N/A"
                ])
        return str(filepath)

# Global singleton
incident_engine = IncidentEngine()
