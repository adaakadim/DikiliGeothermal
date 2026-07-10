"""
data/logger.py
==============
Cycle-by-cycle CSV data logger for the Dikili Geothermal SCADA system.

Appends one row per scan cycle to ``data/logs/scada_data.csv`` (or any
path you configure).  The file is created with a header on first write and
reopened in append mode on subsequent runs, so no data is lost between
restarts.

Columns written per row
-----------------------
    timestamp           ISO-8601 datetime string (local time)
    unix_time           Unix epoch seconds (float, for numeric plotting)
    cycle               Scan cycle counter (integer)
    well_id             Production well tag ID (e.g. "GW-01")
    temperature_c       Wellhead temperature (°C)
    pressure_bar        Wellhead pressure (bar)
    flow_m3h            Flow rate (m³/h)
    pump_state          Derived pump state: RUNNING / STARTING / FAULT
    sensor_healthy      True / False
    risk_score          FaultDetector composite risk score (0–100)
    health_status       GOOD / WARNING / CRITICAL
    active_faults       Pipe-separated list of active fault factor names

One CSV row is written per well per cycle.  For a 3-well setup with a 2-second
scan interval that is 3 rows every 2 s → ~5,400 rows/hour.

Typical usage
-------------
>>> from data.logger import SCADALogger
>>> logger = SCADALogger()
>>> logger.log_cycle(cycle=1, readings=readings, risk_reports=reports)

Or integrate with the dashboard:
>>> from data.logger import SCADALogger
>>> logger = SCADALogger()                    # in __init__
>>> logger.log_cycle(self._cycle, readings, reports)   # in run loop
"""

from __future__ import annotations

import csv
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default output path (relative to project root)
DEFAULT_LOG_PATH = Path("data") / "logs" / "scada_data.csv"

# CSV column header
_FIELDNAMES = [
    "timestamp",
    "unix_time",
    "cycle",
    "well_id",
    "temperature_c",
    "pressure_bar",
    "flow_m3h",
    "pump_state",
    "sensor_healthy",
    "risk_score",
    "health_status",
    "active_faults",
]

# Pump state derivation thresholds (mirrors dashboard logic)
_FLOW_FAULT_THRESHOLD    = 55.0   # m3/h — below this → FAULT
_FLOW_STARTING_THRESHOLD = 80.0   # m3/h — below this → STARTING


def _derive_pump_state(flow: float, healthy: bool) -> str:
    """Return a pump state string based on flow and sensor health."""
    if not healthy or flow < _FLOW_FAULT_THRESHOLD:
        return "FAULT"
    if flow < _FLOW_STARTING_THRESHOLD:
        return "STARTING"
    return "RUNNING"


class SCADALogger:
    """
    Appends SCADA cycle data to a CSV file.

    Parameters
    ----------
    log_path    : Path to the output CSV file.
                  The directory is created if it does not exist.
    flush_every : Flush the file buffer after every N rows written.
                  Lower values reduce data loss on crash; higher values
                  are faster.  Default is 1 (flush every row).
    max_rows    : Optional row limit per file.  When the limit is reached
                  the logger rolls over to a new timestamped file.
                  Set to None (default) for no rollover.
    """

    def __init__(
        self,
        log_path: str | Path = DEFAULT_LOG_PATH,
        flush_every: int = 1,
        max_rows: Optional[int] = None,
    ) -> None:
        self._base_path   = Path(log_path)
        self._flush_every = flush_every
        self._max_rows    = max_rows
        self._rows_written = 0
        self._file_path   = self._resolve_path()
        self._file        = None
        self._writer      = None
        self._open()

    # ── Public API ─────────────────────────────────────────────────────────────

    def log_cycle(
        self,
        cycle:        int,
        readings:     list,
        risk_reports: Optional[dict] = None,
    ) -> None:
        """
        Write one row per well for the current scan cycle.

        Parameters
        ----------
        cycle        : Current scan cycle number.
        readings     : List of ``SensorReading`` objects
                       (from ``simulation.sensors``).
        risk_reports : Optional dict mapping well_id -> ``FaultReport``
                       (from ``analytics.fault_detector``).
                       If None, risk_score and health_status are logged as empty.
        """
        ts       = datetime.now().isoformat(timespec="seconds")
        unix_now = time.time()

        for r in readings:
            rpt          = (risk_reports or {}).get(r.well_id)
            pump_state   = _derive_pump_state(r.flow_m3h, r.is_healthy)
            risk_score   = round(rpt.risk_score, 2) if rpt else ""
            health       = rpt.health.value          if rpt else ""
            faults       = "|".join(rpt.active_faults) if rpt and rpt.active_faults else ""

            row = {
                "timestamp":      ts,
                "unix_time":      round(unix_now, 3),
                "cycle":          cycle,
                "well_id":        r.well_id,
                "temperature_c":  round(r.temperature_c, 3),
                "pressure_bar":   round(r.pressure_bar, 4),
                "flow_m3h":       round(r.flow_m3h,      2),
                "pump_state":     pump_state,
                "sensor_healthy": r.is_healthy,
                "risk_score":     risk_score,
                "health_status":  health,
                "active_faults":  faults,
            }
            self._write_row(row)

        logger.debug("Cycle %d logged: %d well(s).", cycle, len(readings))

    def log_row(self, **kwargs) -> None:
        """
        Write a single arbitrary row.  Any column not in _FIELDNAMES is ignored;
        missing columns are written as empty strings.

        Useful for logging system events or custom metrics.
        """
        row = {k: kwargs.get(k, "") for k in _FIELDNAMES}
        self._write_row(row)

    def flush(self) -> None:
        """Force a flush of the underlying file buffer."""
        if self._file:
            self._file.flush()

    def close(self) -> None:
        """Close the log file gracefully."""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file   = None
            self._writer = None
            logger.info("SCADALogger closed: %s (%d rows written total).",
                        self._file_path, self._rows_written)

    @property
    def file_path(self) -> Path:
        """Absolute path of the current log file."""
        return self._file_path.resolve()

    @property
    def rows_written(self) -> int:
        """Total rows written in this session."""
        return self._rows_written

    # ── Context manager support ────────────────────────────────────────────────

    def __enter__(self) -> "SCADALogger":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _resolve_path(self) -> Path:
        """Return the log file path, inserting a timestamp if rolling over."""
        return self._base_path

    def _open(self) -> None:
        """Open (or create) the CSV file and write the header if needed."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        new_file = not self._file_path.exists()
        # Open in append mode so successive runs accumulate data
        self._file   = open(self._file_path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=_FIELDNAMES)

        if new_file:
            self._writer.writeheader()
            logger.info("SCADALogger: new log file created at %s", self._file_path)
        else:
            logger.info("SCADALogger: appending to existing log at %s", self._file_path)

    def _write_row(self, row: dict) -> None:
        """Write one row, flush if required, and roll over if needed."""
        self._writer.writerow(row)
        self._rows_written += 1

        if self._rows_written % self._flush_every == 0:
            self._file.flush()

        # Optional file rollover
        if self._max_rows and self._rows_written % self._max_rows == 0:
            self._rollover()

    def _rollover(self) -> None:
        """Close current file and open a new timestamped one."""
        self.close()
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = self._base_path.stem
        self._file_path = (
            self._base_path.parent / f"{stem}_{ts}{self._base_path.suffix}"
        )
        self._open()
        logger.info("SCADALogger rolled over to: %s", self._file_path)


# ─── Convenience function ─────────────────────────────────────────────────────

def create_logger(
    path: str | Path = DEFAULT_LOG_PATH,
    flush_every: int = 1,
    max_rows: Optional[int] = None,
) -> SCADALogger:
    """
    Factory shortcut.

    >>> log = create_logger()
    >>> log.log_cycle(1, readings)
    """
    return SCADALogger(log_path=path, flush_every=flush_every, max_rows=max_rows)


# ─── Module self-test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    from simulation.sensors import create_well_array
    from analytics.fault_detector import FaultDetector

    detector = FaultDetector()
    wells    = create_well_array()

    LOG_PATH = Path("data") / "logs" / "scada_data.csv"
    print(f"\n=== SCADALogger Self-Test  -> {LOG_PATH} ===\n")

    with SCADALogger(log_path=LOG_PATH) as scada_log:
        for cycle in range(1, 11):
            readings = [w.read() for w in wells]
            reports  = {r.well_id: detector.evaluate_from_reading(r) for r in readings}
            scada_log.log_cycle(cycle, readings, reports)

            # Echo one row to console
            r0  = readings[0]
            rpt = reports[r0.well_id]
            print(
                f"  Cycle {cycle:02d}  {r0.well_id}"
                f"  T={r0.temperature_c:6.2f}C"
                f"  P={r0.pressure_bar:6.3f}bar"
                f"  Q={r0.flow_m3h:6.1f}m3/h"
                f"  pump={_derive_pump_state(r0.flow_m3h, r0.is_healthy):<8}"
                f"  risk={rpt.risk_score:5.1f}/100"
                f"  [{rpt.health.value}]"
            )

    print(f"\n  Rows written: {scada_log.rows_written}")
    print(f"  Log file    : {scada_log.file_path}\n")

    # Show the CSV header + first few lines
    print("  CSV preview:")
    print("  " + "-" * 80)
    with open(LOG_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f):
            print("  " + line.rstrip())
            if i >= 4:
                print("  ...")
                break
    print("  " + "-" * 80)
