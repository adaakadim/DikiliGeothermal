"""
tests/test_performance_monitor.py
==================================
Automated unit tests for the Performance Monitoring & Profiling Framework.
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

import os
import pytest
from core.performance.performance_monitor import PerformanceMonitor

@pytest.fixture(autouse=True)
def reset_monitor():
    PerformanceMonitor._instance = None
    yield
    PerformanceMonitor._instance = None

def test_performance_monitor_latencies():
    monitor = PerformanceMonitor()
    
    # Record AI latency
    monitor.record_ai_inference(0.05) # 50ms
    monitor.record_ai_inference(0.12) # 120ms
    
    # Record alarm latency
    monitor.record_alarm_processing(0.01) # 10ms
    
    metrics = monitor.get_current_metrics()
    
    assert metrics["ai_inference"]["total_runs"] == 2
    assert metrics["ai_inference"]["avg_latency_ms"] == 85.0
    assert metrics["ai_inference"]["max_latency_ms"] == 120.0
    assert metrics["alarm_manager"]["avg_scan_latency_ms"] == 10.0

def test_metrics_snapshot_and_export(tmp_path):
    monitor = PerformanceMonitor()
    monitor.record_ai_inference(0.04)
    
    # Collect snapshot
    snapshot = monitor.collect_snapshot()
    assert snapshot["ai_inference"]["total_runs"] == 1
    
    export_file = tmp_path / "perf_report.json"
    success = monitor.export_statistics(str(export_file))
    assert success is True
    assert export_file.exists()
    
    # Verify stats clear
    monitor.reset_statistics()
    metrics = monitor.get_current_metrics()
    assert metrics["ai_inference"]["total_runs"] == 0
