"""
tests/test_performance.py
=========================
Automated unit tests for memory management, deques limits, and memory monitor.
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

import pytest
from scada.alarm_manager import AlarmManager, AlarmEvent, AlarmPriority, AlarmState
from core.performance.memory_monitor import MemoryMonitor
from core.configuration import config

def test_bounded_history_buffers():
    # Set config max history size to a small value for testing
    config.set("performance.max_history_size", 5)
    
    manager = AlarmManager(max_history=5)
    
    # Fill event history past the boundary
    for i in range(10):
        manager.record_event("TEST", "EQUIP", f"Event log sequence {i}")
        
    history = manager.event_history
    assert len(history) == 5
    # Should only retain the last 5 events
    assert "sequence 5" in history[0].description
    assert "sequence 9" in history[-1].description

def test_memory_monitor_stats():
    monitor = MemoryMonitor()
    stats = monitor.get_stats()
    
    assert "current_usage_mb" in stats
    assert "peak_usage_mb" in stats
    assert stats["current_usage_mb"] > 0
    assert stats["peak_usage_mb"] >= stats["current_usage_mb"]
    assert stats["warning_threshold_mb"] == config.get("performance.memory_warning_mb")

def test_cleanup_trigger():
    monitor = MemoryMonitor()
    # Should run garbage collection and Matplotlib closing without errors
    monitor.perform_cleanup()
