"""
simulation/fault_injector.py
Manual / scripted fault injection for testing alarm & control logic.
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from scada.tag_database import TagDatabase

logger = logging.getLogger(__name__)


@dataclass
class FaultScenario:
    name: str
    description: str
    action: Callable
    duration_s: float = 30.0
    _started_at: Optional[float] = None

    def start(self):
        self._started_at = time.time()
        self.action()
        logger.warning("[FAULT INJECTOR] Scenario '%s' started: %s", self.name, self.description)

    @property
    def is_expired(self) -> bool:
        return (
            self._started_at is not None
            and time.time() - self._started_at > self.duration_s
        )


class FaultInjector:
    """
    Provides named fault scenarios to stress-test the SCADA system.
    Scenarios can be triggered manually via the CLI or test harness.
    """

    def __init__(self, db: TagDatabase):
        self.db = db
        self._active_scenarios: list[FaultScenario] = []
        self._scenarios: dict[str, FaultScenario] = {}
        self._define_scenarios()

    def _define_scenarios(self):
        db = self.db

        scenarios = [
            FaultScenario(
                "well_high_temp",
                "W-01 wellhead temperature exceeds HI_HI limit",
                lambda: db.write("W-01.TEMP", 122.0),
                duration_s=20,
            ),
            FaultScenario(
                "low_pressure",
                "System-wide low pressure event",
                lambda: [db.write(f"W-0{i}.PRES", 1.8) for i in range(1, 4)],
                duration_s=15,
            ),
            FaultScenario(
                "pump_fault",
                "W-02 production pump fault",
                lambda: db.write("W-02.PUMP_ST", "FAULT"),
                duration_s=30,
            ),
            FaultScenario(
                "dh_low_flow",
                "District heating distribution flow drop",
                lambda: db.write("DH.TOTAL_FLOW", 10.0),
                duration_s=25,
            ),
            FaultScenario(
                "hx_efficiency_drop",
                "Heat exchanger efficiency degradation",
                lambda: db.write("HX.EFFICIENCY", 45.0),
                duration_s=40,
            ),
        ]

        for s in scenarios:
            self._scenarios[s.name] = s

    def trigger(self, scenario_name: str) -> bool:
        s = self._scenarios.get(scenario_name)
        if s:
            s.start()
            self._active_scenarios.append(s)
            return True
        logger.error("Unknown fault scenario: %s", scenario_name)
        return False

    def tick(self):
        """Call on every scan cycle to clean up expired scenarios."""
        expired = [s for s in self._active_scenarios if s.is_expired]
        for s in expired:
            logger.info("[FAULT INJECTOR] Scenario '%s' expired.", s.name)
            self._active_scenarios.remove(s)

    @property
    def available_scenarios(self) -> list[str]:
        return list(self._scenarios.keys())
