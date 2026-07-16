"""
core/historian/historian.py
===========================
SQLite-based Data Historian for archiving SCADA and AI data.
Optimized with in-memory write buffering to minimize disk commits.
"""

import sqlite3
import logging
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DataHistorian:
    """
    Manages long-term storage of SCADA tags, AI predictions, and system events.
    Optimized with batch write queues and configurable flush intervals.
    """

    def __init__(self, db_path: str = "data/historian.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        
        # Buffer and Flush State
        self._write_buffer: List[Dict[str, Any]] = []
        self._last_flush_time = time.time()
        self._last_successful_write = time.time()
        self._total_writes_count = 0
        
        # Load performance limits
        from core.configuration import config
        self._batch_size = config.get("performance.historian.batch_size", 50)
        self._flush_interval_s = config.get("performance.historian.flush_interval_s", 5.0)
        self._queue_limit = config.get("performance.historian.queue_size_limit", 1000)
        
        self._init_db()

    def _init_db(self):
        """Initialize SQLite tables if they do not exist."""
        try:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self._conn.cursor()
            
            # Table for Sensor Readings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    well_id TEXT,
                    temperature_c REAL,
                    pressure_bar REAL,
                    flow_m3h REAL,
                    is_healthy BOOLEAN
                )
            ''')
            
            # Table for AI Predictions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    well_id TEXT,
                    pump_failure_prob REAL,
                    health_status TEXT,
                    risk_score REAL,
                    rul_hours REAL,
                    rul_confidence REAL
                )
            ''')
            
            # Table for Alarms
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    alarm_id TEXT,
                    description TEXT,
                    priority TEXT,
                    status TEXT
                )
            ''')
            
            self._conn.commit()
            logger.info(f"Historian initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Historian DB initialization error: {e}")

    def _queue_write(self, query: str, params: tuple):
        """Queue a write query in memory and check flush limits."""
        if len(self._write_buffer) >= self._queue_limit:
            logger.warning("[HISTORIAN] Queue limit exceeded! Forcing synchronous flush.")
            self.flush()
            
        self._write_buffer.append({"query": query, "params": params})
        
        # Check automatic flush triggers
        now = time.time()
        if (len(self._write_buffer) >= self._batch_size) or (now - self._last_flush_time >= self._flush_interval_s):
            self.flush()

    def flush(self):
        """Flush in-memory queue to the SQLite database in a single transaction."""
        if not self._conn or not self._write_buffer:
            return
            
        try:
            cursor = self._conn.cursor()
            # Wrap all buffered insertions in a single transaction
            cursor.execute("BEGIN TRANSACTION")
            for item in self._write_buffer:
                cursor.execute(item["query"], item["params"])
            self._conn.commit()
            
            self._total_writes_count += len(self._write_buffer)
            self._write_buffer.clear()
            self._last_flush_time = time.time()
            self._last_successful_write = time.time()
        except sqlite3.Error as e:
            logger.error(f"Historian buffer flush error: {e}")
            try:
                self._conn.rollback()
            except sqlite3.Error:
                pass

    def log_sensor_reading(self, well_id: str, temp: float, pres: float, flow: float, healthy: bool):
        ts = datetime.now().isoformat()
        query = '''
            INSERT INTO sensor_readings (timestamp, well_id, temperature_c, pressure_bar, flow_m3h, is_healthy)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (ts, well_id, temp, pres, flow, healthy)
        self._queue_write(query, params)

    def log_ai_prediction(self, well_id: str, prob: float, health: str, risk: float, rul_hours: float = 0.0, rul_conf: float = 0.0):
        ts = datetime.now().isoformat()
        query = '''
            INSERT INTO ai_predictions (timestamp, well_id, pump_failure_prob, health_status, risk_score, rul_hours, rul_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (ts, well_id, prob, health, risk, rul_hours, rul_conf)
        self._queue_write(query, params)

    def log_alarm(self, alarm_id: str, desc: str, priority: str, status: str):
        ts = datetime.now().isoformat()
        query = '''
            INSERT INTO alarms (timestamp, alarm_id, description, priority, status)
            VALUES (?, ?, ?, ?, ?)
        '''
        params = (ts, alarm_id, desc, priority, status)
        self._queue_write(query, params)

    def query_sensor_history(self, start_iso: str, end_iso: str, well_id: str = None) -> list:
        # Flush pending buffered writes first to guarantee read consistency
        self.flush()
        
        if not self._conn: return []
        try:
            cursor = self._conn.cursor()
            if well_id:
                cursor.execute('''
                    SELECT timestamp, well_id, temperature_c, pressure_bar, flow_m3h, is_healthy
                    FROM sensor_readings
                    WHERE timestamp BETWEEN ? AND ? AND well_id = ?
                    ORDER BY timestamp ASC
                ''', (start_iso, end_iso, well_id))
            else:
                cursor.execute('''
                    SELECT timestamp, well_id, temperature_c, pressure_bar, flow_m3h, is_healthy
                    FROM sensor_readings
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                ''', (start_iso, end_iso))
            
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Historian query_sensor_history error: {e}")
            return []
            
    def get_time_range(self):
        """Returns the earliest and latest timestamps in the DB."""
        self.flush()
        if not self._conn: return None, None
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_readings")
            row = cursor.fetchone()
            return row[0], row[1]
        except sqlite3.Error as e:
            logger.error(f"Historian get_time_range error: {e}")
            return None, None
            
    def get_snapshot_at(self, target_iso: str) -> list:
        """Returns the most recent sensor reading for each well at or before target_iso."""
        self.flush()
        if not self._conn: return []
        try:
            cursor = self._conn.cursor()
            cursor.execute('''
                SELECT t1.timestamp, t1.well_id, t1.temperature_c, t1.pressure_bar, t1.flow_m3h, t1.is_healthy
                FROM sensor_readings t1
                INNER JOIN (
                    SELECT well_id, MAX(timestamp) as max_ts
                    FROM sensor_readings
                    WHERE timestamp <= ?
                    GROUP BY well_id
                ) t2 ON t1.well_id = t2.well_id AND t1.timestamp = t2.max_ts
            ''', (target_iso,))
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Historian get_snapshot_at error: {e}")
            return []

    def export_sensor_history_csv(self, start_iso: str, end_iso: str, well_id: str = None) -> str:
        # Query calls flush automatically
        data = self.query_sensor_history(start_iso, end_iso, well_id)
        if not data:
            return ""
            
        import csv
        import pathlib
        
        export_dir = pathlib.Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = well_id if well_id else "ALL"
        filepath = export_dir / f"sensor_history_{prefix}_{ts}.csv"
        
        from security.audit import AuditLogger
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            AuditLogger.log_event("Historian Export", "core.historian", "SUCCESS", "INFO", details=f"Exported data range {start_iso} to {end_iso} for {prefix}")
            return str(filepath.absolute())
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            AuditLogger.log_event("Historian Export", "core.historian", "FAIL", "WARN", details=f"Failed export for range {start_iso} to {end_iso}: {e}")
            return ""

    def run_retention_policy(self):
        """Prepare configurable retention policy parameters. Logging only to preserve production data."""
        logger.info("[HISTORIAN] Retention policy check completed.")

    def get_health_status(self) -> Dict[str, Any]:
        """Returns diagnostic parameters for database sizing and connection statistics."""
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        try:
            total, used, free = shutil.disk_usage(self.db_path.parent)
            free_disk_gb = free / (1024.0**3)
        except Exception:
            free_disk_gb = 0.0
            
        return {
            "database_size_bytes": db_size,
            "free_disk_gb": round(free_disk_gb, 2),
            "last_successful_write": self._last_successful_write,
            "queue_size": len(self._write_buffer),
            "batch_size": self._batch_size,
            "total_writes_count": self._total_writes_count
        }

    def close(self):
        # Force flush remaining writes on shutdown
        self.flush()
        if self._conn:
            self._conn.close()
            self._conn = None
