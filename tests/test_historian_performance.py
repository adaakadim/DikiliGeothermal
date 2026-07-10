"""
tests/test_historian_performance.py
====================================
Automated unit tests for optimized Data Historian writes, buffering, and health checks.
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
from core.historian.historian import DataHistorian
from core.configuration import config

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_historian_perf.db"
    return str(db_file)

def test_write_buffering(temp_db):
    # Set a large batch size so we don't auto-flush
    config.set("performance.historian.batch_size", 100)
    config.set("performance.historian.flush_interval_s", 60.0)
    
    historian = DataHistorian(temp_db)
    
    # Write 3 readings
    for i in range(3):
        historian.log_sensor_reading("GW-01", 85.0 + i, 12.0, 150.0, True)
        
    health = historian.get_health_status()
    # The writes should still be in-memory queue
    assert health["queue_size"] == 3
    assert health["total_writes_count"] == 0
    
    # Query should trigger flush
    data = historian.query_sensor_history("2000-01-01", "2100-01-01", "GW-01")
    assert len(data) == 3
    
    health_after = historian.get_health_status()
    assert health_after["queue_size"] == 0
    assert health_after["total_writes_count"] == 3
    
    historian.close()

def test_close_flushes_remaining_queue(temp_db):
    config.set("performance.historian.batch_size", 100)
    config.set("performance.historian.flush_interval_s", 60.0)
    
    historian = DataHistorian(temp_db)
    historian.log_sensor_reading("GW-01", 90.0, 12.0, 150.0, True)
    
    # Close should flush the write
    historian.close()
    
    # Reopen to verify data is in DB
    historian_reopen = DataHistorian(temp_db)
    data = historian_reopen.query_sensor_history("2000-01-01", "2100-01-01", "GW-01")
    assert len(data) == 1
    historian_reopen.close()

def test_historian_diagnostics_and_retention(temp_db):
    historian = DataHistorian(temp_db)
    
    # Run retention policy check (should log only)
    historian.run_retention_policy()
    
    health = historian.get_health_status()
    assert "database_size_bytes" in health
    assert "free_disk_gb" in health
    assert health["batch_size"] == 100
    
    historian.close()
