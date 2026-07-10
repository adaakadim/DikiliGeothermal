"""
tests/test_rendering_performance.py
====================================
Automated unit tests for the Rendering Scheduler and rate-limited Canvas updates.
"""

import sys
from unittest.mock import MagicMock

# Mock optional packages to run tests without HMI plotting requirements
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['matplotlib.animation'] = MagicMock()
sys.modules['matplotlib.gridspec'] = MagicMock()
sys.modules['matplotlib.lines'] = MagicMock()
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import time
import pytest
from digital_twin.rendering_scheduler import RenderingScheduler

def test_rendering_coalescing():
    # Set max FPS to 2.0 (interval = 0.5s)
    scheduler = RenderingScheduler(max_fps=2.0)
    
    counter = [0]
    def increment():
        counter[0] += 1
        
    # First execution should run immediately
    scheduler.schedule(increment)
    assert counter[0] == 1
    
    # Second execution within 0.5s should be coalesced/pending
    scheduler.schedule(increment)
    assert counter[0] == 1 # still 1
    
    # Third execution should overwrite the second (coalesced)
    scheduler.schedule(increment)
    assert counter[0] == 1 # still 1
    
    metrics = scheduler.get_metrics()
    # 3 total requests, 1 immediate execution, 1 dropped (the second got overwritten by the third)
    assert metrics["total_redraw_requests"] == 3
    assert metrics["dropped_redraw_requests"] == 1
    assert metrics["queue_depth"] == 1
    
    # Force trigger pending task
    scheduler.trigger_pending()
    assert counter[0] == 2
    
    metrics_after = scheduler.get_metrics()
    assert metrics_after["queue_depth"] == 0

def test_rendering_metrics_accuracy():
    scheduler = RenderingScheduler(max_fps=100.0)
    
    # Run multiple immediate tasks
    for i in range(5):
        scheduler.schedule(lambda: time.sleep(0.001))
        # Sleep to exceed frame interval
        time.sleep(0.015)
        
    metrics = scheduler.get_metrics()
    assert metrics["total_redraw_requests"] == 5
    assert metrics["dropped_redraw_requests"] == 0
    assert metrics["avg_render_time_ms"] > 0
    assert metrics["max_render_time_ms"] >= metrics["avg_render_time_ms"]
