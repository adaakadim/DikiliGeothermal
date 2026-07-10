"""
core/diagnostics/communication_monitor.py
=========================================
Professional Communication & Network Diagnostics Center.
Continuously monitors communication between major system modules,
measuring heartbeats, latencies, and network statistics.
"""

import time
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    WARNING = "WARNING"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

@dataclass
class CommEvent:
    timestamp: float
    module_name: str
    event_type: str
    message: str

@dataclass
class ModuleStats:
    name: str
    status: ModuleStatus = ModuleStatus.UNKNOWN
    
    # Heartbeat
    last_response_time: float = 0.0
    avg_response_time: float = 0.0
    heartbeat_interval: float = 1.0
    missed_heartbeats: int = 0
    
    # Latency (ms)
    current_latency: float = 0.0
    avg_latency: float = 0.0
    max_latency: float = 0.0
    min_latency: float = 9999.0
    
    # Statistics
    messages_sent: int = 0
    messages_received: int = 0
    dropped_messages: int = 0
    retry_count: int = 0
    errors: int = 0
    timeouts: int = 0
    
    # Internal metrics for averages
    _latency_sum: float = 0.0
    _latency_count: int = 0
    
    def calculate_health_score(self) -> float:
        """Calculate a connection quality score (0.0 to 100.0)."""
        if self.status in [ModuleStatus.OFFLINE, ModuleStatus.FAILED, ModuleStatus.UNKNOWN]:
            return 0.0
            
        score = 100.0
        
        # Deduct for missed heartbeats
        score -= min(30.0, self.missed_heartbeats * 5.0)
        
        # Deduct for dropped messages
        total_msgs = max(1, self.messages_sent + self.messages_received)
        drop_rate = self.dropped_messages / total_msgs
        score -= min(40.0, drop_rate * 200.0)
        
        # Deduct for errors and timeouts
        error_rate = (self.errors + self.timeouts) / total_msgs
        score -= min(30.0, error_rate * 300.0)
        
        # Deduct for high latency (> 100ms)
        if self.avg_latency > 100.0:
            score -= min(20.0, (self.avg_latency - 100.0) * 0.1)
            
        return max(0.0, min(100.0, score))


class CommunicationMonitor:
    def __init__(self):
        self.modules: Dict[str, ModuleStats] = {}
        self.events: List[CommEvent] = []
        
        # Configurable warning thresholds
        self.latency_warning_ms = 150.0
        self.missed_heartbeat_limit = 3
        
        logger.info("Communication Monitor initialized.")

    def register_module(self, name: str, interval: float = 1.0):
        if name not in self.modules:
            self.modules[name] = ModuleStats(name=name, heartbeat_interval=interval, status=ModuleStatus.STARTING)
            self._log_event(name, "CONNECTED", f"Module {name} registered.")

    def record_heartbeat(self, name: str, latency_ms: float = 0.0):
        if name not in self.modules:
            self.register_module(name)
            
        mod = self.modules[name]
        
        # Handle reconnection/recovery
        if mod.status in [ModuleStatus.OFFLINE, ModuleStatus.FAILED]:
            self._log_event(name, "RECOVERED", f"Connection to {name} restored.")
            
        mod.status = ModuleStatus.ONLINE
        mod.last_response_time = time.time()
        mod.missed_heartbeats = 0
        mod.messages_received += 1
        
        self.record_latency(name, latency_ms)

    def record_latency(self, name: str, latency_ms: float):
        if name in self.modules:
            mod = self.modules[name]
            mod.current_latency = latency_ms
            mod.min_latency = min(mod.min_latency, latency_ms)
            mod.max_latency = max(mod.max_latency, latency_ms)
            
            mod._latency_sum += latency_ms
            mod._latency_count += 1
            mod.avg_latency = mod._latency_sum / mod._latency_count
            
            if mod.current_latency > self.latency_warning_ms and mod.status == ModuleStatus.ONLINE:
                mod.status = ModuleStatus.WARNING
                self._log_event(name, "HIGH_LATENCY", f"Latency spike: {latency_ms:.1f}ms")

    def record_error(self, name: str, error_type: str = "error"):
        if name in self.modules:
            mod = self.modules[name]
            if error_type == "timeout":
                mod.timeouts += 1
                self._log_event(name, "TIMEOUT", f"Timeout occurred communicating with {name}.")
            elif error_type == "dropped":
                mod.dropped_messages += 1
            else:
                mod.errors += 1
                self._log_event(name, "ERROR", f"Communication error with {name}.")

    def record_send(self, name: str):
        if name in self.modules:
            self.modules[name].messages_sent += 1

    def evaluate_health(self):
        """Called periodically by the system to evaluate heartbeat timeouts."""
        now = time.time()
        for name, mod in self.modules.items():
            if mod.status not in [ModuleStatus.OFFLINE, ModuleStatus.FAILED]:
                elapsed = now - mod.last_response_time
                if elapsed > mod.heartbeat_interval * self.missed_heartbeat_limit:
                    mod.missed_heartbeats += 1
                    mod.status = ModuleStatus.OFFLINE
                    self._log_event(name, "HEARTBEAT_LOST", f"Lost heartbeat from {name}. Elapsed: {elapsed:.1f}s")
                elif elapsed > mod.heartbeat_interval * 1.5:
                    if mod.status == ModuleStatus.ONLINE:
                        mod.status = ModuleStatus.WARNING
                        self._log_event(name, "HEARTBEAT_DELAYED", f"Delayed heartbeat from {name}.")
                        
    def get_overall_health_score(self) -> float:
        if not self.modules:
            return 100.0
        return sum(m.calculate_health_score() for m in self.modules.values()) / len(self.modules)

    def _log_event(self, module_name: str, event_type: str, message: str):
        event = CommEvent(time.time(), module_name, event_type, message)
        self.events.append(event)
        
        # Log to the existing application logger
        log_msg = f"[COMM_MONITOR] {module_name} | {event_type} | {message}"
        if event_type in ["ERROR", "TIMEOUT", "HEARTBEAT_LOST"]:
            logger.error(log_msg)
        elif event_type in ["WARNING", "HIGH_LATENCY", "HEARTBEAT_DELAYED"]:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
