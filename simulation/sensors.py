"""
simulation/sensors.py
=====================
Standalone geothermal sensor simulation module.

Generates realistic, time-varying readings for the three core process
variables of the Dikili Geothermal District Heating Plant:

    ┌─────────────────────────────────────────────────────────┐
    │  Variable      Range          Unit   Typical at base    │
    │  ──────────    ─────────────  ────   ─────────────────  │
    │  Temperature   70 – 110 °C   °C     ~95 °C             │
    │  Pressure       3 – 12 bar   bar    ~7.5 bar            │
    │  Flow Rate     50 – 300 m³/h m³/h   ~175 m³/h          │
    └─────────────────────────────────────────────────────────┘

Design goals
------------
* **Time-varying, not fully random** — values evolve smoothly via
  sinusoidal baselines that mimic daily demand cycles and slow
  reservoir drift.  Gaussian noise is layered on top.
* **Physically correlated** — higher flow → slight pressure drop;
  temperature tracks a slow thermal-mass oscillation independently.
* **Self-contained** — no dependency on core.config.system_config, TagDatabase,
  or any other SCADA subsystem.  Import and use directly.
* **Stateful** — each ``GeothermalSensorArray`` instance tracks its
  own internal state so successive calls produce a coherent time
  series.

Typical usage
-------------
>>> sensor_array = GeothermalSensorArray(well_id="GW-01")
>>> reading = sensor_array.read()
>>> print(reading.temperature_c, reading.pressure_bar, reading.flow_m3h)

Or for a quick one-shot reading without managing state:
>>> from simulation.sensors import quick_read
>>> r = quick_read()
"""

from __future__ import annotations

import math
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Physical constants & defaults ────────────────────────────────────────────

# Temperature
_TEMP_BASE      = 92.0      # °C  — long-run average wellhead temperature
_TEMP_AMPLITUDE = 8.0       # °C  — peak-to-peak daily thermal swing (±4 °C)
_TEMP_PERIOD    = 3600 * 8  # s   — 8-hour thermal cycle (reservoir slow response)
_TEMP_NOISE     = 0.25      # °C  — 1-sigma sensor noise

# Pressure
_PRES_BASE      = 7.5       # bar — nominal wellhead pressure
_PRES_AMPLITUDE = 1.8       # bar — demand-driven pressure swing (±0.9 bar)
_PRES_PERIOD    = 3600 * 6  # s   — 6-hour cycle (pump load pattern)
_PRES_NOISE     = 0.04      # bar — 1-sigma sensor noise

# Flow rate
_FLOW_BASE      = 175.0     # m3/h — nominal flow (approx. 70 % of design capacity)
_FLOW_AMPLITUDE = 80.0      # m3/h — demand-driven swing (±40 m3/h)
_FLOW_PERIOD    = 3600 * 4  # s   — 4-hour peak demand cycle
_FLOW_NOISE     = 1.5       # m3/h — 1-sigma turbine-meter noise

# Physical limits (hard clamp — sensor never reports outside these)
_TEMP_MIN,  _TEMP_MAX  = 70.0,  110.0   # °C
_PRES_MIN,  _PRES_MAX  =  3.0,   12.0   # bar
_FLOW_MIN,  _FLOW_MAX  = 50.0,  300.0   # m3/h

# Pressure–flow coupling coefficient
# Every 50 m3/h of flow above/below baseline causes ~0.3 bar pressure drop/rise
_FLOW_PRES_COUPLING = 0.006   # bar per m3/h deviation from baseline


# ─── Data transfer object ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SensorReading:
    """
    Immutable snapshot of one sensor scan cycle.

    Attributes
    ----------
    well_id         : Identifier of the production well (e.g. ``"GW-01"``).
    timestamp       : Unix epoch of the reading (seconds).
    temperature_c   : Wellhead fluid temperature in degrees Celsius.
    pressure_bar    : Wellhead pressure in bar.
    flow_m3h        : Production flow rate in m3/h.
    is_healthy      : False when any value is clamped at a physical limit
                      (indicative of a sensor or process anomaly).
    """

    well_id:        str
    timestamp:      float
    temperature_c:  float
    pressure_bar:   float
    flow_m3h:       float
    is_healthy:     bool

    def __str__(self) -> str:
        status = "OK" if self.is_healthy else "WARN:LIMIT"
        return (
            f"[{self.well_id}] "
            f"T={self.temperature_c:6.2f} C  "
            f"P={self.pressure_bar:5.3f} bar  "
            f"Q={self.flow_m3h:6.1f} m3/h  "
            f"[{status}]"
        )


# ─── Core sensor array ────────────────────────────────────────────────────────

class GeothermalSensorArray:
    """
    Simulates the three primary sensors on a single geothermal production well.

    Each instance maintains independent internal state so that multiple
    wells can be modelled simultaneously with natural phase offsets.

    Parameters
    ----------
    well_id         : Logical tag prefix (e.g. ``"GW-01"``).
    phase_offset    : Seconds of phase shift applied to all sine baselines.
                      Use different offsets per well to break synchrony.
    temp_base       : Override the default temperature baseline (degrees C).
    pres_base       : Override the default pressure baseline (bar).
    flow_base       : Override the default flow baseline (m3/h).
    random_seed     : Optional seed for reproducible sequences.
    """

    def __init__(
        self,
        well_id:      str   = "GW-01",
        phase_offset: float = 0.0,
        temp_base:    float = _TEMP_BASE,
        pres_base:    float = _PRES_BASE,
        flow_base:    float = _FLOW_BASE,
        random_seed:  Optional[int] = None,
    ) -> None:
        self.well_id      = well_id
        self._phase       = phase_offset
        self._temp_base   = temp_base
        self._pres_base   = pres_base
        self._flow_base   = flow_base
        self._rng         = random.Random(random_seed)

        # Slow-moving internal state (exponential smoothing targets)
        self._temp_truth: float = temp_base
        self._pres_truth: float = pres_base
        self._flow_truth: float = flow_base

        logger.debug(
            "GeothermalSensorArray '%s' initialised (phase=%.0f s).",
            well_id, phase_offset,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def read(self, at: Optional[float] = None) -> SensorReading:
        """
        Generate one sensor reading.

        Parameters
        ----------
        at : Unix timestamp to evaluate at.  Defaults to ``time.time()``.

        Returns
        -------
        SensorReading
            Frozen dataclass with temperature, pressure, flow, and health flag.
        """
        t = (at if at is not None else time.time()) + self._phase

        # ── 1. Sinusoidal baseline (slow deterministic trend) ──────────────
        temp_sin = _TEMP_AMPLITUDE * math.sin(2 * math.pi * t / _TEMP_PERIOD)
        pres_sin = _PRES_AMPLITUDE * math.sin(2 * math.pi * t / _PRES_PERIOD)
        flow_sin = _FLOW_AMPLITUDE * math.sin(2 * math.pi * t / _FLOW_PERIOD)

        target_temp = self._temp_base + temp_sin
        target_flow = self._flow_base + flow_sin
        target_pres = self._pres_base + pres_sin

        # ── 2. Exponential smoothing (thermal / hydraulic inertia) ─────────
        #   alpha is the smoothing factor (0 < alpha < 1).
        #   Higher alpha = faster response, lower = more inertia.
        self._temp_truth = self._smooth(self._temp_truth, target_temp, alpha=0.08)
        self._flow_truth = self._smooth(self._flow_truth, target_flow, alpha=0.12)

        # Pressure physically coupled to flow: more flow -> lower pressure
        flow_deviation   = self._flow_truth - self._flow_base
        pressure_coupled = target_pres - flow_deviation * _FLOW_PRES_COUPLING
        self._pres_truth = self._smooth(self._pres_truth, pressure_coupled, alpha=0.15)

        # ── 3. Gaussian sensor noise ───────────────────────────────────────
        temp_meas = self._temp_truth + self._rng.gauss(0.0, _TEMP_NOISE)
        pres_meas = self._pres_truth + self._rng.gauss(0.0, _PRES_NOISE)
        flow_meas = self._flow_truth + self._rng.gauss(0.0, _FLOW_NOISE)

        # ── 4. Physical limit clamping ─────────────────────────────────────
        temp_out, temp_clamped = self._clamp(temp_meas, _TEMP_MIN, _TEMP_MAX)
        pres_out, pres_clamped = self._clamp(pres_meas, _PRES_MIN, _PRES_MAX)
        flow_out, flow_clamped = self._clamp(flow_meas, _FLOW_MIN, _FLOW_MAX)

        is_healthy = not (temp_clamped or pres_clamped or flow_clamped)

        reading = SensorReading(
            well_id       = self.well_id,
            timestamp     = time.time(),
            temperature_c = round(temp_out, 2),
            pressure_bar  = round(pres_out, 3),
            flow_m3h      = round(flow_out, 1),
            is_healthy    = is_healthy,
        )

        logger.debug("%s", reading)
        return reading

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _smooth(current: float, target: float, alpha: float) -> float:
        """
        First-order exponential smoothing (IIR low-pass filter).

        alpha is the smoothing factor (0 < alpha < 1).
        Higher alpha means faster response; lower means more inertia.
        """
        return current + alpha * (target - current)

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> tuple[float, bool]:
        """Return (clamped_value, was_clamped)."""
        if value < lo:
            return lo, True
        if value > hi:
            return hi, True
        return value, False


# ─── Multi-well convenience factory ───────────────────────────────────────────

def create_well_array(
    well_ids: list[str] | None = None,
    *,
    temp_bases:  list[float] | None = None,
    pres_bases:  list[float] | None = None,
    flow_bases:  list[float] | None = None,
) -> list[GeothermalSensorArray]:
    """
    Instantiate a ``GeothermalSensorArray`` for each well in *well_ids*.

    Phase offsets are distributed evenly across one full flow cycle so wells
    do not peak or trough in lockstep.

    Parameters
    ----------
    well_ids    : List of well tag IDs.  Defaults to ``["GW-01", "GW-02", "GW-03"]``.
    temp_bases  : Per-well temperature baselines.  Falls back to the module default.
    pres_bases  : Per-well pressure baselines.
    flow_bases  : Per-well flow baselines.

    Returns
    -------
    list[GeothermalSensorArray]

    Example
    -------
    >>> wells = create_well_array()
    >>> readings = [w.read() for w in wells]
    """
    if well_ids is None:
        well_ids = ["GW-01", "GW-02", "GW-03"]

    n = len(well_ids)
    phase_step = _FLOW_PERIOD / n   # spread phases across one demand cycle

    arrays: list[GeothermalSensorArray] = []
    for i, wid in enumerate(well_ids):
        kwargs: dict = dict(
            well_id      = wid,
            phase_offset = i * phase_step,
        )
        if temp_bases and i < len(temp_bases):
            kwargs["temp_base"] = temp_bases[i]
        if pres_bases and i < len(pres_bases):
            kwargs["pres_base"] = pres_bases[i]
        if flow_bases and i < len(flow_bases):
            kwargs["flow_base"] = flow_bases[i]

        arrays.append(GeothermalSensorArray(**kwargs))

    logger.info(
        "Created %d GeothermalSensorArray instances: %s", n, well_ids
    )
    return arrays


# ─── One-shot helper ──────────────────────────────────────────────────────────

def quick_read(well_id: str = "GW-01") -> SensorReading:
    """
    Return a single stateless sensor reading.

    Useful for scripts and tests that need one snapshot without
    managing a ``GeothermalSensorArray`` instance.  Each call creates
    a fresh array, so successive calls will **not** produce a coherent
    time series — use ``GeothermalSensorArray.read()`` for that.

    Parameters
    ----------
    well_id : Tag ID to embed in the returned ``SensorReading``.
    """
    return GeothermalSensorArray(well_id=well_id).read()


# ─── Module self-test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    print("\n-- GeothermalSensorArray  ·  10-step live demo --\n")

    wells = create_well_array()
    for step in range(10):
        print(f"  Step {step + 1:02d}:")
        for sensor in wells:
            r = sensor.read()
            print(f"    {r}")
        print()
        time.sleep(0.5)
