"""
control/interlock.py
Safety interlock matrix — hard-coded process safety constraints.
Interlocks trigger automated shutdowns / actions when limits are violated.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from scada.tag_database import TagDatabase

logger = logging.getLogger(__name__)


class InterlockAction(Enum):
    TRIP_PUMP  = "TRIP_PUMP"         # Shut down production pump
    CLOSE_VALVE = "CLOSE_VALVE"      # Close isolation / control valve
    REDUCE_FLOW = "REDUCE_FLOW"      # Ramp down flow setpoint
    ALARM_ONLY  = "ALARM_ONLY"       # No hardware action, alarm only


@dataclass
class Interlock:
    interlock_id: str
    description: str
    tag_id: str
    condition: Callable[[float], bool]   # Returns True when interlock should trip
    action: InterlockAction
    callback: Optional[Callable] = None  # Optional action to execute
    _tripped: bool = field(default=False, init=False)

    def evaluate(self, value: float) -> bool:
        """Returns True if the interlock just tripped."""
        should_trip = self.condition(value)
        if should_trip and not self._tripped:
            self._tripped = True
            logger.critical(
                "[INTERLOCK TRIP] %s — %s → %s",
                self.interlock_id, self.description, self.action.value,
            )
            if self.callback:
                self.callback()
            return True
        elif not should_trip and self._tripped:
            self._tripped = False
            logger.info("[INTERLOCK RESET] %s", self.interlock_id)
        return False

    @property
    def is_tripped(self) -> bool:
        return self._tripped


class InterlockMatrix:
    """
    Manages all safety interlocks for the Dikili plant.
    Called on every SCADA tick before output updates.
    """

    def __init__(self, db: TagDatabase, config):
        self.db = db
        self.config = config
        self._interlocks: list[Interlock] = []
        self._define_interlocks()

    def _define_interlocks(self):
        cfg = self.config

        # ── Well temperature high-high trips ──────────────────────────────────
        for well in cfg.wells:
            wid = well.well_id
            hi_hi = cfg.max_wellhead_temp_c + 5

            def make_temp_il(w, limit):
                return Interlock(
                    f"IL_{w}_TEMP_HIHI",
                    f"{w} wellhead temp exceeds {limit}°C",
                    f"{w}.TEMP",
                    condition=lambda v, lim=limit: v >= lim,
                    action=InterlockAction.TRIP_PUMP,
                    callback=lambda w=w: self.db.write(f"{w}.PUMP_ST", "TRIPPED"),
                )

            self._interlocks.append(make_temp_il(wid, hi_hi))

        # ── Pressure low-low trips ─────────────────────────────────────────────
        for well in cfg.wells:
            wid = well.well_id
            lo_lo = cfg.min_system_pressure_bar - 0.5

            def make_pres_il(w, limit):
                return Interlock(
                    f"IL_{w}_PRES_LOLO",
                    f"{w} wellhead pressure below {limit} bar",
                    f"{w}.PRES",
                    condition=lambda v, lim=limit: v <= lim,
                    action=InterlockAction.TRIP_PUMP,
                    callback=lambda w=w: self.db.write(f"{w}.PUMP_ST", "TRIPPED"),
                )

            self._interlocks.append(make_pres_il(wid, lo_lo))

        # ── DH network pressure protection ───────────────────────────────────
        self._interlocks.append(Interlock(
            "IL_DH_PRES_HIHI",
            "DH supply pressure exceeds 10 bar",
            "DH.SUPPLY_PRES",
            condition=lambda v: v >= 10.0,
            action=InterlockAction.CLOSE_VALVE,
        ))

        # ── HX secondary supply over-temperature ─────────────────────────────
        self._interlocks.append(Interlock(
            "IL_HX_SUPPLY_HIHI",
            "HX secondary supply temperature exceeds 95°C",
            "HX.SEC_SUPPLY",
            condition=lambda v: v >= 95.0,
            action=InterlockAction.REDUCE_FLOW,
        ))

    def evaluate_all(self) -> list[str]:
        """Evaluate all interlocks; return list of tripped interlock IDs."""
        tripped = []
        for il in self._interlocks:
            tag = self.db.read(il.tag_id)
            if tag and tag.value is not None:
                if il.evaluate(float(tag.value)):
                    tripped.append(il.interlock_id)
        return tripped

    @property
    def tripped_interlocks(self) -> list[Interlock]:
        return [il for il in self._interlocks if il.is_tripped]

    def summary(self) -> dict:
        return {
            "total": len(self._interlocks),
            "tripped": len(self.tripped_interlocks),
            "details": [
                {"id": il.interlock_id, "desc": il.description, "tripped": il.is_tripped}
                for il in self._interlocks
            ],
        }
