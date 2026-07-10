"""
analytics/matplotlib_dashboard.py
==================================
Live matplotlib monitoring dashboard for the Dikili Geothermal SCADA system.

Renders a 2x2 industrial-style plot panel that refreshes every 2 seconds,
showing time-series traces for temperature, pressure, flow rate, and risk
score across all three production wells.

Run directly:
    python -m analytics.matplotlib_dashboard

or import and call:
    from analytics.matplotlib_dashboard import SCADAPlotDashboard
    dash = SCADAPlotDashboard()
    dash.run()
"""

from __future__ import annotations

import sys
import time
import logging
from collections import deque
from datetime import datetime
from typing import Optional

import matplotlib  # type: ignore
matplotlib.use("TkAgg")          # works headless-safe; falls back gracefully
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.animation as animation  # type: ignore
import matplotlib.gridspec as gridspec  # type: ignore
from matplotlib.lines import Line2D  # type: ignore


from simulation.sensors import create_well_array, SensorReading
from analytics.fault_detector import FaultDetector, SystemHealth

logger = logging.getLogger(__name__)

# ─── Industrial colour palette ────────────────────────────────────────────────

# Dark background theme
BG_FIGURE   = "#0d1117"   # outermost figure background
BG_AXES     = "#161b22"   # individual plot backgrounds
BG_PANEL    = "#1c2128"   # header / legend panel
GRID_COLOR  = "#21262d"
BORDER_CLR  = "#30363d"
TEXT_CLR    = "#e6edf3"
DIM_TEXT    = "#8b949e"

# Per-well trace colours
WELL_COLORS = {
    "GW-01": "#00e5ff",   # electric cyan
    "GW-02": "#ff9800",   # amber
    "GW-03": "#76ff03",   # lime green
}
WELL_ALPHA   = 0.90
FILL_ALPHA   = 0.08

# Threshold / annotation colours
CLR_HI_HI    = "#ff1744"   # critical high
CLR_HI       = "#ff9100"   # high warning
CLR_LO       = "#ff9100"   # low warning
CLR_LO_LO    = "#ff1744"   # critical low
CLR_NOMINAL  = "#00e676"   # nominal band

# Risk score colours
RISK_GOOD     = "#00e676"
RISK_WARN     = "#ffc400"
RISK_CRIT     = "#ff1744"

# ─── Process alarm thresholds (matching Thresholds in dashboard.py) ───────────

T_HI_HI = 109.0;  T_HI = 105.0;  T_LO = 78.0;  T_LO_LO = 72.0
P_LO_LO = 3.5;    P_LO = 4.5
Q_LO_LO = 55.0;   Q_LO = 80.0
RISK_WARN_LEVEL = 40.0;  RISK_CRIT_LEVEL = 70.0

# ─── Rolling buffer size ──────────────────────────────────────────────────────
MAX_POINTS = 90   # ~3 minutes at 2-second scans


class SCADAPlotDashboard:
    """
    Live matplotlib SCADA monitoring dashboard.

    Parameters
    ----------
    well_ids      : Production well identifiers.
    scan_interval : Seconds between data acquisitions (default 2.0).
    max_points    : Rolling history length in samples (default 90 = ~3 min).
    """

    def __init__(
        self,
        well_ids: list[str] | None = None,
        scan_interval: float = 2.0,
        max_points: int = MAX_POINTS,
    ) -> None:
        if well_ids is None:
            well_ids = ["GW-01", "GW-02", "GW-03"]

        self._wells       = create_well_array(well_ids)
        self._well_ids    = well_ids
        self._interval    = scan_interval
        self._detector    = FaultDetector()
        self._cycle       = 0
        self._start_time  = time.time()

        # Rolling data buffers: {well_id: deque}
        self._times: deque[float] = deque(maxlen=max_points)
        self._data: dict[str, dict[str, deque]] = {
            wid: {
                "temp":  deque(maxlen=max_points),
                "pres":  deque(maxlen=max_points),
                "flow":  deque(maxlen=max_points),
                "risk":  deque(maxlen=max_points),
            }
            for wid in well_ids
        }

        self._fig  = None
        self._axes = {}
        self._lines: dict[str, dict[str, Line2D]] = {}
        self._fills: dict[str, dict] = {}
        self._anim = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Build the figure and start the animation loop (blocks until closed)."""
        self._build_figure()
        self._anim = animation.FuncAnimation(
            self._fig,
            self._update,
            interval=int(self._interval * 1000),
            cache_frame_data=False,
        )
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()

    # ── Figure construction ────────────────────────────────────────────────────

    def _build_figure(self) -> None:
        plt.rcParams.update({
            "font.family":          "monospace",
            "font.size":            9,
            "axes.facecolor":       BG_AXES,
            "axes.edgecolor":       BORDER_CLR,
            "axes.labelcolor":      TEXT_CLR,
            "axes.titlecolor":      TEXT_CLR,
            "axes.grid":            True,
            "grid.color":           GRID_COLOR,
            "grid.linestyle":       "--",
            "grid.linewidth":       0.5,
            "grid.alpha":           0.6,
            "xtick.color":          DIM_TEXT,
            "ytick.color":          DIM_TEXT,
            "xtick.labelsize":      8,
            "ytick.labelsize":      8,
            "figure.facecolor":     BG_FIGURE,
            "figure.edgecolor":     BG_FIGURE,
            "text.color":           TEXT_CLR,
            "lines.linewidth":      1.8,
            "lines.antialiased":    True,
            "legend.facecolor":     BG_PANEL,
            "legend.edgecolor":     BORDER_CLR,
            "legend.labelcolor":    TEXT_CLR,
            "legend.fontsize":      8,
        })

        self._fig = plt.figure(figsize=(14, 9))
        self._fig.patch.set_facecolor(BG_FIGURE)

        # ── Super title (status bar) ───────────────────────────────────────
        self._title = self._fig.suptitle(
            "  DIKILI GEOTHERMAL SCADA  |  MONITORING DASHBOARD  |  Initialising...",
            fontsize=11, fontweight="bold",
            color=TEXT_CLR, ha="left", x=0.01,
            backgroundcolor=BG_PANEL,
        )

        # ── 2x2 grid ──────────────────────────────────────────────────────
        gs = gridspec.GridSpec(
            2, 2,
            figure=self._fig,
            hspace=0.38, wspace=0.30,
            left=0.07, right=0.97,
            top=0.90, bottom=0.08,
        )

        specs = [
            ("temp",  gs[0, 0], "TEMPERATURE",  "°C",    (70, 112),
             [(T_HI_HI, CLR_HI_HI, "HI-HI"), (T_HI, CLR_HI, "HI"),
              (T_LO,    CLR_LO,    "LO"),      (T_LO_LO, CLR_LO_LO, "LO-LO")]),
            ("pres",  gs[0, 1], "PRESSURE",     "bar",   (2, 13),
             [(P_LO_LO, CLR_LO_LO, "LO-LO"), (P_LO, CLR_LO, "LO")]),
            ("flow",  gs[1, 0], "FLOW RATE",    "m³/h",  (40, 310),
             [(Q_LO_LO, CLR_LO_LO, "LO-LO"), (Q_LO, CLR_LO, "LO")]),
            ("risk",  gs[1, 1], "RISK SCORE",   "/100",  (-2, 102),
             [(RISK_CRIT_LEVEL, CLR_HI_HI, "CRIT"),
              (RISK_WARN_LEVEL, CLR_HI,    "WARN")]),
        ]

        for key, gs_cell, title, unit, ylim, thresholds in specs:
            ax = self._fig.add_subplot(gs_cell)
            ax.set_facecolor(BG_AXES)
            ax.set_ylim(*ylim)
            ax.set_ylabel(f"{title}  ({unit})", fontsize=8.5, labelpad=4)
            ax.set_title(f"  {title}", loc="left", fontsize=9,
                         fontweight="bold", pad=6)
            ax.tick_params(axis="x", rotation=20, labelsize=7)

            # Threshold reference lines
            for level, color, label in thresholds:
                ax.axhline(level, color=color, linewidth=0.8,
                           linestyle="--", alpha=0.65, zorder=1)
                ax.text(0.01, level, f" {label}", transform=ax.get_yaxis_transform(),
                        color=color, fontsize=7, va="bottom", alpha=0.75)

            # Shaded nominal region for temperature
            if key == "temp":
                ax.axhspan(T_LO, T_HI, color=CLR_NOMINAL, alpha=0.04, zorder=0)
            if key == "risk":
                ax.axhspan(0, RISK_WARN_LEVEL, color=RISK_GOOD, alpha=0.04, zorder=0)
                ax.axhspan(RISK_WARN_LEVEL, RISK_CRIT_LEVEL,
                           color=RISK_WARN, alpha=0.04, zorder=0)
                ax.axhspan(RISK_CRIT_LEVEL, 100, color=RISK_CRIT, alpha=0.05, zorder=0)

            self._axes[key] = ax
            self._lines[key] = {}
            self._fills[key] = {}

            # One line + fill per well
            for wid in self._well_ids:
                color = WELL_COLORS.get(wid, "#ffffff")
                (line,) = ax.plot([], [], color=color, alpha=WELL_ALPHA,
                                  linewidth=1.8, label=wid, zorder=3)
                self._lines[key][wid] = line
                self._fills[key][wid] = None   # filled area created later

            # Legend — only on first row plots
            if key in ("temp", "pres", "risk", "flow"):
                custom_handles = [
                    Line2D([0], [0], color=WELL_COLORS.get(w, "#fff"),
                           linewidth=2, label=w)
                    for w in self._well_ids
                ]
                ax.legend(handles=custom_handles, loc="upper right",
                          framealpha=0.7, borderpad=0.4)

        # ── Decorative border around the whole figure ──────────────────────
        self._fig.add_artist(plt.Rectangle(
            (0, 0), 1, 1,
            fill=False, edgecolor=BORDER_CLR, linewidth=1.5,
            transform=self._fig.transFigure, zorder=10,
        ))

    # ── Animation update ───────────────────────────────────────────────────────

    def _update(self, _frame) -> list:
        self._cycle += 1
        now     = time.time()
        elapsed = now - self._start_time

        readings = [w.read() for w in self._wells]
        reports  = {r.well_id: self._detector.evaluate_from_reading(r)
                    for r in readings}

        # Push data into buffers
        self._times.append(elapsed)
        for r in readings:
            rpt = reports[r.well_id]
            self._data[r.well_id]["temp"].append(r.temperature_c)
            self._data[r.well_id]["pres"].append(r.pressure_bar)
            self._data[r.well_id]["flow"].append(r.flow_m3h)
            self._data[r.well_id]["risk"].append(rpt.risk_score)

        xs = list(self._times)

        # System-level health
        max_risk = max(
            self._data[wid]["risk"][-1] for wid in self._well_ids
            if self._data[wid]["risk"]
        )
        if max_risk >= RISK_CRIT_LEVEL:
            health_str = "CRITICAL"
            h_color    = CLR_HI_HI
        elif max_risk >= RISK_WARN_LEVEL:
            health_str = "WARNING"
            h_color    = "#ffc400"
        else:
            health_str = "NOMINAL"
            h_color    = CLR_NOMINAL

        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        up = int(elapsed)
        up_str = f"{up // 3600:02d}:{(up % 3600)//60:02d}:{up % 60:02d}"
        self._title.set_text(
            f"  DIKILI GEOTHERMAL SCADA  |  MONITORING DASHBOARD"
            f"  |  {ts}  |  UP {up_str}  |  CYCLE #{self._cycle:05d}"
            f"  |  STATUS: {health_str}  |  RISK: {max_risk:.0f}/100"
        )
        self._title.set_color(h_color if health_str != "NOMINAL" else TEXT_CLR)

        updated = []
        for key, ax in self._axes.items():
            for wid in self._well_ids:
                ys = list(self._data[wid][key])
                if not ys:
                    continue
                line = self._lines[key][wid]
                line.set_data(xs[-len(ys):], ys)

                # Remove old fill and redraw
                if self._fills[key][wid] is not None:
                    self._fills[key][wid].remove()
                    self._fills[key][wid] = None

                color = WELL_COLORS.get(wid, "#ffffff")
                baseline = 0.0 if key == "risk" else (
                    ax.get_ylim()[0]
                )
                fill = ax.fill_between(
                    xs[-len(ys):], baseline, ys,
                    color=color, alpha=FILL_ALPHA, zorder=2,
                )
                self._fills[key][wid] = fill
                updated.append(line)

            # Slide x-axis window
            if xs:
                span = max(xs[-1] - xs[0], 10)
                ax.set_xlim(xs[0], xs[-1] + span * 0.02)
                # Format x-axis as elapsed seconds
                ax.set_xlabel("Elapsed  (s)", fontsize=7.5, labelpad=2)

        self._fig.canvas.draw_idle()
        return updated


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    dash = SCADAPlotDashboard(
        well_ids      = ["GW-01", "GW-02", "GW-03"],
        scan_interval = 2.0,
        max_points    = 90,
    )
    dash.run()
