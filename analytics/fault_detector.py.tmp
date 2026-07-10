"""
analytics/fault_detector.py
============================
Risk-based fault detection engine for the Dikili Geothermal SCADA system.

Evaluates per-well and system-level sensor readings against configurable
thresholds and computes a composite **Risk Score** (0–100) together with a
**SystemHealth** classification (GOOD / WARNING / CRITICAL).

Scoring model
-------------
Each monitored variable contributes a partial risk score that is scaled by
a weight reflecting its relative importance.  Partial scores use sigmoid-like
linear interpolation between a "concern onset" point and a "maximum risk"
point so the score ramps smoothly instead of switching abruptly.

    ┌─────────────────────────────────────────────────────────────────┐
    │  Variable          Concern onset    Max risk    Weight          │
    │  ──────────────    ─────────────    ────────    ──────          │
    │  Temperature HI    100 °C           110 °C       35 %           │
    │  Pressure LO       4.0 bar          2.5 bar      35 %           │
    │  Flow Rate LO      80 m³/h          50 m³/h      20 %           │
    │  Sensor fault                       any           10 %           │
    └─────────────────────────────────────────────────────────────────┘

    risk_score = Σ (partial_score_i × weight_i)   clamped to [0, 100]

Health classification
---------------------
    0  – 39   →  GOOD      normal operation
    40 – 69   →  WARNING   operator attention required
    70 – 100  →  CRITICAL  immediate action required

Typical usage
-------------
>>> from analytics.fault_detector import FaultDetector
>>> from simulation.sensors import SensorReading
>>> detector = FaultDetector()
>>> report = detector.evaluate(reading)       # single well
>>> report = detector.evaluate_system(readings_list)   # all wells
>>> print(report.risk_score, report.health)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Enumerations ─────────────────────────────────────────────────────────────

class SystemHealth(Enum):
    GOOD     = "GOOD"      # 0–39
    WARNING  = "WARNING"   # 40–69
    CRITICAL = "CRITICAL"  # 70–100

    @property
    def symbol(self) -> str:
        return {"GOOD": "[OK]", "WARNING": "[!!]", "CRITICAL": "[XX]"}[self.value]


# ─── Fault factor ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class FaultFactor:
    """
    Represents one contributing element of the overall risk score.

    Attributes
    ----------
    name        : Short identifier (e.g. "TEMP_HIGH").
    description : Human-readable description of the condition.
    raw_value   : The sensor reading that triggered this factor (or None).
    partial_score : Contribution to the risk score (0–100, un-weighted).
    weight      : Weight of this factor in the composite score (0–1).
    weighted    : Actual contribution = partial_score * weight.
    """
    name:          str
    description:   str
    raw_value:     Optional[float]
    partial_score: float
    weight:        float

    @property
    def weighted(self) -> float:
        return self.partial_score * self.weight

    def __str__(self) -> str:
        val = f"{self.raw_value:.3g}" if self.raw_value is not None else "N/A"
        return (
            f"  {self.name:<20} val={val:<8} "
            f"partial={self.partial_score:5.1f}  "
            f"weight={self.weight:.2f}  "
            f"contribution={self.weighted:5.1f}"
        )


# ─── Detection report ─────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class FaultReport:
    """
    Full result of one fault detection evaluation.

    Attributes
    ----------
    well_id       : Tag identifier of the evaluated well, or "SYSTEM" for
                    a multi-well aggregate.
    timestamp     : Unix epoch of the evaluation.
    risk_score    : Composite risk score in the range [0, 100].
    health        : ``SystemHealth`` classification.
    factors       : Individual fault factors that contributed to the score.
    active_faults : Names of factors whose partial_score > 0.
    recommendations : Human-readable list of suggested operator actions.
    """
    well_id:         str
    timestamp:       float
    risk_score:      float
    health:          SystemHealth
    factors:         tuple[FaultFactor, ...]
    active_faults:   tuple[str, ...]
    recommendations: tuple[str, ...]

    # ── Convenience properties ─────────────────────────────────────────────

    @property
    def is_critical(self) -> bool:
        return self.health == SystemHealth.CRITICAL

    @property
    def is_warning(self) -> bool:
        return self.health == SystemHealth.WARNING

    @property
    def is_healthy(self) -> bool:
        return self.health == SystemHealth.GOOD

    def summary(self) -> str:
        ts   = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        flt  = ", ".join(self.active_faults) if self.active_faults else "none"
        return (
            f"[{ts}] {self.well_id:<10} "
            f"RISK={self.risk_score:5.1f}/100  "
            f"HEALTH={self.health.value:<8}  "
            f"FAULTS: {flt}"
        )

    def full_report(self) -> str:
        lines = [
            "",
            f"  Fault Detection Report -- {self.well_id}",
            f"  {'-' * 50}",
            f"  Risk Score  : {self.risk_score:.1f} / 100",
            f"  Health      : {self.health.value}  {self.health.symbol}",
            f"  Evaluated   : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}",
            "",
            "  Contributing Factors:",
        ]
        for f in self.factors:
            lines.append(str(f))
        if self.recommendations:
            lines.append("")
            lines.append("  Recommendations:")
            for r in self.recommendations:
                lines.append(f"    * {r}")
        lines.append("")
        return "\n".join(lines)


# ─── Threshold configuration ──────────────────────────────────────────────────

@dataclass
class DetectorConfig:
    """
    Configurable thresholds and weights for the fault detection engine.

    All threshold pairs define a linear ramp:
      partial_score = 0   at the  "concern_onset" point (or below/above)
      partial_score = 100 at the  "max_risk" point (or beyond)

    Weights must sum to 1.0.  Adjust as needed for different plant designs.
    """

    # Temperature
    temp_concern_c:  float = 100.0   # °C — risk starts here
    temp_max_c:      float = 110.0   # °C — full risk here
    temp_weight:     float = 0.35

    # Pressure (inverted: lower = worse)
    pres_concern_bar: float = 4.0    # bar — risk starts below this
    pres_max_bar:     float = 2.5    # bar — full risk here
    pres_weight:      float = 0.35

    # Flow rate (inverted: lower = worse)
    flow_concern_m3h: float = 80.0   # m³/h — risk starts below this
    flow_max_m3h:     float = 50.0   # m³/h — full risk here
    flow_weight:      float = 0.20

    # Sensor health penalty
    sensor_weight:    float = 0.10

    def __post_init__(self):
        total = self.temp_weight + self.pres_weight + self.flow_weight + self.sensor_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"DetectorConfig weights must sum to 1.0, got {total:.4f}"
            )


# ─── Fault Detector ───────────────────────────────────────────────────────────

class FaultDetector:
    """
    Stateless risk evaluator for geothermal sensor readings.

    Each ``evaluate()`` / ``evaluate_system()`` call is independent — the
    detector holds no history between calls.  For trend-based detection,
    wrap this class and feed it rolling windows from ``TrendAnalyzer``.

    Parameters
    ----------
    config : ``DetectorConfig`` with thresholds and weights.
             Defaults to the values defined in ``DetectorConfig``.
    """

    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()

    # ── Public API ─────────────────────────────────────────────────────────────

    def evaluate(
        self,
        well_id:        str,
        temperature_c:  Optional[float],
        pressure_bar:   Optional[float],
        flow_m3h:       Optional[float],
        sensor_healthy: bool = True,
    ) -> FaultReport:
        """
        Evaluate a single well's sensor snapshot.

        Parameters
        ----------
        well_id        : Well identifier (e.g. "GW-01").
        temperature_c  : Wellhead temperature in °C.  Pass None for LOS.
        pressure_bar   : Wellhead pressure in bar.    Pass None for LOS.
        flow_m3h       : Flow rate in m³/h.           Pass None for LOS.
        sensor_healthy : False if any sensor is in a fault/clamped state.

        Returns
        -------
        FaultReport
        """
        cfg = self.config
        factors: list[FaultFactor] = []

        # ── 1. Temperature factor ──────────────────────────────────────────
        factors.append(self._temperature_factor(temperature_c, cfg))

        # ── 2. Pressure factor ─────────────────────────────────────────────
        factors.append(self._pressure_factor(pressure_bar, cfg))

        # ── 3. Flow rate factor ────────────────────────────────────────────
        factors.append(self._flow_factor(flow_m3h, cfg))

        # ── 4. Sensor health factor ────────────────────────────────────────
        factors.append(self._sensor_factor(sensor_healthy, cfg))

        # ── Composite score ────────────────────────────────────────────────
        raw_score  = sum(f.weighted for f in factors)
        risk_score = round(min(max(raw_score, 0.0), 100.0), 2)
        health     = self._classify(risk_score)

        active  = tuple(f.name for f in factors if f.partial_score > 0)
        recs    = self._recommendations(factors, sensor_healthy)

        report = FaultReport(
            well_id         = well_id,
            timestamp       = time.time(),
            risk_score      = risk_score,
            health          = health,
            factors         = tuple(factors),
            active_faults   = active,
            recommendations = recs,
        )

        level = logging.WARNING if health != SystemHealth.GOOD else logging.DEBUG
        logger.log(level, "%s", report.summary())
        return report

    def evaluate_from_reading(self, reading) -> FaultReport:
        """
        Convenience wrapper that accepts a ``SensorReading`` dataclass
        (from ``simulation.sensors``) directly.

        Parameters
        ----------
        reading : ``simulation.sensors.SensorReading``
        """
        return self.evaluate(
            well_id        = reading.well_id,
            temperature_c  = reading.temperature_c,
            pressure_bar   = reading.pressure_bar,
            flow_m3h       = reading.flow_m3h,
            sensor_healthy = reading.is_healthy,
        )

    def evaluate_system(self, readings: list) -> FaultReport:
        """
        Aggregate fault detection across multiple wells.

        Computes per-well reports, then derives a system-level report whose
        risk score is the **maximum** individual well score — the worst well
        defines the system health.

        Parameters
        ----------
        readings : List of ``SensorReading`` objects (from ``simulation.sensors``).

        Returns
        -------
        FaultReport
            Well ID is set to "SYSTEM"; risk_score and health reflect the
            worst-case single well.  Recommendations are merged and de-duplicated.
        """
        if not readings:
            raise ValueError("readings list must not be empty.")

        per_well = [self.evaluate_from_reading(r) for r in readings]

        worst      = max(per_well, key=lambda rp: rp.risk_score)
        all_faults = tuple(dict.fromkeys(
            f"{rp.well_id}:{fault}"
            for rp in per_well
            for fault in rp.active_faults
        ))
        all_recs = tuple(dict.fromkeys(
            rec for rp in per_well for rec in rp.recommendations
        ))
        avg_score = round(sum(rp.risk_score for rp in per_well) / len(per_well), 2)

        # Synthetic system-level factors showing per-well worst values
        sys_factors = tuple(
            FaultFactor(
                name          = f"{rp.well_id}:RISK",
                description   = f"Well {rp.well_id} composite risk",
                raw_value     = rp.risk_score,
                partial_score = rp.risk_score,
                weight        = 1.0 / len(per_well),
            )
            for rp in per_well
        )

        system_report = FaultReport(
            well_id         = "SYSTEM",
            timestamp       = time.time(),
            risk_score      = worst.risk_score,   # worst-case drives system health
            health          = worst.health,
            factors         = sys_factors,
            active_faults   = all_faults,
            recommendations = all_recs,
        )

        logger.info(
            "SYSTEM evaluation: worst=%.1f avg=%.1f health=%s",
            worst.risk_score, avg_score, worst.health.value,
        )
        return system_report

    # ── Factor builders ────────────────────────────────────────────────────────

    def _temperature_factor(
        self, temp: Optional[float], cfg: DetectorConfig
    ) -> FaultFactor:
        if temp is None:
            return FaultFactor(
                "TEMP_LOSS_OF_SIGNAL",
                "Temperature sensor — loss of signal",
                None, 100.0, cfg.temp_weight,
            )
        score = _ramp_up(temp, cfg.temp_concern_c, cfg.temp_max_c)
        desc  = (
            "Temperature nominal"                    if score == 0 else
            f"Temperature elevated ({temp:.1f} C)"   if score < 60 else
            f"Temperature critical ({temp:.1f} C)"
        )
        return FaultFactor("TEMP_HIGH", desc, temp, score, cfg.temp_weight)

    def _pressure_factor(
        self, pres: Optional[float], cfg: DetectorConfig
    ) -> FaultFactor:
        if pres is None:
            return FaultFactor(
                "PRES_LOSS_OF_SIGNAL",
                "Pressure sensor — loss of signal",
                None, 100.0, cfg.pres_weight,
            )
        # Inverted ramp: risk rises as pressure FALLS below concern threshold
        score = _ramp_down(pres, cfg.pres_concern_bar, cfg.pres_max_bar)
        desc  = (
            "Pressure nominal"                        if score == 0 else
            f"Pressure low ({pres:.3f} bar)"          if score < 60 else
            f"Pressure critically low ({pres:.3f} bar)"
        )
        return FaultFactor("PRES_LOW", desc, pres, score, cfg.pres_weight)

    def _flow_factor(
        self, flow: Optional[float], cfg: DetectorConfig
    ) -> FaultFactor:
        if flow is None:
            return FaultFactor(
                "FLOW_LOSS_OF_SIGNAL",
                "Flow sensor — loss of signal",
                None, 100.0, cfg.flow_weight,
            )
        score = _ramp_down(flow, cfg.flow_concern_m3h, cfg.flow_max_m3h)
        desc  = (
            "Flow rate nominal"                       if score == 0 else
            f"Flow rate low ({flow:.1f} m3/h)"        if score < 60 else
            f"Flow rate critically low ({flow:.1f} m3/h)"
        )
        return FaultFactor("FLOW_LOW", desc, flow, score, cfg.flow_weight)

    def _sensor_factor(
        self, healthy: bool, cfg: DetectorConfig
    ) -> FaultFactor:
        score = 0.0 if healthy else 100.0
        desc  = "All sensors nominal" if healthy else "Sensor reading at physical limit"
        return FaultFactor("SENSOR_FAULT", desc, None, score, cfg.sensor_weight)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _classify(score: float) -> SystemHealth:
        if score >= 70.0:
            return SystemHealth.CRITICAL
        if score >= 40.0:
            return SystemHealth.WARNING
        return SystemHealth.GOOD

    @staticmethod
    def _recommendations(
        factors: list[FaultFactor], healthy: bool
    ) -> tuple[str, ...]:
        recs: list[str] = []
        for f in factors:
            if f.partial_score == 0:
                continue
            if f.name == "TEMP_HIGH":
                recs.append("Check wellhead temperature — consider reducing pump speed.")
                if f.partial_score >= 80:
                    recs.append("URGENT: Temperature near limit — initiate controlled shutdown.")
            elif f.name in ("TEMP_LOSS_OF_SIGNAL",):
                recs.append("Inspect RTD wiring on temperature sensor — loss of signal.")
            elif f.name == "PRES_LOW":
                recs.append("Check wellhead pressure — inspect pump seals and isolation valves.")
                if f.partial_score >= 80:
                    recs.append("URGENT: Low pressure may indicate pump cavitation or pipe leak.")
            elif f.name in ("PRES_LOSS_OF_SIGNAL",):
                recs.append("Inspect pressure transmitter signal cable — loss of signal.")
            elif f.name == "FLOW_LOW":
                recs.append("Check flow meter and upstream valves — flow below acceptable range.")
                if f.partial_score >= 80:
                    recs.append("URGENT: Very low flow — risk of pump dry-run damage.")
            elif f.name in ("FLOW_LOSS_OF_SIGNAL",):
                recs.append("Inspect flow meter — loss of signal, possible wiring fault.")
            elif f.name == "SENSOR_FAULT":
                recs.append("One or more sensors reading at physical limit — verify field instruments.")
        return tuple(dict.fromkeys(recs))   # de-duplicate, preserve order


# ─── Pure maths helpers ───────────────────────────────────────────────────────

def _ramp_up(value: float, onset: float, maximum: float) -> float:
    """
    Linear ramp from 0 to 100 as *value* rises from *onset* to *maximum*.
    Returns 0 below onset, 100 at or above maximum.
    """
    if value <= onset:
        return 0.0
    if value >= maximum:
        return 100.0
    return (value - onset) / (maximum - onset) * 100.0


def _ramp_down(value: float, onset: float, maximum: float) -> float:
    """
    Linear ramp from 0 to 100 as *value* falls from *onset* down to *maximum*.
    Returns 0 at or above onset, 100 at or below maximum.
    (onset > maximum for inverted / low-limit checks)
    """
    if value >= onset:
        return 0.0
    if value <= maximum:
        return 100.0
    return (onset - value) / (onset - maximum) * 100.0


# ─── Module self-test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    detector = FaultDetector()

    scenarios = [
        # (label, well, temp, pres, flow, healthy)
        ("All nominal",               "GW-01",  92.0, 7.5,  180.0, True),
        ("Temp slightly elevated",    "GW-01", 101.5, 7.5,  175.0, True),
        ("Temp critical",             "GW-01", 108.0, 7.5,  165.0, True),
        ("Pressure low (concern)",    "GW-02",  90.0, 3.8,  170.0, True),
        ("Pressure critical",         "GW-02",  90.0, 2.6,  150.0, True),
        ("Flow low (concern)",        "GW-03",  91.0, 7.0,   72.0, True),
        ("Flow critical",             "GW-03",  91.0, 7.0,   51.0, True),
        ("Sensor fault",              "GW-01",  92.0, 7.5,  180.0, False),
        ("Multi-fault (T+P+Q)",       "GW-02", 104.0, 3.2,   62.0, True),
        ("Loss of signal (all None)", "GW-03",  None, None, None,  False),
    ]

    print("\n=== FaultDetector  Single-Well Scenarios ===\n")
    for label, wid, t, p, q, h in scenarios:
        report = detector.evaluate(wid, t, p, q, h)
        t_s = f"{t:.1f}" if t is not None else " N/A"
        p_s = f"{p:.2f}" if p is not None else "N/A "
        q_s = f"{q:.1f}" if q is not None else " N/A"
        print(
            f"  {label:<30} "
            f"T={t_s}C  P={p_s}bar  Q={q_s}m3/h  "
            f"-> RISK={report.risk_score:5.1f}  "
            f"HEALTH={report.health.value:<8} {report.health.symbol}"
        )

    print("\n=== Detailed Report: Multi-Fault ===")
    multi = detector.evaluate("GW-02", 104.0, 3.2, 62.0, True)
    print(multi.full_report())

    print("=== System-Level Evaluation ===\n")
    # Simulate using sensor readings directly
    from simulation.sensors import create_well_array
    wells   = create_well_array()
    readings = [w.read() for w in wells]
    sys_rpt  = detector.evaluate_system(readings)
    print(sys_rpt.full_report())
    print("  Per-well details:")
    for r in readings:
        wr = detector.evaluate_from_reading(r)
        print(f"    {wr.summary()}")
