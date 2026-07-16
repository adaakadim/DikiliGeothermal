import time
import uuid
import csv
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

class EventType(Enum):
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    MODE_CHANGE = "MODE_CHANGE"
    ALARM_GENERATED = "ALARM_GENERATED"
    ALARM_ACKNOWLEDGED = "ALARM_ACKNOWLEDGED"
    ALARM_CLEARED = "ALARM_CLEARED"
    PUMP_STARTED = "PUMP_STARTED"
    PUMP_STOPPED = "PUMP_STOPPED"
    VALVE_OPENED = "VALVE_OPENED"
    VALVE_CLOSED = "VALVE_CLOSED"
    MAINTENANCE_STARTED = "MAINTENANCE_STARTED"
    MAINTENANCE_FINISHED = "MAINTENANCE_FINISHED"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    GENERIC = "GENERIC"

class EventSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"

@dataclass
class PlantEvent:
    event_id: str
    timestamp: float
    event_type: EventType
    equipment: str
    description: str
    severity: EventSeverity
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventEngine:
    """Centralized engine for capturing discrete plant events."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventEngine, cls).__new__(cls)
            cls._instance._events = []
            cls._instance._subscribers = []
            Path("data/exports").mkdir(parents=True, exist_ok=True)
        return cls._instance

    def subscribe(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def log_event(self, event_type: EventType, equipment: str, description: str, severity: EventSeverity = EventSeverity.INFO, metadata: Dict[str, Any] = None) -> PlantEvent:
        event = PlantEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type=event_type,
            equipment=equipment,
            description=description,
            severity=severity,
            metadata=metadata or {}
        )
        self._events.append(event)
        
        # Notify subscribers (like the IncidentEngine)
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass
                
        return event

    def get_recent_events(self, limit: int = 100) -> List[PlantEvent]:
        return self._events[-limit:]

    def export_events_csv(self) -> str:
        filepath = Path("data/exports") / f"event_log_{int(time.time())}.csv"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Event ID", "Type", "Equipment", "Description", "Severity"])
            from datetime import datetime
            for e in self._events:
                ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([ts, e.event_id, e.event_type.value, e.equipment, e.description, e.severity.value])
        return str(filepath)

# Global singleton
event_engine = EventEngine()
