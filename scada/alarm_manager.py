"""
scada/alarm_manager.py
Alarm detection, acknowledgement, and event log.
"""

import time
import logging
import csv
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class AlarmPriority(Enum):
    CRITICAL = 1   # Shutdown / immediate action required
    HIGH     = 2   # Urgent operator response
    WARNING  = 3   # Operator attention (alias for MEDIUM)
    MEDIUM   = 3   # Backward compatibility
    INFO     = 4   # Advisory / informational
    LOW      = 4   # Backward compatibility

class AlarmState(Enum):
    ACTIVE       = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLEARED      = "CLEARED"

class AlarmCategory(Enum):
    TRADITIONAL = "TRADITIONAL"
    PREDICTIVE_AI = "PREDICTIVE_AI"
    SYSTEM = "SYSTEM"

@dataclass
class AlarmEvent:
    alarm_id: str
    tag_id: str
    description: str
    priority: AlarmPriority
    category: AlarmCategory = AlarmCategory.TRADITIONAL
    state: AlarmState = AlarmState.ACTIVE
    triggered_at: float = field(default_factory=time.time)
    acknowledged_at: Optional[float] = None
    cleared_at: Optional[float] = None
    operator: Optional[str] = None

    @property
    def age_seconds(self) -> float:
        end_time = self.cleared_at if self.state == AlarmState.CLEARED and self.cleared_at else time.time()
        return end_time - self.triggered_at

@dataclass
class EventRecord:
    timestamp: float
    category: str
    equipment: str
    description: str

class AlarmManager:
    """Manages alarm detection, acknowledgement, and event histories."""

    def __init__(self, max_history: int = 5000):
        from collections import deque
        from core.configuration import config
        self._max_history = config.get("performance.max_history_size", max_history)
        self._active: dict[str, AlarmEvent] = {}
        self._history = deque(maxlen=self._max_history)
        self._event_history = deque(maxlen=self._max_history)


        # Statistics trackers
        self._today_count = 0
        self._critical_count = 0
        self._equipment_counts: Dict[str, int] = {}
        self._alarm_id_counts: Dict[str, int] = {}

        # Pre-create export dir
        Path("data/exports").mkdir(parents=True, exist_ok=True)
        
        # --- Add Mock Data for UI Demonstration ---
        self._add_mock_data()
        
    def _add_mock_data(self):
        # Add some historical events
        self.record_event("SYSTEM", "Main Server", "System boot sequence initiated.")
        self.record_event("MAINTENANCE", "P-101", "Routine inspection completed.")
        self.record_event("OPERATOR", "Admin", "User logged in.")
        
        # Add some cleared alarms to history
        import random
        for i in range(15):
            t = time.time() - random.randint(1000, 100000)
            a = AlarmEvent(
                alarm_id=f"HIST_ALARM_{i}", tag_id=random.choice(["P-101", "GW-01", "HX-101", "SEP-01"]),
                description=f"Historical threshold violation {i}",
                priority=random.choice(list(AlarmPriority)),
                state=AlarmState.CLEARED,
                triggered_at=t, acknowledged_at=t + 100, cleared_at=t + 500
            )
            self._history.append(a)
            self._equipment_counts[a.tag_id] = self._equipment_counts.get(a.tag_id, 0) + 1
            
        # Add some active alarms
        self.raise_alarm("P101_VIB", "P-101", "High vibration detected on motor casing", AlarmPriority.HIGH)
        self.raise_alarm("HX_TEMP_LO", "HX-101", "Outlet temperature below setpoint", AlarmPriority.WARNING)
        self.raise_alarm("SEP_LVL_HI", "SEP-01", "Brine level approaching limit", AlarmPriority.CRITICAL)

    def raise_alarm(
        self,
        alarm_id: str,
        tag_id: str,
        description: str,
        priority: AlarmPriority = AlarmPriority.WARNING,
        category: AlarmCategory = AlarmCategory.TRADITIONAL,
    ) -> AlarmEvent:
        if alarm_id not in self._active:
            evt = AlarmEvent(alarm_id, tag_id, description, priority, category)
            self._active[alarm_id] = evt
            
            # Update stats
            self._today_count += 1
            if priority == AlarmPriority.CRITICAL:
                self._critical_count += 1
            self._equipment_counts[tag_id] = self._equipment_counts.get(tag_id, 0) + 1
            self._alarm_id_counts[alarm_id] = self._alarm_id_counts.get(alarm_id, 0) + 1
            
            logger.warning(
                "[%s ALARM %s] %s | Tag: %s | Priority: %s",
                category.name, alarm_id, description, tag_id, priority.name,
            )
            return evt
        return self._active[alarm_id]

    def clear_alarm(self, alarm_id: str):
        if alarm_id in self._active:
            evt = self._active.pop(alarm_id)
            evt.state = AlarmState.CLEARED
            evt.cleared_at = time.time()
            self._history.append(evt)
            logger.info("[ALARM CLEAR] %s", alarm_id)


    def acknowledge(self, alarm_id: str, operator: str = "SYSTEM") -> bool:
        if alarm_id in self._active:
            self._active[alarm_id].state = AlarmState.ACKNOWLEDGED
            self._active[alarm_id].acknowledged_at = time.time()
            self._active[alarm_id].operator = operator
            logger.info("[ACK] Alarm %s acknowledged by %s", alarm_id, operator)
            from security.audit import AuditLogger
            AuditLogger.log_event("Alarm Acknowledgement", "scada.alarms", "SUCCESS", "INFO", operator, details=f"Alarm ID: {alarm_id}")
            return True
        return False

    def record_event(self, category: str, equipment: str, description: str):
        evt = EventRecord(time.time(), category, equipment, description)
        self._event_history.append(evt)
        logger.info("[EVENT] %s | %s | %s", category, equipment, description)


    @property
    def active_alarms(self) -> List[AlarmEvent]:
        return sorted(self._active.values(), key=lambda a: a.priority.value)

    @property
    def alarm_history(self) -> List[AlarmEvent]:
        return list(self._history)

    @property
    def event_history(self) -> List[EventRecord]:
        return list(self._event_history)

    @property
    def unacknowledged_count(self) -> int:
        return sum(1 for a in self._active.values() if a.state == AlarmState.ACTIVE)

    @property
    def critical_active(self) -> bool:
        return any(
            a.priority == AlarmPriority.CRITICAL for a in self._active.values()
        )

    def get_statistics(self) -> dict:
        total_duration = 0.0
        longest_duration = 0.0
        all_alarms = list(self._active.values()) + list(self._history)
        
        distribution = {"CRITICAL": 0, "HIGH": 0, "WARNING": 0, "INFO": 0}
        
        for a in all_alarms:
            dur = a.age_seconds
            total_duration += dur
            if dur > longest_duration:
                longest_duration = dur
            distribution[a.priority.name] += 1
            
        avg_duration = total_duration / len(all_alarms) if all_alarms else 0.0
        
        most_frequent = max(self._alarm_id_counts, key=self._alarm_id_counts.get) if self._alarm_id_counts else "None"
        most_affected = max(self._equipment_counts, key=self._equipment_counts.get) if self._equipment_counts else "None"

        return {
            "active_count": len(self._active),
            "today_count": self._today_count,
            "critical_count": self._critical_count,
            "most_frequent": most_frequent,
            "avg_duration": avg_duration,
            "longest_duration": longest_duration,
            "most_affected": most_affected,
            "distribution": distribution
        }

    def export_alarms_csv(self) -> str:
        filepath = Path("data/exports") / f"alarm_history_{int(time.time())}.csv"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Equipment", "Alarm Name", "Severity", "Status", "Duration (s)", "ACK Time", "Clear Time"])
            for a in self._history:
                from datetime import datetime
                ts = datetime.fromtimestamp(a.triggered_at).strftime("%Y-%m-%d %H:%M:%S")
                ack = datetime.fromtimestamp(a.acknowledged_at).strftime("%Y-%m-%d %H:%M:%S") if a.acknowledged_at else ""
                clr = datetime.fromtimestamp(a.cleared_at).strftime("%Y-%m-%d %H:%M:%S") if a.cleared_at else ""
                writer.writerow([ts, a.tag_id, a.alarm_id, a.priority.name, a.state.value, round(a.age_seconds, 1), ack, clr])
        return str(filepath)

    def export_events_csv(self) -> str:
        filepath = Path("data/exports") / f"event_history_{int(time.time())}.csv"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Category", "Equipment", "Description"])
            for e in self._event_history:
                from datetime import datetime
                ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([ts, e.category, e.equipment, e.description])
        return str(filepath)

    def summary(self) -> dict:
        return {
            "total_active": len(self._active),
            "unacknowledged": self.unacknowledged_count,
            "critical": self.critical_active,
            "alarms": [
                {
                    "id": a.alarm_id,
                    "description": a.description,
                    "priority": a.priority.name,
                    "category": a.category.name,
                    "state": a.state.value,
                    "age_s": round(a.age_seconds, 1),
                }
                for a in self.active_alarms
            ],
        }
