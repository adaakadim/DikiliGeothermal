"""
analytics/reporter.py
Periodic report generator — console KPI reports and JSON snapshots.
"""

import json
import logging
import time
from pathlib import Path

from .kpi_engine import KPIEngine
from .trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)

REPORT_DIR = Path("data/reports")


class ReportGenerator:
    """
    Generates periodic summary reports:
      - Every 60 s: console KPI summary
      - Every 300 s: JSON snapshot saved to data/reports/
    """

    def __init__(self, scada):
        self.scada  = scada
        self.db     = scada.db
        self.config = scada.config
        self.kpi    = KPIEngine(self.db, self.config)
        self.trends = TrendAnalyzer(self.db)

        self._last_console_report = 0.0
        self._last_file_report    = 0.0
        self._report_index        = 0

        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def update(self):
        """Call once per SCADA tick."""
        self.trends.update()
        now = time.time()

        if now - self._last_console_report >= 60:
            self._console_kpi_report()
            self._last_console_report = now

        if now - self._last_file_report >= 300:
            self._file_snapshot()
            self._last_file_report = now

    # ── Console Report ────────────────────────────────────────────────────────
    def _console_kpi_report(self):
        kpis = self.kpi.compute()
        anomalies = self.trends.anomalies()

        print("\n" + "─" * 60)
        print("  📊  KPI REPORT  —  DikiliGeothermal Plant")
        print("─" * 60)
        print(f"  Thermal Power    : {kpis.get('thermal_power_mw', 0):.2f} MW")
        print(f"  Capacity Factor  : {kpis.get('capacity_factor_pct', 0):.1f} %")
        print(f"  HX Efficiency    : {kpis.get('hx_efficiency_pct', 0):.1f} %")
        print(f"  Supply Temp      : {kpis.get('supply_temp_c', 0):.1f} °C  "
              f"(dev: {kpis.get('supply_temp_dev_k', 0):.1f} K)")
        print(f"  ΔT (supply-ret)  : {kpis.get('delta_t_k', 0):.1f} K")
        print(f"  COP              : {kpis.get('cop', 0):.1f}")
        print(f"  Daily Energy     : {kpis.get('daily_energy_mwh', 0):.3f} MWh")
        print(f"  Uptime Today     : {kpis.get('uptime_pct', 0):.1f} %")
        print(f"  Alarm Rate       : {kpis.get('alarm_rate_per_hour', 0):.2f} /h")

        if anomalies:
            print(f"\n  ⚠  TREND ANOMALIES: {', '.join(anomalies)}")

        print("─" * 60)

    # ── File Snapshot ─────────────────────────────────────────────────────────
    def _file_snapshot(self):
        self._report_index += 1
        ts_str = time.strftime("%Y%m%d_%H%M%S")
        fname  = REPORT_DIR / f"snapshot_{ts_str}.json"

        snapshot = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "plant":  self.config.plant_name,
            "kpis":   self.kpi.compute(),
            "alarms": self.scada.alarms.summary(),
            "tags":   self.db.snapshot(),
            "trends": self.trends.all_summaries(),
        }

        with open(fname, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, default=str)

        logger.info("Snapshot saved: %s", fname)
