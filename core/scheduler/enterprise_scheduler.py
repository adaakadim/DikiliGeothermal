"""
core/scheduler/enterprise_scheduler.py
======================================
Enterprise Scheduler to manage periodic background tasks with priority tiers.
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Dict, List, Optional

logger = logging.getLogger("core.scheduler")

class TaskPriority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3

class ScheduledTask:
    def __init__(
        self, 
        name: str, 
        action: Callable[[], Any], 
        interval: float, 
        priority: TaskPriority = TaskPriority.NORMAL, 
        enabled: bool = True,
        module: str = "custom"
    ):
        self.name = name
        self.action = action
        self.interval = interval
        self.priority = priority
        self.enabled = enabled
        self.module = module
        
        # Metrics
        self.last_execution_time = 0.0
        self.next_execution_time = time.time()
        self.average_execution_time = 0.0
        self.execution_count = 0
        self.failure_count = 0
        self.total_execution_duration = 0.0
        self.missed_cycles = 0
        self.late_executions = 0

class EnterpriseScheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EnterpriseScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._tasks: Dict[str, ScheduledTask] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True
        
        # Load configs
        from core.configuration import config
        self._warning_threshold = config.get("performance.scheduler.warning_threshold_s", 1.5)

    def register_task(
        self, 
        name: str, 
        action: Callable[[], Any], 
        interval: float, 
        priority: TaskPriority = TaskPriority.NORMAL, 
        enabled: bool = True,
        module: str = "custom"
    ):
        """Registers a periodic background task. Prevents duplicates."""
        if name in self._tasks:
            logger.error(f"Task '{name}' is already registered in Enterprise Scheduler.")
            raise ValueError(f"Duplicate task registration: {name}")
            
        task = ScheduledTask(name, action, interval, priority, enabled, module)
        self._tasks[name] = task
        logger.info(f"Registered periodic task: {name} (Interval: {interval}s, Priority: {priority.name})")

    def unregister_task(self, name: str):
        """Removes a task from the scheduler."""
        if name in self._tasks:
            del self._tasks[name]
            logger.info(f"Unregistered task: {name}")

    def start(self):
        """Starts the background execution worker thread."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="EnterpriseSchedulerWorker", daemon=True)
        self._thread.start()
        logger.info("Enterprise Scheduler background worker started.")

    def shutdown(self, timeout: float = 2.0):
        """Gracefully stops the scheduler thread."""
        logger.info("Stopping Enterprise Scheduler background worker...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None
        logger.info("Enterprise Scheduler background worker stopped.")

    def _run_loop(self):
        """Worker thread loop dispatching tasks based on priorities and time."""
        while not self._stop_event.is_set():
            now = time.time()
            
            # Filter and sort enabled ready tasks based on priority (HIGH first) and execution order
            ready_tasks: List[ScheduledTask] = []
            for task in self._tasks.values():
                if task.enabled and now >= task.next_execution_time:
                    ready_tasks.append(task)
                    
            ready_tasks.sort(key=lambda t: (t.priority.value, t.next_execution_time))
            
            for task in ready_tasks:
                if self._stop_event.is_set():
                    break
                    
                # Track latency / missed cycles
                lat = now - task.next_execution_time
                if lat > 0.05: # late by more than 50ms
                    task.late_executions += 1
                if lat > task.interval:
                    task.missed_cycles += int(lat // task.interval)
                    
                # Execute
                start_run = time.time()
                try:
                    task.action()
                except Exception as e:
                    task.failure_count += 1
                    logger.error(f"Task '{task.name}' execution failed: {e}")
                finally:
                    end_run = time.time()
                    duration = end_run - start_run
                    task.last_execution_time = start_run
                    task.total_execution_duration += duration
                    task.execution_count += 1
                    task.average_execution_time = task.total_execution_duration / task.execution_count
                    task.next_execution_time = start_run + task.interval
                    
                    if duration > self._warning_threshold:
                        logger.warning(
                            f"[SCHEDULER ALERT] Task '{task.name}' execution duration {duration:.2f}s "
                            f"exceeded threshold of {self._warning_threshold:.2f}s."
                        )
                        
            # Short sleep to prevent CPU spinning
            time.sleep(0.05)

    def get_diagnostics(self) -> List[Dict[str, Any]]:
        """Returns execution diagnostics for all registered tasks."""
        diag = []
        for task in self._tasks.values():
            diag.append({
                "name": task.name,
                "module": task.module,
                "interval": task.interval,
                "priority": task.priority.name,
                "enabled": task.enabled,
                "execution_count": task.execution_count,
                "average_execution_time_ms": round(task.average_execution_time * 1000, 2),
                "failure_count": task.failure_count,
                "missed_cycles": task.missed_cycles,
                "late_executions": task.late_executions,
                "next_run_epoch": task.next_execution_time
            })
        return diag
