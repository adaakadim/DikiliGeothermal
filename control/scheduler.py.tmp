"""
control/scheduler.py
Control action scheduler — runs PID loops, interlock checks, and
periodic control tasks at configurable intervals.
"""

import threading
import time
import logging
from typing import Optional

from .pid_controller import PIDController
from .interlock import InterlockMatrix

logger = logging.getLogger(__name__)


class ControlScheduler:
    """
    Runs control tasks in a background thread at fixed intervals.
    Implements the pump speed and zone valve PID loops.
    """

    def __init__(self, scada):
        self.scada  = scada
        self.config = scada.config
        self.db     = scada.db

        # ── PID Controllers ───────────────────────────────────────────────────
        self.pump_pids: dict[str, PIDController] = {}
        for well in self.config.wells:
            self.pump_pids[well.well_id] = PIDController(
                name=f"{well.well_id}_PUMP_SPEED",
                kp=2.0, ki=0.15, kd=0.05,
                setpoint=well.max_flow_m3h * 0.70,
                out_min=10.0, out_max=100.0,
                sample_time_s=self.config.scan_interval,
            )

        self.supply_temp_pid = PIDController(
            name="DH_SUPPLY_TEMP",
            kp=3.0, ki=0.2, kd=0.08,
            setpoint=self.config.target_supply_temp_c,
            out_min=0.0, out_max=100.0,
            sample_time_s=self.config.scan_interval,
        )

        # ── Interlock Matrix ──────────────────────────────────────────────────
        self.interlocks = InterlockMatrix(self.db, self.config)

        # ── Thread ────────────────────────────────────────────────────────────
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ControlScheduler",
            daemon=True,
        )
        self._thread.start()
        logger.info("ControlScheduler started.")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ControlScheduler stopped.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self._control_cycle()
            except Exception as exc:
                logger.error("Control cycle error: %s", exc, exc_info=True)
            time.sleep(self.config.scan_interval)

    def _control_cycle(self):
        # 1. Evaluate safety interlocks (highest priority)
        tripped = self.interlocks.evaluate_all()
        if tripped:
            logger.warning("Interlocks tripped: %s", tripped)

        # 2. Pump speed PID loops
        for well in self.config.wells:
            wid = well.well_id
            actual_flow = self.db.read_value(f"{wid}.FLOW", 0.0)
            pump_sp     = self.pump_pids[wid].compute(actual_flow)
            self.db.write(f"{wid}.PUMP_SP", round(pump_sp, 1))

        # 3. Supply temperature PID → modulates total flow via virtual output
        sec_supply = self.db.read_value("HX.SEC_SUPPLY", 0.0)
        temp_out   = self.supply_temp_pid.compute(sec_supply)
        # (In real plant this would drive a control valve or pump VFD setpoint)
        # Here we log it as a diagnostic tag
        self.db.write("DH.SUPPLY_PRES",
                      round(self.db.read_value("DH.SUPPLY_PRES", 4.5), 2))
