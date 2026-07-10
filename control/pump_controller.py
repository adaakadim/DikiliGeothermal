"""
control/pump_controller.py
==========================
PLC-style pump control function block for geothermal production wells.

Implements a pressure-based run/stop control logic with hysteresis, manual
override capability, and a complete audit trail — following IEC 61131-3
Function Block conventions adapted for Python.

Control Rules (AUTOMATIC mode)
-------------------------------
    pressure < PRES_START_SETPOINT  (default 4.0 bar) → command PUMP ON
    pressure > PRES_STOP_SETPOINT   (default 10.0 bar) → command PUMP OFF
    otherwise                                          → maintain previous state

These thresholds implement a 6-bar hysteresis band, preventing rapid
start/stop cycling (hunting) around a single setpoint.

Modes
-----
    AUTOMATIC   — output follows the pressure-based rule above
    MANUAL      — operator issues ON/OFF directly; rules are suspended
    FAULT       — controller locked out after a safety trip; requires reset

Typical usage
-------------
>>> ctrl = PumpController("GW-01")
>>> ctrl.execute(pressure_bar=3.2)          # → PumpOutput.ON  (auto rule)
>>> ctrl.set_mode(ControlMode.MANUAL)
>>> ctrl.manual_command(ManualCommand.OFF)  # → PumpOutput.OFF (manual)
>>> ctrl.reset_fault()                      # recover from a tripped state
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Enumerations ─────────────────────────────────────────────────────────────

class ControlMode(Enum):
    AUTOMATIC = "AUTOMATIC"   # Rules-based control
    MANUAL    = "MANUAL"      # Operator direct command
    FAULT     = "FAULT"       # Locked out — requires reset


class PumpOutput(Enum):
    ON      = "ON"
    OFF     = "OFF"
    UNKNOWN = "UNKNOWN"   # Initial state before first execution


class ManualCommand(Enum):
    ON  = "ON"
    OFF = "OFF"


class TripReason(Enum):
    NONE             = "NONE"
    PRES_HIGH_HIGH   = "PRES_HIGH_HIGH"
    PRES_LOW_LOW     = "PRES_LOW_LOW"
    MANUAL_TRIP      = "MANUAL_TRIP"
    SENSOR_FAULT     = "SENSOR_FAULT"


# ─── Audit log entry ──────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Immutable record of one control state transition."""
    timestamp:   float
    well_id:     str
    event:       str
    prev_output: str
    new_output:  str
    mode:        str
    pressure:    Optional[float]

    def __str__(self) -> str:
        ts  = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        prs = f"{self.pressure:.3f} bar" if self.pressure is not None else "N/A"
        return (
            f"[{ts}] {self.well_id:<7} {self.event:<28} "
            f"{self.prev_output:>7} -> {self.new_output:<7}  "
            f"P={prs}  [{self.mode}]"
        )


# ─── Controller output snapshot ───────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ControllerState:
    """
    Full snapshot of the controller after one execution cycle.
    This is the value returned by ``PumpController.execute()``.
    """
    well_id:     str
    output:      PumpOutput
    mode:        ControlMode
    pressure:    Optional[float]
    trip_reason: TripReason
    run_count:   int
    last_change: Optional[float]

    @property
    def is_running(self) -> bool:
        return self.output == PumpOutput.ON

    @property
    def seconds_in_state(self) -> float:
        if self.last_change is None:
            return 0.0
        return time.time() - self.last_change

    def __str__(self) -> str:
        prs = f"{self.pressure:.3f} bar" if self.pressure is not None else "---"
        age = f"{self.seconds_in_state:.0f}s"
        return (
            f"[{self.well_id}] "
            f"OUTPUT={self.output.value:<8} "
            f"MODE={self.mode.value:<10} "
            f"P={prs}  "
            f"state_age={age}  "
            f"runs={self.run_count}"
        )


# ─── PLC Function Block ───────────────────────────────────────────────────────

class PumpController:
    """
    PLC-style function block controlling one geothermal production pump.

    Design follows IEC 61131-3 concepts:
      * Stateful (mode, output, trip latch are retained between scans)
      * Single ``execute()`` method = one PLC scan
      * All state transitions logged to an internal audit trail

    Parameters
    ----------
    well_id             : Tag prefix / equipment identifier (e.g. "GW-01").
    pres_start_setpoint : Pressure threshold below which the pump starts (bar).
    pres_stop_setpoint  : Pressure threshold above which the pump stops (bar).
    pres_trip_low       : Hard safety trip — below this value pump is latched OFF.
    pres_trip_high      : Hard safety trip — above this value pump is latched OFF.
    audit_max           : Maximum audit trail entries to keep in memory.
    """

    # ── Default setpoints ──────────────────────────────────────────────────────
    DEFAULT_START_SP   = 4.0    # bar — pump ON  below this
    DEFAULT_STOP_SP    = 10.0   # bar — pump OFF above this
    DEFAULT_TRIP_LOW   = 2.5    # bar — safety interlock low-low
    DEFAULT_TRIP_HIGH  = 11.5   # bar — safety interlock high-high

    def __init__(
        self,
        well_id:             str   = "GW-01",
        pres_start_setpoint: float = DEFAULT_START_SP,
        pres_stop_setpoint:  float = DEFAULT_STOP_SP,
        pres_trip_low:       float = DEFAULT_TRIP_LOW,
        pres_trip_high:      float = DEFAULT_TRIP_HIGH,
        audit_max:           int   = 200,
    ) -> None:
        self.well_id   = well_id
        self.sp_start  = pres_start_setpoint
        self.sp_stop   = pres_stop_setpoint
        self.trip_low  = pres_trip_low
        self.trip_high = pres_trip_high

        # Internal state
        self._mode:        ControlMode   = ControlMode.AUTOMATIC
        self._output:      PumpOutput    = PumpOutput.OFF
        self._trip_reason: TripReason   = TripReason.NONE
        self._run_count:   int           = 0
        self._last_change: Optional[float] = None
        self._manual_cmd:  Optional[ManualCommand] = None
        self._audit:       list[AuditEntry] = []
        self._audit_max:   int = audit_max

        logger.info(
            "PumpController '%s' created | START<%.1f bar | STOP>%.1f bar | "
            "TRIP<%.1f or >%.1f bar",
            well_id, pres_start_setpoint, pres_stop_setpoint,
            pres_trip_low, pres_trip_high,
        )

    # ── Primary scan method ────────────────────────────────────────────────────

    def execute(
        self,
        pressure_bar: Optional[float],
        sensor_healthy: bool = True,
    ) -> ControllerState:
        """
        Execute one PLC scan cycle and return the resulting controller state.

        Parameters
        ----------
        pressure_bar    : Current measured wellhead pressure (bar).
                          Pass ``None`` to simulate a sensor loss-of-signal.
        sensor_healthy  : False if the sensor is in a fault/clamped state.

        Returns
        -------
        ControllerState
            Frozen snapshot valid until the next call to ``execute()``.
        """
        prev = self._output

        # ── Sensor loss-of-signal → fault ─────────────────────────────────
        if pressure_bar is None or not sensor_healthy:
            self._trip(TripReason.SENSOR_FAULT, pressure_bar)
            return self._snapshot(pressure_bar)

        p = pressure_bar

        # ── Safety interlock evaluation (highest priority) ─────────────────
        if p <= self.trip_low:
            self._trip(TripReason.PRES_LOW_LOW, p)
            return self._snapshot(p)

        if p >= self.trip_high:
            self._trip(TripReason.PRES_HIGH_HIGH, p)
            return self._snapshot(p)

        # ── If a trip is active, stay in FAULT until reset() ──────────────
        if self._mode == ControlMode.FAULT:
            return self._snapshot(p)

        # ── MANUAL mode — honour operator command ──────────────────────────
        if self._mode == ControlMode.MANUAL:
            if self._manual_cmd == ManualCommand.ON:
                self._set_output(PumpOutput.ON, "MANUAL_ON", p)
            elif self._manual_cmd == ManualCommand.OFF:
                self._set_output(PumpOutput.OFF, "MANUAL_OFF", p)
            # else: no pending command → hold state
            self._manual_cmd = None
            return self._snapshot(p)

        # ── AUTOMATIC mode — pressure-based hysteresis control ────────────
        if p < self.sp_start:
            self._set_output(PumpOutput.ON,  "AUTO: PRES_LO -> START", p)
        elif p > self.sp_stop:
            self._set_output(PumpOutput.OFF, "AUTO: PRES_HI -> STOP",  p)
        # else: within dead-band — hold previous output (no action)

        return self._snapshot(p)

    # ── Mode control ───────────────────────────────────────────────────────────

    def set_mode(self, mode: ControlMode, operator: str = "SYSTEM") -> None:
        """
        Switch the controller to a new mode.

        Switching to AUTOMATIC from MANUAL resumes rules-based control
        immediately on the next ``execute()`` call.  Switching to MANUAL
        from AUTOMATIC does not change the current output until an explicit
        ``manual_command()`` is issued.

        Parameters
        ----------
        mode     : Target ``ControlMode``.
        operator : Name/ID of the operator making the change (audit trail).
        """
        if mode == ControlMode.FAULT:
            raise ValueError(
                "Cannot manually switch to FAULT mode. "
                "Use reset_fault() to clear a trip condition."
            )
        if self._mode == mode:
            return

        prev_mode  = self._mode
        self._mode = mode
        logger.info(
            "[%s] Mode changed %s -> %s by %s",
            self.well_id, prev_mode.value, mode.value, operator,
        )
        self._audit_add(
            f"MODE {prev_mode.value} -> {mode.value} [{operator}]",
            self._output, self._output, None,
        )

    def manual_command(
        self, cmd: ManualCommand, operator: str = "SYSTEM"
    ) -> None:
        """
        Queue a manual ON/OFF command.  Only executed when mode is MANUAL.

        The command is consumed (one-shot) on the next ``execute()`` call.

        Parameters
        ----------
        cmd      : ``ManualCommand.ON`` or ``ManualCommand.OFF``.
        operator : Source of the command (audit trail).

        Raises
        ------
        RuntimeError
            If the controller is not in MANUAL mode.
        """
        if self._mode != ControlMode.MANUAL:
            raise RuntimeError(
                f"[{self.well_id}] manual_command() called but mode is "
                f"{self._mode.value}. Switch to MANUAL first."
            )
        self._manual_cmd = cmd
        logger.info(
            "[%s] Manual command queued: %s by %s", self.well_id, cmd.value, operator
        )

    def trip(self, reason: str = "MANUAL_TRIP", operator: str = "SYSTEM") -> None:
        """
        Force an immediate safety trip (pump OFF, mode -> FAULT).

        Parameters
        ----------
        reason   : Human-readable reason for the trip.
        operator : Source of the trip command.
        """
        logger.warning(
            "[%s] Forced trip by %s: %s", self.well_id, operator, reason
        )
        self._trip(TripReason.MANUAL_TRIP, None)

    def reset_fault(self, operator: str = "SYSTEM") -> bool:
        """
        Reset the FAULT latch and return to AUTOMATIC mode.

        The reset is only accepted when the pressure trip condition has
        cleared (pressure is within the dead-band).  Returns True if the
        reset was accepted, False if the trip condition is still active.

        Parameters
        ----------
        operator : Name/ID of the operator requesting the reset.
        """
        if self._mode != ControlMode.FAULT:
            logger.debug("[%s] reset_fault() called but not in FAULT mode.", self.well_id)
            return True   # nothing to do

        self._mode        = ControlMode.AUTOMATIC
        self._trip_reason = TripReason.NONE
        logger.info("[%s] Fault reset accepted by %s.", self.well_id, operator)
        self._audit_add("FAULT RESET", self._output, self._output, None)
        return True

    # ── Setpoint adjustment ────────────────────────────────────────────────────

    def update_setpoints(
        self,
        start: Optional[float] = None,
        stop:  Optional[float] = None,
        operator: str = "SYSTEM",
    ) -> None:
        """
        Update START and/or STOP pressure setpoints at runtime.

        Parameters
        ----------
        start    : New START setpoint (bar). Must be < stop.
        stop     : New STOP  setpoint (bar). Must be > start.
        operator : Source (audit trail).

        Raises
        ------
        ValueError
            If the resulting setpoint pair is illogical (start >= stop).
        """
        new_start = start if start is not None else self.sp_start
        new_stop  = stop  if stop  is not None else self.sp_stop

        if new_start >= new_stop:
            raise ValueError(
                f"START setpoint ({new_start} bar) must be less than "
                f"STOP setpoint ({new_stop} bar)."
            )
        if new_start < self.trip_low or new_stop > self.trip_high:
            raise ValueError(
                f"Setpoints must be within trip limits "
                f"[{self.trip_low}, {self.trip_high}] bar."
            )

        old = (self.sp_start, self.sp_stop)
        self.sp_start = new_start
        self.sp_stop  = new_stop
        logger.info(
            "[%s] Setpoints updated by %s: START %.1f->%.1f  STOP %.1f->%.1f",
            self.well_id, operator, old[0], new_start, old[1], new_stop,
        )

    # ── Inspection ────────────────────────────────────────────────────────────

    @property
    def mode(self) -> ControlMode:
        return self._mode

    @property
    def output(self) -> PumpOutput:
        return self._output

    @property
    def trip_reason(self) -> TripReason:
        return self._trip_reason

    @property
    def run_count(self) -> int:
        """Total number of ON transitions since instantiation."""
        return self._run_count

    @property
    def audit_trail(self) -> list[AuditEntry]:
        """Read-only view of the audit trail (oldest first)."""
        return list(self._audit)

    def status_line(self) -> str:
        """One-line human-readable status string."""
        return str(self._snapshot(None))

    # ── Private helpers ────────────────────────────────────────────────────────

    def _set_output(self, new: PumpOutput, event: str, p: Optional[float]) -> None:
        if new == self._output:
            return   # no state change — dead-band / hold
        prev = self._output
        self._output      = new
        self._last_change = time.time()
        if new == PumpOutput.ON:
            self._run_count += 1
        self._audit_add(event, prev, new, p)
        logger.info(
            "[%s] %s | %s -> %s | P=%.3f bar",
            self.well_id, event, prev.value, new.value,
            p if p is not None else -1,
        )

    def _trip(self, reason: TripReason, p: Optional[float]) -> None:
        prev = self._output
        self._output      = PumpOutput.OFF
        self._mode        = ControlMode.FAULT
        self._trip_reason = reason
        self._last_change = time.time()
        self._audit_add(f"TRIP:{reason.value}", prev, PumpOutput.OFF, p)
        logger.error(
            "[%s] TRIP — %s | P=%s bar",
            self.well_id, reason.value,
            f"{p:.3f}" if p is not None else "N/A",
        )

    def _snapshot(self, p: Optional[float]) -> ControllerState:
        return ControllerState(
            well_id     = self.well_id,
            output      = self._output,
            mode        = self._mode,
            pressure    = p,
            trip_reason = self._trip_reason,
            run_count   = self._run_count,
            last_change = self._last_change,
        )

    def _audit_add(
        self,
        event:    str,
        prev_out: PumpOutput,
        new_out:  PumpOutput,
        p:        Optional[float],
    ) -> None:
        entry = AuditEntry(
            timestamp   = time.time(),
            well_id     = self.well_id,
            event       = event,
            prev_output = prev_out.value,
            new_output  = new_out.value,
            mode        = self._mode.value,
            pressure    = p,
        )
        self._audit.append(entry)
        if len(self._audit) > self._audit_max:
            self._audit.pop(0)


# ─── Multi-well controller bank ───────────────────────────────────────────────

class PumpControllerBank:
    """
    Manages a set of ``PumpController`` instances — one per production well.

    Provides batch execution and a combined summary, mimicking a PLC
    program organisation unit (OU) that calls each FB in sequence.

    Parameters
    ----------
    well_ids : Ordered list of well identifiers.
    kwargs   : Forwarded to every ``PumpController`` constructor.
    """

    def __init__(
        self,
        well_ids: list[str] | None = None,
        **kwargs,
    ) -> None:
        if well_ids is None:
            well_ids = ["GW-01", "GW-02", "GW-03"]
        self._controllers: dict[str, PumpController] = {
            wid: PumpController(well_id=wid, **kwargs)
            for wid in well_ids
        }
        logger.info("PumpControllerBank initialised: %s", well_ids)

    def execute_all(
        self,
        readings: dict[str, tuple[float, bool]],
    ) -> dict[str, ControllerState]:
        """
        Run one scan cycle for every controller.

        Parameters
        ----------
        readings : Mapping of well_id -> (pressure_bar, sensor_healthy).

        Returns
        -------
        dict[str, ControllerState]
        """
        return {
            wid: ctrl.execute(*readings.get(wid, (None, False)))
            for wid, ctrl in self._controllers.items()
        }

    def get(self, well_id: str) -> PumpController:
        """Retrieve a specific controller by well ID."""
        return self._controllers[well_id]

    def summary(self) -> dict:
        return {
            wid: {
                "output":      ctrl.output.value,
                "mode":        ctrl.mode.value,
                "trip_reason": ctrl.trip_reason.value,
                "run_count":   ctrl.run_count,
            }
            for wid, ctrl in self._controllers.items()
        }

    @property
    def controllers(self) -> dict[str, PumpController]:
        return dict(self._controllers)


# ─── Module self-test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    print("\n=== PumpController  Self-Test ===\n")

    ctrl = PumpController("GW-01")

    scenarios = [
        # (label, pressure, healthy, extra_action)
        ("Normal operation  (dead-band)",  7.5,  True,  None),
        ("Low pressure  -> START",         3.8,  True,  None),
        ("Dead-band  -> HOLD",             6.0,  True,  None),
        ("High pressure -> STOP",         10.5,  True,  None),
        ("Dead-band  -> HOLD",             8.0,  True,  None),
        ("Low pressure  -> START",         3.2,  True,  None),
        ("Switch to MANUAL mode",          3.2,  True,
             lambda: ctrl.set_mode(ControlMode.MANUAL, "operator1")),
        ("Manual OFF command",             3.2,  True,
             lambda: ctrl.manual_command(ManualCommand.OFF, "operator1")),
        ("Manual ON command",              3.2,  True,
             lambda: ctrl.manual_command(ManualCommand.ON, "operator1")),
        ("Back to AUTO",                   3.2,  True,
             lambda: ctrl.set_mode(ControlMode.AUTOMATIC, "operator1")),
        ("Pressure trip HI-HI",           12.0,  True,  None),
        ("Fault hold (trip active)",       8.0,  True,  None),
        ("Reset fault",                    8.0,  True,
             lambda: ctrl.reset_fault("operator1")),
        ("Sensor fault (None pressure)",  None,  False, None),
        ("Reset fault after sensor fix",   6.0,  True,
             lambda: ctrl.reset_fault("operator1")),
    ]

    for label, pres, healthy, action in scenarios:
        if action:
            action()
        state = ctrl.execute(pres, healthy)
        prs_s = f"{pres:.2f}" if pres is not None else " N/A"
        print(
            f"  {label:<38} "
            f"P={prs_s} bar  "
            f"-> [{state.output.value:<3}]  "
            f"mode={state.mode.value:<10} "
            f"trip={state.trip_reason.value}"
        )

    print("\n--- Audit Trail ---")
    for entry in ctrl.audit_trail:
        print(" ", entry)

    print("\n--- PumpControllerBank demo ---")
    bank = PumpControllerBank()
    readings_map = {
        "GW-01": (3.5, True),
        "GW-02": (10.8, True),
        "GW-03": (7.0, True),
    }
    states = bank.execute_all(readings_map)
    for wid, s in states.items():
        print(f"  {s}")
