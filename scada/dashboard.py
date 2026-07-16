"""
scada/dashboard.py
==================
Real-time ANSI terminal dashboard for the Dikili Geothermal SCADA system.

Renders an industrial-style control panel that refreshes every 2 seconds,
displaying per-well temperature, pressure, flow and derived system totals,
with a live alarm log and colour-coded status indicators.

Run directly:
    python -m scada.dashboard

or import and call:
    from scada.dashboard import SCADADashboard
    dash = SCADADashboard()
    dash.run()
"""

from __future__ import annotations

import io
import os
import sys
import time
import signal
import random
import logging
from collections import deque
from datetime import datetime
from typing import Optional

# Force UTF-8 output so box-drawing characters render correctly on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from simulation.sensors import GeothermalSensorArray, SensorReading, create_well_array
from scada.alarm_manager import AlarmManager, AlarmPriority
from scada.incident_engine import incident_engine
from analytics.fault_detector import FaultDetector, SystemHealth
from analytics.ai.operator_assistant import ai_assistant
from data.logger import SCADALogger

logger = logging.getLogger(__name__)

# ─── ANSI Colour helpers ──────────────────────────────────────────────────────

class C:
    """ANSI escape-code constants."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Foreground
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright foreground
    BR_RED     = "\033[91m"
    BR_GREEN   = "\033[92m"
    BR_YELLOW  = "\033[93m"
    BR_BLUE    = "\033[94m"
    BR_CYAN    = "\033[96m"
    BR_WHITE   = "\033[97m"

    # Background
    BG_BLACK  = "\033[40m"
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"
    BG_CYAN   = "\033[46m"

def clr(text: str, *codes: str) -> str:
    return "".join(codes) + text + C.RESET


# ─── Alarm thresholds ─────────────────────────────────────────────────────────
from engineering.profiles.asset_profiles import ProfileRegistry, LegacyThresholds as Thresholds

# ─── Display Helpers ──────────────────────────────────────────────────────────

def _temp_color(v: float) -> str:
    if v <= Thresholds.TEMP_LO_LO or v >= Thresholds.TEMP_HI_HI:
        return C.BR_RED + C.BOLD
    if v <= Thresholds.TEMP_LO or v >= Thresholds.TEMP_HI:
        return C.BR_YELLOW
    return C.BR_GREEN


def _pres_color(v: float) -> str:
    if v <= Thresholds.PRES_LO_LO or v >= Thresholds.PRES_HI_HI:
        return C.BR_RED + C.BOLD
    if v <= Thresholds.PRES_LO or v >= Thresholds.PRES_HI:
        return C.BR_YELLOW
    return C.BR_GREEN


def _flow_color(v: float) -> str:
    if v <= Thresholds.FLOW_LO_LO or v >= Thresholds.FLOW_HI_HI:
        return C.BR_RED + C.BOLD
    if v <= Thresholds.FLOW_LO or v >= Thresholds.FLOW_HI:
        return C.BR_YELLOW
    return C.BR_GREEN


# ─── Bar-graph renderer ───────────────────────────────────────────────────────

def _bar(value: float, lo: float, hi: float, width: int = 12, color: str = C.BR_GREEN) -> str:
    """Render a filled ASCII progress bar scaled to [lo, hi]."""
    fraction = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    filled   = round(fraction * width)
    empty    = width - filled
    bar_body = "\u2588" * filled + "\u2591" * empty
    return f"{color}[{bar_body}]{C.RESET}"


# ─── Pump state simulation ────────────────────────────────────────────────────

PUMP_STATES  = ["RUNNING", "RUNNING", "RUNNING", "STARTING", "FAULT"]
PUMP_HISTORY: dict[str, str] = {}


def _pump_state(well_id: str, flow: float, healthy: bool) -> str:
    """Derive a plausible pump state from sensor health and flow."""
    if not healthy or flow < Thresholds.FLOW_LO_LO:
        state = "FAULT"
    elif flow < Thresholds.FLOW_LO:
        state = "STARTING"
    else:
        # Occasionally inject a transient STARTING state for realism
        prev = PUMP_HISTORY.get(well_id, "RUNNING")
        if prev == "FAULT":
            state = "STARTING"
        elif random.random() < 0.005:
            state = "STARTING"
        else:
            state = "RUNNING"
    PUMP_HISTORY[well_id] = state
    return state


def _pump_color(state: str) -> str:
    return {
        "RUNNING":  C.BR_GREEN,
        "STARTING": C.BR_YELLOW,
        "FAULT":    C.BR_RED + C.BOLD,
        "STOPPED":  C.DIM + C.WHITE,
    }.get(state, C.BR_WHITE)


# ─── Event log entry ──────────────────────────────────────────────────────────

class LogEntry:
    __slots__ = ("ts", "level", "msg")

    def __init__(self, level: str, msg: str):
        self.ts    = datetime.now().strftime("%H:%M:%S")
        self.level = level
        self.msg   = msg

    def render(self) -> str:
        lvl_color = {
            "INFO":  C.DIM + C.WHITE,
            "WARN":  C.BR_YELLOW,
            "ALARM": C.BR_RED + C.BOLD,
            "OK":    C.BR_GREEN,
        }.get(self.level, C.WHITE)
        return (
            f"  {C.DIM}[{self.ts}]{C.RESET} "
            f"{lvl_color}{self.level:<5}{C.RESET}  {self.msg}"
        )


# ─── Dashboard ────────────────────────────────────────────────────────────────

# Box-drawing characters
_TL = "\u2554"; _TR = "\u2557"; _BL = "\u255a"; _BR = "\u255d"
_HH = "\u2550"; _VV = "\u2551"; _TT = "\u2566"; _BB = "\u2569"
_LL = "\u2560"; _RR = "\u2563"; _CC = "\u256c"
_LT = "\u2560"; _RT = "\u2563"


class SCADADashboard:
    """
    Real-time ANSI terminal SCADA panel.

    Parameters
    ----------
    well_ids        : Production well identifiers.
    scan_interval   : Seconds between screen refreshes (default 2.0).
    log_lines       : Number of event log entries to display.
    """

    WIDTH = 80   # total terminal columns used

    def __init__(
        self,
        well_ids: list[str] | None = None,
        scan_interval: float = 2.0,
        log_lines: int = 6,
        log_csv: str | None = "data/logs/scada_data.csv",
    ) -> None:
        if well_ids is None:
            well_ids = ["GW-01", "GW-02", "GW-03"]

        from core.connectivity.simulator_provider import SimulatorDataProvider
        self._provider       = SimulatorDataProvider()
        self._provider.connect()
        self._wells          = self._provider._wells
        
        self._interval       = scan_interval
        self._log_lines      = log_lines
        self._cycle          = 0
        self._running        = False
        self._start_time     = time.time()
        self._event_log: deque[LogEntry] = deque(maxlen=log_lines)
        self._alarms         = AlarmManager()
        self._fault_detector = FaultDetector()
        # Track last fault risk scores per well for pump failure alarm
        self._last_risk: dict[str, float] = {}
        # CSV data logger (None = disabled)
        self._csv_logger: SCADALogger | None = (
            SCADALogger(log_path=log_csv) if log_csv else None
        )

        # Seed the event log
        self._log("INFO", "SCADA system initialised.")
        self._log("INFO", f"Monitoring {len(well_ids)} production wells: {', '.join(well_ids)}")
        self._log("INFO", "Scan interval: {:.1f} s".format(scan_interval))
        if self._csv_logger:
            self._log("INFO", f"Data logging -> {self._csv_logger.file_path}")

    # ── Run loop ───────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the dashboard run loop. Blocks until Ctrl-C or SIGTERM."""
        signal.signal(signal.SIGINT,  self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        self._running = True

        # Enable ANSI on Windows
        if os.name == "nt":
            os.system("chcp 65001 > nul 2>&1")
            os.system("color")   # enables VT sequences in conhost

        self._hide_cursor()
        try:
            while self._running:
                readings = self._provider.read_all()
                self._cycle += 1
                
                # AI Assistant STARTUP Event
                if self._cycle == 1:
                    from scada.event_engine import event_engine, EventType, EventSeverity
                    event_engine.log_event(EventType.STARTUP, "SYSTEM", "SCADA dashboard started", EventSeverity.INFO)
                
                self._evaluate_alarms(readings)
                # Log to CSV — build risk report map for this cycle
                if self._csv_logger:
                    risk_reports = {
                        r.well_id: self._fault_detector.evaluate_from_reading(r)
                        for r in readings
                    }
                    self._csv_logger.log_cycle(self._cycle, readings, risk_reports)
                self._render(readings)
                time.sleep(self._interval)
        finally:
            self._show_cursor()
            if self._csv_logger:
                self._csv_logger.close()
            print()

    def _shutdown(self, *_):
        self._log("INFO", "Shutdown signal received — stopping SCADA.")
        self._running = False

    # ── Alarm evaluation ───────────────────────────────────────────────────────

    def _evaluate_alarms(self, readings: list[SensorReading]) -> None:
        fault_reports_for_ai = {}
        for r in readings:
            wid = r.well_id

            # ══ 1. HIGH TEMPERATURE alarm ════════════════════════════════════
            if r.temperature_c >= Thresholds.TEMP_HI_HI:
                if self._alarms.raise_alarm(
                    f"{wid}.TEMP.HIHI", wid,
                    f"HIGH TEMP  {wid}: {r.temperature_c:.1f} C  (HI-HI limit {Thresholds.TEMP_HI_HI} C)",
                    AlarmPriority.CRITICAL,
                ):
                    self._log("ALARM", f"HIGH TEMP HI-HI  {wid}: {r.temperature_c:.1f} C")
            elif r.temperature_c >= Thresholds.TEMP_HI:
                if self._alarms.raise_alarm(
                    f"{wid}.TEMP.HI", wid,
                    f"HIGH TEMP  {wid}: {r.temperature_c:.1f} C  (HI limit {Thresholds.TEMP_HI} C)",
                    AlarmPriority.HIGH,
                ):
                    self._log("WARN", f"HIGH TEMP  {wid}: {r.temperature_c:.1f} C")
            else:
                self._alarms.clear_alarm(f"{wid}.TEMP.HIHI")
                self._alarms.clear_alarm(f"{wid}.TEMP.HI")

            if r.temperature_c <= Thresholds.TEMP_LO_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.TEMP.LOLO", wid,
                    f"HIGH TEMP (LO-LO)  {wid}: {r.temperature_c:.1f} C  (limit {Thresholds.TEMP_LO_LO} C)",
                    AlarmPriority.CRITICAL,
                ):
                    self._log("ALARM", f"TEMP LO-LO  {wid}: {r.temperature_c:.1f} C")
            elif r.temperature_c <= Thresholds.TEMP_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.TEMP.LO", wid,
                    f"HIGH TEMP (LO)  {wid}: {r.temperature_c:.1f} C  (limit {Thresholds.TEMP_LO} C)",
                    AlarmPriority.MEDIUM,
                ):
                    self._log("WARN", f"TEMP LO  {wid}: {r.temperature_c:.1f} C")
            else:
                self._alarms.clear_alarm(f"{wid}.TEMP.LOLO")
                self._alarms.clear_alarm(f"{wid}.TEMP.LO")

            # ══ 2. LOW PRESSURE alarm ═════════════════════════════════════════
            if r.pressure_bar <= Thresholds.PRES_LO_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.PRES.LOLO", wid,
                    f"LOW PRESSURE  {wid}: {r.pressure_bar:.3f} bar  (LO-LO limit {Thresholds.PRES_LO_LO} bar)",
                    AlarmPriority.CRITICAL,
                ):
                    self._log("ALARM", f"LOW PRES LO-LO  {wid}: {r.pressure_bar:.3f} bar")
            elif r.pressure_bar <= Thresholds.PRES_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.PRES.LO", wid,
                    f"LOW PRESSURE  {wid}: {r.pressure_bar:.3f} bar  (LO limit {Thresholds.PRES_LO} bar)",
                    AlarmPriority.HIGH,
                ):
                    self._log("WARN", f"LOW PRES  {wid}: {r.pressure_bar:.3f} bar")
            else:
                self._alarms.clear_alarm(f"{wid}.PRES.LOLO")
                self._alarms.clear_alarm(f"{wid}.PRES.LO")

            # ══ 3. FLOW FAILURE alarm ════════════════════════════════════════
            if r.flow_m3h <= Thresholds.FLOW_LO_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.FLOW.LOLO", wid,
                    f"FLOW FAILURE  {wid}: {r.flow_m3h:.1f} m3/h  (LO-LO limit {Thresholds.FLOW_LO_LO} m3/h)",
                    AlarmPriority.CRITICAL,
                ):
                    self._log("ALARM", f"FLOW FAIL LO-LO  {wid}: {r.flow_m3h:.1f} m3/h")
            elif r.flow_m3h <= Thresholds.FLOW_LO:
                if self._alarms.raise_alarm(
                    f"{wid}.FLOW.LO", wid,
                    f"FLOW FAILURE  {wid}: {r.flow_m3h:.1f} m3/h  (LO limit {Thresholds.FLOW_LO} m3/h)",
                    AlarmPriority.HIGH,
                ):
                    self._log("WARN", f"FLOW LOW  {wid}: {r.flow_m3h:.1f} m3/h")
            else:
                self._alarms.clear_alarm(f"{wid}.FLOW.LOLO")
                self._alarms.clear_alarm(f"{wid}.FLOW.LO")

            # ══ 4. PUMP FAILURE RISK  (fault-detector risk score) ════════════
            rpt = self._fault_detector.evaluate_from_reading(r)
            self._last_risk[wid] = rpt.risk_score
            fault_reports_for_ai[wid] = rpt

            if rpt.health == SystemHealth.CRITICAL:
                if self._alarms.raise_alarm(
                    f"{wid}.PUMP.RISK.CRIT", wid,
                    f"PUMP FAILURE RISK  {wid}: score={rpt.risk_score:.0f}/100  [{', '.join(rpt.active_faults)}]",
                    AlarmPriority.CRITICAL,
                ):
                    self._log("ALARM", f"PUMP RISK CRITICAL  {wid}: {rpt.risk_score:.0f}/100")
            elif rpt.health == SystemHealth.WARNING:
                if self._alarms.raise_alarm(
                    f"{wid}.PUMP.RISK.WARN", wid,
                    f"PUMP FAILURE RISK  {wid}: score={rpt.risk_score:.0f}/100  [{', '.join(rpt.active_faults)}]",
                    AlarmPriority.MEDIUM,
                ):
                    self._log("WARN", f"PUMP RISK WARNING  {wid}: {rpt.risk_score:.0f}/100")
            else:
                self._alarms.clear_alarm(f"{wid}.PUMP.RISK.CRIT")
                self._alarms.clear_alarm(f"{wid}.PUMP.RISK.WARN")

            # ══ 5. SENSOR FAULT ══════════════════════════════════════════════
            if not r.is_healthy:
                if self._alarms.raise_alarm(
                    f"{wid}.SENSOR.FAULT", wid,
                    f"SENSOR FAULT  {wid}: reading at physical limit",
                    AlarmPriority.HIGH,
                ):
                    self._log("ALARM", f"SENSOR FAULT  {wid}: value at limit")
            else:
                self._alarms.clear_alarm(f"{wid}.SENSOR.FAULT")

        # Evaluate AI Assistant
        ai_assistant.evaluate(readings, fault_reports_for_ai)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self, readings: list[SensorReading]) -> None:
        W   = self.WIDTH
        buf = self._build_screen(readings, W)
        # Move cursor to home, print atomically
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.write("\n".join(buf) + "\n")
        sys.stdout.flush()

    def _build_screen(self, readings: list[SensorReading], W: int) -> list[str]:
        lines: list[str] = []

        now       = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        uptime_s  = int(time.time() - self._start_time)
        uptime    = f"{uptime_s // 3600:02d}:{(uptime_s % 3600)//60:02d}:{uptime_s % 60:02d}"
        n_alarms  = len(self._alarms.active_alarms)
        critical  = self._alarms.critical_active

        sys_state = (
            clr(" ALARM ", C.BG_RED, C.BR_WHITE, C.BOLD)
            if critical else
            clr(" ONLINE ", C.BG_GREEN, C.BLACK, C.BOLD)
            if n_alarms == 0 else
            clr(" WARNING ", C.BG_YELLOW, C.BLACK, C.BOLD)
        )

        # ── Header ─────────────────────────────────────────────────────────
        lines.append(clr(_TL + _HH * (W - 2) + _TR, C.CYAN))
        title = "  DIKILI GEOTHERMAL SCADA  |  DISTRICT HEATING PLANT  "
        lines.append(
            clr(_VV, C.CYAN)
            + clr(title.center(W - 2), C.BR_WHITE, C.BOLD)
            + clr(_VV, C.CYAN)
        )
        loc_line = f"  Location: Dikili, Izmir, Turkey   {now}  "
        lines.append(
            clr(_VV, C.CYAN)
            + clr(loc_line.ljust(W - 2), C.DIM, C.WHITE)
            + clr(_VV, C.CYAN)
        )
        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))

        # Status bar
        alarm_txt = (
            clr(f" {n_alarms} ACTIVE ALARM{'S' if n_alarms != 1 else ''} ", C.BR_RED, C.BOLD)
            if n_alarms else clr(" NO ALARMS ", C.BR_GREEN)
        )
        scan_txt  = clr(f" CYCLE #{self._cycle:05d}  UP {uptime} ", C.DIM, C.WHITE)
        status_bar = f"  STATUS: {sys_state}  |{alarm_txt}|{scan_txt}  INTERVAL: {self._interval:.1f}s"
        lines.append(
            clr(_VV, C.CYAN)
            + status_bar.ljust(W - 2 + _ansi_len(status_bar))
            + clr(_VV, C.CYAN)
        )
        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))

        # ── Well separator header ───────────────────────────────────────────
        col_w = (W - 2) // len(readings)

        well_header = clr(_VV, C.CYAN)
        for r in readings:
            cell = clr(f"  PRODUCTION WELL  {r.well_id}  ", C.BR_CYAN, C.BOLD).center(
                col_w + _ansi_len(clr("", C.BR_CYAN, C.BOLD))
            )
            well_header += cell
        well_header += clr(_VV, C.CYAN)
        lines.append(well_header)
        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))

        # ── Per-well metrics ────────────────────────────────────────────────
        for r in readings:
            pump_st = _pump_state(r.well_id, r.flow_m3h, r.is_healthy)
            PUMP_HISTORY[r.well_id] = pump_st

        # Temperature row
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _metric_cell(
                    "TEMPERATURE",
                    f"{r.temperature_c:6.2f} C",
                    _temp_color(r.temperature_c),
                    col_w,
                )
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )
        # Temperature bar
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _bar_cell(r.temperature_c, 70, 110, col_w, _temp_color(r.temperature_c))
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )

        lines.append(clr(_VV + " " * (W - 2) + _VV, C.CYAN))

        # Pressure row
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _metric_cell(
                    "PRESSURE",
                    f"{r.pressure_bar:5.3f} bar",
                    _pres_color(r.pressure_bar),
                    col_w,
                )
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _bar_cell(r.pressure_bar, 3, 12, col_w, _pres_color(r.pressure_bar))
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )

        lines.append(clr(_VV + " " * (W - 2) + _VV, C.CYAN))

        # Flow row
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _metric_cell(
                    "FLOW RATE",
                    f"{r.flow_m3h:6.1f} m3/h",
                    _flow_color(r.flow_m3h),
                    col_w,
                )
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _bar_cell(r.flow_m3h, 50, 300, col_w, _flow_color(r.flow_m3h))
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )

        lines.append(clr(_VV + " " * (W - 2) + _VV, C.CYAN))

        # Pump status row
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _pump_cell(r.well_id, r.flow_m3h, r.is_healthy, col_w)
                for r in readings
            )
            + clr(_VV, C.CYAN)
        )

        # Sensor status row
        lines.append(
            clr(_VV, C.CYAN)
            + "".join(
                _status_cell(r, col_w) for r in readings
            )
            + clr(_VV, C.CYAN)
        )

        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))

        # ── System totals ───────────────────────────────────────────────────
        total_flow  = sum(r.flow_m3h for r in readings)
        avg_temp    = sum(r.temperature_c for r in readings) / len(readings)
        avg_pres    = sum(r.pressure_bar for r in readings) / len(readings)
        est_power   = total_flow * (avg_temp - 40.0) * 4186 / 3_600_000  # approx kW
        max_risk    = max(self._last_risk.values()) if self._last_risk else 0.0
        risk_color  = C.BR_RED if max_risk >= 70 else C.BR_YELLOW if max_risk >= 40 else C.BR_GREEN

        totals_line = (
            f"  SYSTEM TOTALS"
            f"   {clr('FLOW:', C.DIM, C.WHITE)} {clr(f'{total_flow:7.1f} m3/h', C.BR_CYAN, C.BOLD)}"
            f"   {clr('AVG T:', C.DIM, C.WHITE)} {clr(f'{avg_temp:5.1f} C', C.BR_CYAN, C.BOLD)}"
            f"   {clr('AVG P:', C.DIM, C.WHITE)} {clr(f'{avg_pres:5.3f} bar', C.BR_CYAN, C.BOLD)}"
            f"   {clr('PWR:', C.DIM, C.WHITE)} {clr(f'{est_power:6.0f} kW', C.BR_YELLOW, C.BOLD)}"
            f"   {clr('RISK:', C.DIM, C.WHITE)} {clr(f'{max_risk:5.1f}/100', risk_color, C.BOLD)}"
        )
        lines.append(
            clr(_VV, C.CYAN)
            + totals_line.ljust(W - 2 + _ansi_len(totals_line))
            + clr(_VV, C.CYAN)
        )
        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))

        # ── Alarm panel ─────────────────────────────────────────────────────
        lines += self._build_alarm_panel(W)

        # ── Incident Timeline ───────────────────────────────────────────────
        lines += self._build_incident_panel(W)

        # ── Event log ───────────────────────────────────────────────────────
        log_header = clr("  EVENT LOG ", C.DIM, C.WHITE) + clr(
            f" (last {self._log_lines} entries)", C.DIM
        )
        lines.append(
            clr(_VV, C.CYAN)
            + log_header.ljust(W - 2 + _ansi_len(log_header))
            + clr(_VV, C.CYAN)
        )
        log_entries = list(self._event_log)
        for i in range(self._log_lines):
            entry_str = log_entries[-(i + 1)].render() if i < len(log_entries) else ""
            lines.append(
                clr(_VV, C.CYAN)
                + entry_str.ljust(W - 2 + _ansi_len(entry_str))
                + clr(_VV, C.CYAN)
            )

        lines.append(clr(_BL + _HH * (W - 2) + _BR, C.CYAN))
        lines.append(
            clr(
                "  Press  Ctrl+C  to stop monitoring   |"
                "  Dikili Geothermal SCADA v1.0",
                C.DIM,
            )
        )

        return lines

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _build_alarm_panel(self, W: int) -> list[str]:
        """Render a structured alarm panel showing the four alarm categories."""
        active = self._alarms.active_alarms  # sorted by priority
        n      = len(active)

        # ── Panel header ──────────────────────────────────────────────────
        if n == 0:
            hdr_color = C.BR_GREEN
            hdr_label = "  ALARM PANEL  [ NO ACTIVE ALARMS — ALL SYSTEMS NOMINAL ]"
        elif self._alarms.critical_active:
            hdr_color = C.BR_RED
            hdr_label = f"  ALARM PANEL  [ {n} ACTIVE  |  CRITICAL ALARMS PRESENT ]"
        else:
            hdr_color = C.BR_YELLOW
            hdr_label = f"  ALARM PANEL  [ {n} ACTIVE  |  WARNINGS PRESENT ]"

        lines: list[str] = []
        hdr = clr(hdr_label, hdr_color, C.BOLD)
        lines.append(
            clr(_VV, C.CYAN)
            + hdr.ljust(W - 2 + _ansi_len(hdr))
            + clr(_VV, C.CYAN)
        )

        if n == 0:
            # Show four "all-clear" category badges
            badges = [
                clr(" HIGH TEMP ",  C.BG_GREEN, C.BLACK, C.BOLD),
                clr(" LOW PRES  ",  C.BG_GREEN, C.BLACK, C.BOLD),
                clr(" FLOW FAIL ",  C.BG_GREEN, C.BLACK, C.BOLD),
                clr(" PUMP RISK ",  C.BG_GREEN, C.BLACK, C.BOLD),
            ]
            row = "  " + "   ".join(badges) + "   ALL CLEAR"
            lines.append(
                clr(_VV, C.CYAN)
                + row.ljust(W - 2 + _ansi_len(row))
                + clr(_VV, C.CYAN)
            )
        else:
            # ── Column header ──────────────────────────────────────────────
            col_hdr = (
                clr("  TYPE       ", C.DIM, C.WHITE)
                + clr("WELL   ", C.DIM, C.WHITE)
                + clr("DESCRIPTION                              ", C.DIM, C.WHITE)
                + clr("PRI    ", C.DIM, C.WHITE)
                + clr("AGE   ", C.DIM, C.WHITE)
            )
            lines.append(
                clr(_VV, C.CYAN)
                + col_hdr.ljust(W - 2 + _ansi_len(col_hdr))
                + clr(_VV, C.CYAN)
            )

            # Limit rows to keep display compact
            show = active[:6]
            for alarm in show:
                # Determine alarm type badge from alarm_id
                aid = alarm.alarm_id.upper()
                if ".TEMP." in aid:
                    badge = clr(" HIGH TEMP ", C.BG_RED,    C.BR_WHITE, C.BOLD)
                elif ".PRES." in aid:
                    badge = clr(" LOW PRES  ", C.BG_YELLOW, C.BLACK,    C.BOLD)
                elif ".FLOW." in aid:
                    badge = clr(" FLOW FAIL ", C.BG_YELLOW, C.BLACK,    C.BOLD)
                elif ".PUMP.RISK" in aid:
                    badge = clr(" PUMP RISK ", C.BG_RED,    C.BR_WHITE, C.BOLD)
                else:
                    badge = clr(" SENSOR    ", C.BG_BLUE,   C.BR_WHITE, C.BOLD)

                # Priority colour
                pri_color = {
                    "CRITICAL": C.BR_RED + C.BOLD,
                    "HIGH":     C.BR_YELLOW,
                    "MEDIUM":   C.BR_YELLOW,
                    "LOW":      C.DIM + C.WHITE,
                }.get(alarm.priority.name, C.WHITE)
                pri_badge = clr(f"{alarm.priority.name:<6}", pri_color)

                # Age
                age_s = int(alarm.age_seconds)
                age   = f"{age_s // 60:02d}:{age_s % 60:02d}"

                # Description — truncate to fit
                desc = alarm.description[:38].ljust(38)
                tag  = alarm.tag_id[:6].ljust(6)

                row = (
                    "  " + badge
                    + "  " + clr(tag, C.BR_WHITE)
                    + "  " + clr(desc, C.DIM, C.WHITE)
                    + "  " + pri_badge
                    + "  " + clr(age, C.DIM)
                )
                lines.append(
                    clr(_VV, C.CYAN)
                    + row.ljust(W - 2 + _ansi_len(row))
                    + clr(_VV, C.CYAN)
                )

            if n > 6:
                more = clr(f"  ... and {n - 6} more alarm(s) not shown", C.DIM)
                lines.append(
                    clr(_VV, C.CYAN)
                    + more.ljust(W - 2 + _ansi_len(more))
                    + clr(_VV, C.CYAN)
                )

        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))
        return lines

    def _build_incident_panel(self, W: int) -> list[str]:
        lines: list[str] = []
        incidents = incident_engine.get_active_incidents()
        
        n = len(incidents)
        if n == 0:
            hdr_color = C.BR_GREEN
            hdr_label = "  INCIDENT TIMELINE  [ NO ACTIVE INCIDENTS ]"
        else:
            hdr_color = C.BR_RED if any(i.severity.value in ["FATAL", "CRITICAL"] for i in incidents) else C.BR_YELLOW
            hdr_label = f"  INCIDENT TIMELINE  [ {n} ACTIVE INCIDENTS ]"
            
        hdr = clr(hdr_label, hdr_color, C.BOLD)
        lines.append(
            clr(_VV, C.CYAN)
            + hdr.ljust(W - 2 + _ansi_len(hdr))
            + clr(_VV, C.CYAN)
        )
        
        if n == 0:
            row = "    All systems stable."
            lines.append(
                clr(_VV, C.CYAN)
                + clr(row, C.DIM, C.WHITE).ljust(W - 2 + _ansi_len(clr("", C.DIM, C.WHITE)))
                + clr(_VV, C.CYAN)
            )
        else:
            col_hdr = (
                clr("  ID       ", C.DIM, C.WHITE)
                + clr("EQUIP  ", C.DIM, C.WHITE)
                + clr("SEVERITY   ", C.DIM, C.WHITE)
                + clr("DURATION  ", C.DIM, C.WHITE)
                + clr("LATEST EVENT                 ", C.DIM, C.WHITE)
            )
            lines.append(
                clr(_VV, C.CYAN)
                + col_hdr.ljust(W - 2 + _ansi_len(col_hdr))
                + clr(_VV, C.CYAN)
            )
            
            for inc in incidents[:3]:
                import time
                dur = f"{int(time.time() - inc.start_time)}s"
                latest = inc.timeline[-1].event_type.value if inc.timeline else "NONE"
                latest = latest[:25].ljust(25)
                
                sev_color = C.BR_RED if inc.severity.value in ["FATAL", "CRITICAL"] else C.BR_YELLOW
                row = (
                    f"  {inc.incident_id:<8} "
                    f" {inc.equipment:<6} "
                    + clr(f" {inc.severity.value:<9} ", sev_color)
                    + f" {dur:<9} "
                    f" {latest}"
                )
                lines.append(
                    clr(_VV, C.CYAN)
                    + row.ljust(W - 2 + _ansi_len(row))
                    + clr(_VV, C.CYAN)
                )

        lines.append(clr(_LL + _HH * (W - 2) + _RR, C.CYAN))
        return lines

    def _log(self, level: str, msg: str) -> None:
        self._event_log.append(LogEntry(level, msg))

    @staticmethod
    def _hide_cursor() -> None:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def _show_cursor() -> None:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


# ─── Cell-rendering helpers ───────────────────────────────────────────────────

def _ansi_len(s: str) -> int:
    """Estimate extra bytes introduced by ANSI codes (used for padding math)."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s)) - len(s.replace("\033", ""))


def _pad(text: str, width: int) -> str:
    """Left-pad *text* to *width* visible characters (ignoring ANSI codes)."""
    import re
    visible = len(re.sub(r"\033\[[0-9;]*m", "", text))
    return text + " " * max(0, width - visible)


def _metric_cell(label: str, value: str, color: str, col_w: int) -> str:
    label_part = clr(f"  {label:<12}", C.DIM, C.WHITE)
    value_part = clr(value, color, C.BOLD)
    cell = label_part + value_part
    return _pad(cell, col_w)


def _bar_cell(value: float, lo: float, hi: float, col_w: int, color: str) -> str:
    bar = _bar(value, lo, hi, width=col_w - 6, color=color)
    cell = "  " + bar
    return _pad(cell, col_w)


def _pump_cell(well_id: str, flow: float, healthy: bool, col_w: int) -> str:
    state = _pump_state(well_id, flow, healthy)
    label = clr("  PUMP       ", C.DIM, C.WHITE)
    value = clr(f"{state:<8}", _pump_color(state), C.BOLD)
    cell  = label + value
    return _pad(cell, col_w)


def _status_cell(r: SensorReading, col_w: int) -> str:
    label = clr("  SENSOR     ", C.DIM, C.WHITE)
    if r.is_healthy:
        value = clr("[ NOMINAL ]", C.BR_GREEN, C.BOLD)
    else:
        value = clr("[ FAULT   ]", C.BR_RED, C.BOLD)
    cell = label + value
    return _pad(cell, col_w)


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    dash = SCADADashboard(
        well_ids      = ["GW-01", "GW-02", "GW-03"],
        scan_interval = 2.0,
        log_lines     = 8,
    )
    dash.run()
