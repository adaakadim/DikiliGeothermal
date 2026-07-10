"""
digital_twin/rendering_scheduler.py
===================================
Rendering Scheduler to rate-limit and coalesce HMI and Digital Twin redraw calls.
Prevents canvas execution storms during high frequency SCADA updates.
"""

import time
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class RenderingScheduler:
    def __init__(self, max_fps: float = 10.0):
        self._max_fps = max_fps
        self._interval = 1.0 / max_fps if max_fps > 0 else 0.1
        self._last_run_time = 0.0
        self._pending_task: Optional[Callable[[], Any]] = None
        
        # Metrics
        self._render_times: list[float] = []
        self._dropped_count = 0
        self._total_count = 0

    def schedule(self, task: Callable[[], Any]):
        """Schedules a redraw task, dropping outdated requests if within the frame interval."""
        self._total_count += 1
        now = time.time()
        
        if now - self._last_run_time >= self._interval:
            self._execute(task)
        else:
            # Request coalescing: drop older queued rendering requests
            if self._pending_task is not None:
                self._dropped_count += 1
            self._pending_task = task

    def _execute(self, task: Callable[[], Any]):
        start = time.time()
        try:
            task()
        except Exception as e:
            logger.error(f"Error executing scheduled render task: {e}")
        finally:
            end = time.time()
            self._render_times.append(end - start)
            if len(self._render_times) > 100:
                self._render_times.pop(0)
            self._last_run_time = time.time()
            self._pending_task = None

    def trigger_pending(self):
        """Execute any pending/coalesced redraw task."""
        if self._pending_task:
            self._execute(self._pending_task)

    def get_metrics(self) -> Dict[str, Any]:
        """Compile and return rendering diagnostics."""
        avg_time = sum(self._render_times) / len(self._render_times) if self._render_times else 0.0
        max_time = max(self._render_times) if self._render_times else 0.0
        return {
            "avg_render_time_ms": round(avg_time * 1000, 2),
            "max_render_time_ms": round(max_time * 1000, 2),
            "total_redraw_requests": self._total_count,
            "dropped_redraw_requests": self._dropped_count,
            "queue_depth": 1 if self._pending_task else 0
        }
