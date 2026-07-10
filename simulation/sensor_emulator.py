"""
simulation/sensor_emulator.py
Sensor noise and failure mode emulation.
Provides realistic analog sensor behaviour: drift, offset, stuck value, freeze.
"""

import random
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class SensorFaultMode(Enum):
    NONE      = "NONE"
    STUCK     = "STUCK"       # sensor frozen at last good value
    DRIFT     = "DRIFT"       # slow systematic offset accumulation
    SPIKE     = "SPIKE"       # single out-of-range spike
    NOISE     = "NOISE"       # excessive noise / oscillation
    OPEN_CKT  = "OPEN_CKT"   # sensor reads min/max rail (broken wire)


@dataclass
class SensorEmulator:
    """
    Wraps a raw process value and adds realistic sensor imperfections.

    Parameters
    ----------
    tag_id          : Tag ID in the database
    accuracy_pct    : Full-scale accuracy (%)
    full_scale      : Full-scale range for accuracy calculation
    fault_prob      : Probability of a fault event per step (0..1)
    """

    tag_id: str
    accuracy_pct: float = 0.25         # 0.25 % FS typical RTD
    full_scale: float = 150.0
    fault_prob: float = 0.002          # 0.2 % per step

    _fault_mode: SensorFaultMode = field(default=SensorFaultMode.NONE, init=False)
    _stuck_value: Optional[float] = field(default=None, init=False)
    _drift_offset: float = field(default=0.0, init=False)
    _fault_start: Optional[float] = field(default=None, init=False)

    @property
    def noise_sigma(self) -> float:
        return self.accuracy_pct / 100.0 * self.full_scale

    def process(self, true_value: float) -> tuple[float, bool]:
        """
        Apply sensor characteristics to a true process value.

        Returns
        -------
        (measured_value, is_healthy)
        """
        # Random fault injection
        if self._fault_mode == SensorFaultMode.NONE and random.random() < self.fault_prob:
            self._fault_mode = random.choice(list(SensorFaultMode)[1:])
            self._fault_start = time.time()
            logger.debug("Sensor %s entering fault mode: %s", self.tag_id, self._fault_mode.value)

        # Auto-recovery after 30–120 s
        if self._fault_mode != SensorFaultMode.NONE and self._fault_start:
            if time.time() - self._fault_start > random.uniform(30, 120):
                self._recover()

        match self._fault_mode:
            case SensorFaultMode.NONE:
                measured = true_value + random.gauss(0, self.noise_sigma)
                return round(measured, 3), True

            case SensorFaultMode.STUCK:
                if self._stuck_value is None:
                    self._stuck_value = true_value
                return round(self._stuck_value, 3), False

            case SensorFaultMode.DRIFT:
                self._drift_offset += random.uniform(0.01, 0.05)
                measured = true_value + self._drift_offset + random.gauss(0, self.noise_sigma)
                return round(measured, 3), False

            case SensorFaultMode.SPIKE:
                spike = true_value + random.uniform(-50, 50)
                self._recover()   # spike is a one-shot event
                return round(spike, 3), False

            case SensorFaultMode.NOISE:
                measured = true_value + random.gauss(0, self.noise_sigma * 10)
                return round(measured, 3), False

            case SensorFaultMode.OPEN_CKT:
                return 0.0 if random.random() > 0.5 else self.full_scale, False

            case _:
                return true_value, True

    def _recover(self):
        self._fault_mode = SensorFaultMode.NONE
        self._stuck_value = None
        self._drift_offset = 0.0
        self._fault_start = None
        logger.debug("Sensor %s recovered.", self.tag_id)