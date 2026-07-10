"""
control/pid_controller.py
Generic discrete PID controller with anti-windup and output clamping.
Used for pump speed, valve position, and temperature regulation loops.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PIDController:
    """
    Incremental (velocity-form) PID controller.

    Parameters
    ----------
    name        : Descriptive name for logging
    kp, ki, kd  : Proportional, integral, derivative gains
    setpoint    : Desired process value
    out_min     : Minimum output (default 0.0)
    out_max     : Maximum output (default 100.0)
    deadband    : No-action zone around setpoint (±)
    """

    name: str
    kp: float = 1.0
    ki: float = 0.1
    kd: float = 0.05
    setpoint: float = 0.0
    out_min: float = 0.0
    out_max: float = 100.0
    deadband: float = 0.0
    sample_time_s: float = 2.0       # should match SCADA scan interval

    _output: float = field(default=0.0, init=False)
    _integral: float = field(default=0.0, init=False)
    _prev_error: float = field(default=0.0, init=False)
    _last_time: Optional[float] = field(default=None, init=False)
    _enabled: bool = field(default=True, init=False)

    # ── Interface ─────────────────────────────────────────────────────────────
    def compute(self, process_value: float | None) -> float:
        """
        Compute the next PID output given the current process value.
        Returns the clamped output [out_min, out_max].
        """
        if not self._enabled:
            return self._output

        if process_value is None:
            logger.warning("PID '%s' received None for process_value; skipping update.", self.name)
            return self._output

        now = time.time()
        dt = (now - self._last_time) if self._last_time else self.sample_time_s
        self._last_time = now

        error = self.setpoint - process_value

        # Deadband
        if abs(error) <= self.deadband:
            return self._output

        # Proportional
        p_term = self.kp * error

        # Integral with anti-windup (back-calculation via clamping)
        self._integral += error * dt
        i_term = self.ki * self._integral

        # Derivative (on process value to avoid derivative kick)
        d_term = -self.kd * (error - self._prev_error) / max(dt, 1e-6)
        self._prev_error = error

        raw = p_term + i_term + d_term

        # Clamp output
        clamped = max(self.out_min, min(self.out_max, raw))

        # Anti-windup: back-calculate integral if output is clamped
        if raw != clamped:
            self._integral -= error * dt  # undo last integral increment

        self._output = clamped
        return self._output

    def reset(self):
        self._integral  = 0.0
        self._prev_error = 0.0
        self._last_time  = None
        logger.debug("PID '%s' reset.", self.name)

    def enable(self):
        self._enabled = True
        logger.info("PID '%s' enabled.", self.name)

    def disable(self):
        self._enabled = False
        logger.info("PID '%s' disabled.", self.name)

    @property
    def output(self) -> float:
        return self._output

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def status(self) -> dict:
        return {
            "name": self.name,
            "setpoint": self.setpoint,
            "output": round(self._output, 2),
            "integral": round(self._integral, 4),
            "enabled": self._enabled,
        }
