"""
analytics/kpi_engine.py
Key Performance Indicator calculations for the Dikili Geothermal plant.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KPIEngine:
    """
    Computes real-time and rolling KPIs from tag values.

    KPIs
    ----
    COP         — Coefficient of Performance (thermal output / pumping energy)
    Capacity Factor — Actual vs. design capacity
    MTBF        — Mean time between failures (alarm events)
    Efficiency  — HX thermal efficiency
    Load Factor — Current load vs. rated load
    """

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self._alarm_events: list[float] = []   # timestamps of alarm trips
        self._last_alarm_count = 0
        self._session_start = time.time()

    def compute(self) -> dict:
        """Return a dict of current KPI values."""
        kpis = {}

        # ── Thermal Power & Capacity Factor ───────────────────────────────────
        power_mw = self.db.read_value("PLANT.TOTAL_POWER", 0.0) or 0.0
        design_mw = sum(z.design_load_mw for z in self.config.zones)
        kpis["thermal_power_mw"]   = round(power_mw, 3)
        kpis["design_capacity_mw"] = round(design_mw, 3)
        kpis["capacity_factor_pct"]= round(min(power_mw / max(design_mw, 0.001) * 100, 100), 1)

        # ── HX Efficiency ─────────────────────────────────────────────────────
        kpis["hx_efficiency_pct"] = self.db.read_value("HX.EFFICIENCY", 0.0) or 0.0

        # ── Temperature Performance ────────────────────────────────────────────
        supply   = self.db.read_value("HX.SEC_SUPPLY", 0.0) or 0.0
        target_s = self.config.target_supply_temp_c
        kpis["supply_temp_c"]      = round(supply, 2)
        kpis["supply_temp_dev_k"]  = round(abs(supply - target_s), 2)

        # ── Network Δ-T ───────────────────────────────────────────────────────
        delta_t = self.db.read_value("DH.DELTA_T", 0.0) or 0.0
        kpis["delta_t_k"] = round(delta_t, 2)

        # ── Energy Delivered Today ─────────────────────────────────────────────
        kpis["daily_energy_mwh"] = self.db.read_value("PLANT.DAILY_ENERGY", 0.0) or 0.0

        # ── System Uptime ─────────────────────────────────────────────────────
        kpis["uptime_pct"] = self.db.read_value("PLANT.UPTIME_PCT", 0.0) or 0.0

        # ── Simplified COP ────────────────────────────────────────────────────
        # COP = Q_delivered / W_pumping   (estimate pumping as 3% of thermal)
        est_pump_power_mw = power_mw * 0.03
        kpis["cop"] = round(power_mw / max(est_pump_power_mw, 0.001), 1)

        # ── Alarm Rate (alarms/hour) ───────────────────────────────────────────
        alarm_count = self.db.read_value("PLANT.ALARM_COUNT", 0) or 0
        if alarm_count > self._last_alarm_count:
            self._alarm_events.append(time.time())
        self._last_alarm_count = alarm_count

        # Keep only last 24 h of alarm events
        cutoff = time.time() - 86400
        self._alarm_events = [t for t in self._alarm_events if t > cutoff]
        elapsed_h = max((time.time() - self._session_start) / 3600.0, 0.001)
        kpis["alarm_rate_per_hour"] = round(len(self._alarm_events) / elapsed_h, 2)

        return kpis
