"""
gui/trend_charts.py
===================
Embedded matplotlib trend charts for the graphical SCADA interface.
Supports Live Rolling mode and Historical Query mode.
"""

from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timedelta

import matplotlib  # type: ignore
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.dates as mdates # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # type: ignore
from matplotlib.figure import Figure  # type: ignore
import numpy as np

import tkinter as tk

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, GRID_LINE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    WELL_COLORS,
    FONT_LABEL_SM,
)

# Process thresholds for reference lines
_T_HI = 105.0;  _T_LO = 78.0
_P_LO = 4.5
_Q_LO = 80.0
_RISK_WARN = 40.0;  _RISK_CRIT = 70.0

# Rolling buffer size
_MAX_POINTS = 45000  # 25 hours at 2-second scans


class TrendChartPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, well_ids: list[str] | None = None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        if well_ids is None:
            well_ids = ["W-01", "W-02", "W-03"]
        self._well_ids = well_ids
        self._mode = "LIVE"
        self._live_window_minutes = 60
        self._bg_cache = None

        # ── Rolling data buffers ───────────────────────────────────────────
        self._times: deque[datetime] = deque(maxlen=_MAX_POINTS)
        self._data: dict[str, dict[str, deque]] = {
            wid: {
                "temp": deque(maxlen=_MAX_POINTS),
                "pres": deque(maxlen=_MAX_POINTS),
                "flow": deque(maxlen=_MAX_POINTS),
                "risk": deque(maxlen=_MAX_POINTS),
                "health": deque(maxlen=_MAX_POINTS),
                "conf": deque(maxlen=_MAX_POINTS),
            }
            for wid in well_ids
        }

        # ── Create Qt-equivalent layout with Tkinter ──────────────────────────────────────
        grid_frame = tk.Frame(self, bg=BG_PRIMARY)
        grid_frame.pack(fill="both", expand=True)
        for i in range(2): grid_frame.rowconfigure(i, weight=1)
        for j in range(3): grid_frame.columnconfigure(j, weight=1)

        specs = [
            ("temp",   "TEMPERATURE",      "°C",   (70, 112), [(_T_HI, CLR_CRITICAL), (100.0, CLR_WARNING)]),
            ("pres",   "PRESSURE",         "bar",  (2, 13),   [(_P_LO, CLR_WARNING), (3.5, CLR_CRITICAL)]),
            ("flow",   "FLOW RATE",        "m³/h", (40, 310), [(_Q_LO, CLR_WARNING), (60.0, CLR_CRITICAL)]),
            ("risk",   "AI FAILURE RISK",  "%",    (-2, 102), [(_RISK_WARN, CLR_WARNING), (_RISK_CRIT, CLR_CRITICAL)]),
            ("health", "EQUIPMENT HEALTH", "%",    (-2, 102), [(50.0, CLR_CRITICAL), (80.0, CLR_WARNING)]),
            ("conf",   "AI CONFIDENCE",    "%",    (-2, 102), [(70.0, CLR_WARNING), (50.0, CLR_CRITICAL)]),
        ]
        self._specs = specs

        self._axes: dict[str, plt.Axes] = {}
        self._lines: dict[str, dict[str, object]] = {}
        self._kpi_texts: dict[str, dict[str, object]] = {}
        self._canvases = {}
        self._figs = {}
        self._chart_frames = {}

        for idx, (key, title, unit, ylim, thresholds) in enumerate(specs):
            row = idx // 3
            col = idx % 3
            
            c_frame = tk.Frame(grid_frame, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
            c_frame.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            self._chart_frames[key] = c_frame
            
            lbl_title = tk.Label(c_frame, text=title, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"), anchor="w")
            lbl_title.pack(side="top", fill="x", padx=8, pady=(4, 0))
            
            # Figure mapping to expanding canvas
            fig = Figure(dpi=100)
            fig.subplots_adjust(left=0.12, right=0.98, top=0.90, bottom=0.20)
            fig.patch.set_facecolor(BG_SECONDARY)
            self._figs[key] = fig
            
            ax = fig.add_subplot(1, 1, 1)
            ax.set_facecolor(BG_SECONDARY)
            ax.set_ylim(*ylim)
            ax.set_ylabel(unit, fontsize=10, color=TEXT_SECONDARY, labelpad=4)
            ax.tick_params(colors=TEXT_MUTED, labelsize=9)
            
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
            
            ax.grid(True, color=GRID_LINE, linestyle="--", linewidth=0.5, alpha=0.2)
            for spine in ax.spines.values(): spine.set_color(BORDER)
            
            for level, color in thresholds:
                label_txt = f"Warning Threshold ({level} {unit})" if color == CLR_WARNING else f"Critical Threshold ({level} {unit})"
                ax.axhline(level, color=color, linewidth=1.5, linestyle="--", alpha=0.6, label=label_txt)
                
            self._lines[key] = {}
            for wid in well_ids:
                color = WELL_COLORS.get(wid, "#ffffff")
                line, = ax.plot([], [], color=color, linewidth=2.5, alpha=0.9, label=wid, antialiased=True)
                self._lines[key][wid] = line
                
            ax.legend(fontsize=8, loc="upper left", facecolor=BG_HEADER, edgecolor=BORDER, labelcolor=TEXT_SECONDARY, framealpha=0.5)
            self._axes[key] = ax
            
            canvas = FigureCanvasTkAgg(fig, master=c_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side="top", fill="both", expand=True)
            self._canvases[key] = canvas
            
            stats_frame = tk.Frame(c_frame, bg=BG_SECONDARY)
            stats_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 4))
            
            self._kpi_texts[key] = {}
            for wid in well_ids:
                color = WELL_COLORS.get(wid, TEXT_PRIMARY)
                lbl = tk.Label(stats_frame, text=f"{wid} Cur: -- Avg: -- Min: -- Max: -- Std: --", bg=BG_SECONDARY, fg=color, font=("Consolas", 9), anchor="w")
                lbl.pack(side="top", fill="x")
                self._kpi_texts[key][wid] = lbl
                
        self.pack_propagate(False)
        
        # Navigation Toolbar
        toolbar_frame = tk.Frame(self, bg="#0f172a")
        toolbar_frame.pack(fill="x", side="bottom")
        self._toolbar = NavigationToolbar2Tk(self._canvas, toolbar_frame)
        self._toolbar.config(background="#0f172a")
        self._toolbar._message_label.config(background="#0f172a", foreground="#f8fafc", font=("Segoe UI", 8))
        for button in self._toolbar.winfo_children():
            button.config(background="#0f172a")
        self._toolbar.update()
        
        # Custom Export CSV Button
        btn_csv = tk.Button(toolbar_frame, text="Export CSV", bg="#334155", fg="#f8fafc", bd=0, padx=5, font=("Segoe UI", 8), command=self._export_csv)
        btn_csv.pack(side="right", padx=5, pady=2)
        
        # Custom Fullscreen Button
        btn_fs = tk.Button(toolbar_frame, text="Fullscreen", bg="#334155", fg="#f8fafc", bd=0, padx=5, font=("Segoe UI", 8), command=self._toggle_fullscreen)
        btn_fs.pack(side="right", padx=5, pady=2)
        
        # Hover Tooltip & Crosshair
        self._annot = {}
        self._vlines = {}
        self._hlines = {}
        for key, ax in self._axes.items():
            self._annot[key] = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                bbox=dict(boxstyle="round", fc=BG_HEADER, ec=BORDER, alpha=0.9),
                arrowprops=dict(arrowstyle="->", color=TEXT_SECONDARY), color=TEXT_PRIMARY, fontsize=7)
            self._annot[key].set_visible(False)
            self._vlines[key] = ax.axvline(x=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
            self._hlines[key] = ax.axhline(y=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
        
        for c in self._canvases.values():
            c.mpl_connect("motion_notify_event", self._on_hover)
            c.mpl_connect("button_press_event", self._on_click)
            c.mpl_connect("scroll_event", self._on_scroll)
            c.mpl_connect("button_press_event", self._on_press)
            c.mpl_connect("button_release_event", self._on_release)
            c.mpl_connect("button_press_event", self._on_double_click)

        self.on_chart_click_cb = None
        self._is_panning = False
        self._pan_start_x = None
        self._pan_start_xlims = {}
        self._auto_scale_y = True

        self.after(100, self._draw_all_canvases)

    def _draw_all_canvases(self):
        for c in self._canvases.values(): c.draw_idle()

    def _on_click(self, event):
        # We only care about left click (button 1), ignoring dragging clicks if possible.
        # Simple click check:
        if event.button == 1 and event.inaxes:
            for key, ax in self._axes.items():
                if ax == event.inaxes:
                    if hasattr(self, "on_chart_click_cb") and self.on_chart_click_cb:
                        title = next((t[1] for t in self._specs if t[0] == key), key)
                        self.on_chart_click_cb(key, title)
                    break

    def set_live_window_minutes(self, minutes: int):
        self._live_window_minutes = minutes
        self._bg_cache = None
        self._draw_all_canvases()

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == "LIVE":
            for key, lines_dict in self._lines.items():
                for line in lines_dict.values():
                    line.set_data([], [])
            self._draw_all_canvases()

    def set_line_visibility(self, states: dict[str, bool]):
        # States: { "W-01": True, ... }
        for key in ["temp", "pres", "flow", "risk", "health", "conf"]:
            ax = self._axes[key]
            
            for wid, visible in states.items():
                if wid in self._lines[key]:
                    self._lines[key][wid].set_visible(visible)
                if wid in self._kpi_texts[key]:
                    if visible:
                        self._kpi_texts[key][wid].pack(side="top", fill="x")
                    else:
                        self._kpi_texts[key][wid].pack_forget()
            
            handles, labels = [], []
            for line in ax.lines:
                if line.get_linestyle() == "--" and "Threshold" in str(line.get_label()):
                    handles.append(line)
                    labels.append(line.get_label())
            for wid in self._well_ids:
                if states.get(wid, True) and wid in self._lines[key]:
                    handles.append(self._lines[key][wid])
                    labels.append(wid)
            if ax.get_legend(): ax.get_legend().remove()
            if handles: ax.legend(handles, labels, fontsize=8, loc="upper left", facecolor=BG_HEADER, edgecolor=BORDER, labelcolor=TEXT_SECONDARY, framealpha=0.5)
                
        self._draw_all_canvases()

    def _update_kpis(self, key: str, wid: str, y_data: list):
        if not y_data:
            self._kpi_texts[key][wid].set_text(f"{wid}\\nNo Data")
            return
        valid_y = [v for v in y_data if v is not None and not np.isnan(v)]
        if not valid_y:
            self._kpi_texts[key][wid].set_text(f"{wid}\\nNo Data")
            return
            
        cur_val = valid_y[-1]
        avg_val = np.mean(valid_y)
        min_val = np.min(valid_y)
        max_val = np.max(valid_y)
        std_val = np.std(valid_y)
        
        # Trend Direction
        trend = "►"
        if len(valid_y) >= 5:
            recent = valid_y[-5:]
            slope = np.polyfit(range(len(recent)), recent, 1)[0]
            if slope > (0.01 * cur_val): trend = "▲"
            elif slope < (-0.01 * cur_val): trend = "▼"
            
        unit = next((u for k, t, u, l, th in self._specs if k == key), "")
        unit_str = f" {unit}" if unit else ""
        stat_text = f"{wid:<5} Cur: {cur_val:6.1f}{unit_str:<4} {trend}  Avg: {avg_val:6.1f}  Min: {min_val:6.1f}  Max: {max_val:6.1f}  Std: {std_val:5.2f}"
        self._kpi_texts[key][wid].config(text=stat_text)

    def initialize_history(self, history_data: list[dict]):
        """Injects past history into the LIVE rolling buffer so the chart is full at startup."""
        if not history_data:
            return
            
        # Group by well
        for row in history_data:
            wid = row.get('well_id')
            if wid in self._data:
                dt = datetime.fromisoformat(row['timestamp'].replace("Z", "+00:00"))
                t = mdates.date2num(dt)
                
                # Only append if we haven't already filled the buffer, to prevent overflow if they pass too much
                # But since it's a deque, it will just roll. However, we want times to match.
                # Actually, wait. We need a unified time list for `self._times`. 
                pass
                
        # To keep it simple, since historical rows arrive grouped by time, 
        # let's extract unique times, sort them, and fill the deques.
        times_map = {}
        for row in history_data:
            ts_str = row['timestamp'].replace("Z", "")
            if "+" in ts_str: ts_str = ts_str.split("+")[0]
            dt = datetime.fromisoformat(ts_str)
            t = mdates.date2num(dt)
            if t not in times_map:
                times_map[t] = {}
            times_map[t][row.get('well_id')] = row

        sorted_times = sorted(times_map.keys())
        
        # Only keep the last _MAX_POINTS
        sorted_times = sorted_times[-_MAX_POINTS:]
        
        self._times.clear()
        for wid in self._well_ids:
            for key in self._data[wid]:
                self._data[wid][key].clear()
                
        global_conf = 85.0 # fallback
        
        last_risk = {wid: 15.0 for wid in self._well_ids}
        last_health = {wid: 95.0 for wid in self._well_ids}
        last_conf = {wid: global_conf for wid in self._well_ids}
                
        prev_t = None
        for t in sorted_times:
            if prev_t is not None and (t - prev_t) > (2.0 / (24.0 * 60.0)):
                self._times.append(prev_t + 1.0/(24.0*60.0*60.0))
                for wid in self._well_ids:
                    self._data[wid]["temp"].append(np.nan)
                    self._data[wid]["pres"].append(np.nan)
                    self._data[wid]["flow"].append(np.nan)
                    self._data[wid]["risk"].append(np.nan)
                    self._data[wid]["health"].append(np.nan)
                    self._data[wid]["conf"].append(np.nan)
            prev_t = t
            
            self._times.append(t)
            row_map = times_map[t]
            for wid in self._well_ids:
                row = row_map.get(wid, {})
                
                self._data[wid]["temp"].append(row.get('temperature_c', np.nan))
                self._data[wid]["pres"].append(row.get('pressure_bar', np.nan))
                self._data[wid]["flow"].append(row.get('flow_m3h', np.nan))
                
                # Use base values if provided, otherwise random walk from last known
                risk = row.get('risk_score', last_risk[wid])
                health = row.get('health_score', last_health[wid])
                conf = row.get('confidence', last_conf[wid])
                
                # Do not fabricate data with random noise, use provided base values
                risk = max(0.0, min(100.0, risk))
                health = max(0.0, min(100.0, health))
                conf = max(0.0, min(100.0, conf))
                
                self._data[wid]["risk"].append(risk)
                self._data[wid]["health"].append(health)
                self._data[wid]["conf"].append(conf)
                
                last_risk[wid] = risk
                last_health[wid] = health
                last_conf[wid] = conf
                
        # Draw the initialized data
        for key in ["temp", "pres", "flow", "risk", "health", "conf"]:
            for wid in self._well_ids:
                if wid in self._lines[key]:
                    self._lines[key][wid].set_data(list(self._times), list(self._data[wid][key]))
            self._auto_scale_y_axis(key)
            
        self._canvas.draw_idle()

    def plot_historical_data(self, data: list[dict]):
        # Clear out empty axes handling text
        for ax in self._axes.values():
            for txt in ax.texts:
                if txt.get_text() == "No historical data available for the selected period.":
                    txt.remove()
                    
        if not data:
            # Empty Data Handling
            for ax in self._axes.values():
                ax.text(0.5, 0.5, "No historical data available for the selected period.", transform=ax.transAxes, ha="center", va="center", color=TEXT_MUTED, fontsize=8)
            self._draw_all_canvases()
            return
            
        self._mode = "HISTORICAL"
        
        # Group by well_id
        hist_data = {wid: {"times": [], "temp": [], "pres": [], "flow": [], "risk": [], "health": [], "conf": []} for wid in self._well_ids}
        
        for row in data:
            wid = row.get('well_id')
            if wid in hist_data:
                # Convert ISO string to matplotlib date float
                ts_str = row['timestamp'].replace("Z", "")
                if "+" in ts_str: ts_str = ts_str.split("+")[0]
                dt = datetime.fromisoformat(ts_str)
                t = mdates.date2num(dt)
                
                if len(hist_data[wid]["times"]) > 0:
                    prev_t = hist_data[wid]["times"][-1]
                    if (t - prev_t) > (2.0 / (24.0 * 60.0)):
                        hist_data[wid]["times"].append(prev_t + 1.0/(24.0*60.0*60.0))
                        hist_data[wid]["temp"].append(np.nan)
                        hist_data[wid]["pres"].append(np.nan)
                        hist_data[wid]["flow"].append(np.nan)
                        hist_data[wid]["risk"].append(np.nan)
                        hist_data[wid]["health"].append(np.nan)
                        hist_data[wid]["conf"].append(np.nan)
                
                hist_data[wid]["times"].append(t)
                hist_data[wid]["temp"].append(row.get('temperature_c', np.nan))
                hist_data[wid]["pres"].append(row.get('pressure_bar', np.nan))
                hist_data[wid]["flow"].append(row.get('flow_m3h', np.nan))
                # For historian, if risk/health/conf aren't in row, pad with NaN
                hist_data[wid]["risk"].append(row.get('risk_score', np.nan))
                hist_data[wid]["health"].append(row.get('health_score', np.nan))
                hist_data[wid]["conf"].append(row.get('confidence', np.nan))

        t_all = []
        for wid in self._well_ids:
            if hist_data[wid]["times"]:
                t_all.extend(hist_data[wid]["times"])
        
        if not t_all:
            return
            
        t_min = min(t_all)
        t_max = max(t_all)

        for key in ["temp", "pres", "flow", "risk", "health", "conf"]:
            for wid in self._well_ids:
                if len(hist_data[wid]["times"]) > 0:
                    self._lines[key][wid].set_data(hist_data[wid]["times"], hist_data[wid][key])
                    self._update_kpis(key, wid, hist_data[wid][key])
            
            # Add a bit of padding to X axis
            pad = (t_max - t_min) * 0.05 if t_max > t_min else 0.01
            self._axes[key].set_xlim(t_min - pad, t_max + pad)
            
            self._auto_scale_y_axis(key)

        self._draw_all_canvases()

    def _auto_scale_y_axis(self, key):
        if not self._auto_scale_y: return
        ax = self._axes[key]
        
        # Get threshold values
        thresholds = next((t for k, _, _, _, t in self._specs if k == key), [])
        
        all_y = []
        for wid in self._well_ids:
            line = self._lines[key].get(wid)
            if line and line.get_visible():
                ydata = [y for y in line.get_ydata() if not np.isnan(y)]
                all_y.extend(ydata)
        
        if not all_y: return
        
        min_y, max_y = min(all_y), max(all_y)
        range_y = max_y - min_y
        
        thresh_list = [t[0] for t in thresholds]
        fixed_min = min(thresh_list) if thresh_list else min_y
        fixed_max = max(thresh_list) if thresh_list else max_y
        
        if range_y == 0:
            pad = max(abs(min_y) * 0.1, 1.0)
            target_min = min(min_y - pad, fixed_min)
            target_max = max(max_y + pad, fixed_max)
        else:
            pad = range_y * 0.20
            target_min = min(min_y - pad, fixed_min)
            target_max = max(max_y + pad, fixed_max)
            
        if target_max < fixed_max:
            target_max = fixed_max + (fixed_max - target_min) * 0.10
        if target_min > fixed_min:
            target_min = fixed_min - (target_max - fixed_min) * 0.10

        ax.set_ylim(target_min, target_max)

    # ── Interactive Zoom & Pan ──────────────────────────────────────
    def _on_scroll(self, event):
        if not event.inaxes: return
        ax = event.inaxes
        
        # Stop auto-scrolling if user zooms manually
        self._auto_scale_y = False

        cur_xlim = ax.get_xlim()
        cur_xrange = cur_xlim[1] - cur_xlim[0]
        
        xdata = event.xdata
        if event.button == 'up':
            scale_factor = 0.8 # Zoom in
        elif event.button == 'down':
            scale_factor = 1.2 # Zoom out
        else:
            scale_factor = 1.0
            
        new_xrange = cur_xrange * scale_factor
        
        # Keep cursor position stationary
        ratio = (xdata - cur_xlim[0]) / cur_xrange
        new_xmin = xdata - new_xrange * ratio
        new_xmax = xdata + new_xrange * (1 - ratio)
        
        for axes in self._axes.values():
            axes.set_xlim(new_xmin, new_xmax)
            
        self._draw_all_canvases()

    def _on_press(self, event):
        if event.dblclick:
            return # Handled in double click
        if event.button == 1 and event.inaxes: # Left click
            self._is_panning = True
            self._pan_start_x = event.xdata
            for k, ax in self._axes.items():
                self._pan_start_xlims[k] = ax.get_xlim()

    def _on_release(self, event):
        if event.button == 1:
            self._is_panning = False

    def _on_double_click(self, event):
        if event.dblclick and event.button == 1:
            self._auto_scale_y = True
            if self._mode == "HISTORICAL":
                # Reset to full historical bounds
                pass # Ideally we would store global limits
            else:
                # Let LIVE mode auto-scroll naturally again
                pass
            
            for key in self._axes.keys():
                self._auto_scale_y_axis(key)
                
            self._draw_all_canvases()

    def _on_hover(self, event):
        if self._is_panning and event.button == 1 and event.xdata and self._pan_start_x:
            # Perform Panning
            dx = event.xdata - self._pan_start_x
            for k, ax in self._axes.items():
                xlim = self._pan_start_xlims[k]
                ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
            self._draw_all_canvases()
            return
            
        hover_key = None
        for key, ax in self._axes.items():
            if ax == event.inaxes:
                hover_key = key
                break
                
        # Hover Visual Effects
        if hover_key:
            self._canvases[hover_key].get_tk_widget().config(cursor="hand2")
            for key, ax in self._axes.items():
                if ax == event.inaxes:
                    ax.set_facecolor("#2a2a35") # Brightened BG
                    for spine in ax.spines.values():
                        spine.set_color("#3b82f6") # Blue highlight
                        spine.set_linewidth(1.5)
                else:
                    ax.set_facecolor(BG_SECONDARY)
                    for spine in ax.spines.values():
                        spine.set_color(BORDER)
                        spine.set_linewidth(1.0)
                        
            ax = event.inaxes
            self._annot[hover_key].set_visible(False)
            
            # Find closest line
            min_dist = float('inf')
            closest_point = None
            closest_label = None
            unit = ax.get_ylabel()
            
            for line in ax.get_lines():
                if not line.get_visible() or "Threshold" in str(line.get_label()): continue
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                if len(xdata) == 0: continue
                
                # Check distances
                idx = np.abs(np.array(xdata) - event.xdata).argmin()
                px, py = xdata[idx], ydata[idx]
                if np.isnan(py): continue
                
                if abs(event.xdata - px) < (ax.get_xlim()[1] - ax.get_xlim()[0])*0.05:
                    if abs(event.ydata - py) < min_dist:
                        min_dist = abs(event.ydata - py)
                        closest_point = (px, py)
                        closest_label = line.get_label()

            if closest_point and min_dist < (ax.get_ylim()[1] - ax.get_ylim()[0])*0.15:
                # Update Crosshairs
                for key, vl in self._vlines.items():
                    vl.set_xdata([closest_point[0], closest_point[0]])
                    if key == hover_key: vl.set_alpha(0.6)
                
                for key, hl in self._hlines.items():
                    if key == hover_key:
                        hl.set_ydata([closest_point[1], closest_point[1]])
                        hl.set_alpha(0.6)
                    else:
                        hl.set_alpha(0.0)
                        
                self._annot[hover_key].xy = closest_point
                
                dt = mdates.num2date(closest_point[0])
                time_str = dt.strftime('%H:%M:%S')
                val = closest_point[1]
                
                # Determine status
                status = "Normal"
                thresholds = next((t for k, _, _, _, t in self._specs if k == hover_key), [])
                for level, color in thresholds:
                    if color == CLR_CRITICAL:
                        if (val >= level and level > np.mean(ax.get_ylim())) or (val <= level and level < np.mean(ax.get_ylim())): status = "Critical"
                    elif color == CLR_WARNING and status == "Normal":
                        if val >= level and level > np.mean(ax.get_ylim()): status = "Warning"
                        elif val <= level and level < np.mean(ax.get_ylim()): status = "Warning"

                self._annot[hover_key].set_text(f"{time_str}\n{closest_label}\n{val:.1f} {unit}\nStatus: {status}")
                self._annot[hover_key].set_visible(True)
                
            self._draw_all_canvases()
        else:
            for c in self._canvases.values(): c.get_tk_widget().config(cursor="")
            for ax in self._axes.values():
                ax.set_facecolor(BG_SECONDARY)
                for spine in ax.spines.values():
                    spine.set_color(BORDER)
                    spine.set_linewidth(1.0)
            
            for ann in self._annot.values():
                if ann.get_visible():
                    ann.set_visible(False)
            for vl in self._vlines.values(): vl.set_alpha(0.0)
            for hl in self._hlines.values(): hl.set_alpha(0.0)
            self._draw_all_canvases()

    def update_data(self, readings: list, reports: dict, ai_result: dict = None, rul_results: dict = None, health_indexes: dict = None):
        if self._mode != "LIVE" or not readings: return

        now = datetime.now()
        t = mdates.date2num(now)
        
        if len(self._times) > 0:
            prev_t = self._times[-1]
            if (t - prev_t) > (2.0 / (24.0 * 60.0)):
                self._times.append(prev_t + 1.0/(24.0*60.0*60.0))
                for wid in self._well_ids:
                    self._data[wid]["temp"].append(np.nan)
                    self._data[wid]["pres"].append(np.nan)
                    self._data[wid]["flow"].append(np.nan)
                    self._data[wid]["risk"].append(np.nan)
                    self._data[wid]["health"].append(np.nan)
                    self._data[wid]["conf"].append(np.nan)
                    
        self._times.append(t)

        # Build a dict of the newest reading for each well in this batch
        latest_readings = {r.well_id: r for r in readings}

        # Global AI result parsing for fallback
        global_conf = ai_result.get("Prediction Confidence (%)", 0.0) if ai_result else 0.0

        for wid in self._well_ids:
            if wid in self._data:
                if wid in latest_readings:
                    r = latest_readings[wid]
                    self._data[wid]["temp"].append(r.temperature_c)
                    self._data[wid]["pres"].append(r.pressure_bar)
                    self._data[wid]["flow"].append(r.flow_m3h)
                else:
                    self._data[wid]["temp"].append(np.nan)
                    self._data[wid]["pres"].append(np.nan)
                    self._data[wid]["flow"].append(np.nan)
                    
                # Derive per-well AI metrics
                risk = 0.0
                health = 100.0
                conf = global_conf
                
                if reports and wid in reports:
                    risk = reports[wid].risk_score
                    health = 100.0 - risk # Fallback health proxy
                
                if health_indexes and wid in health_indexes:
                    health = health_indexes[wid]
                    
                if rul_results and wid in rul_results:
                    conf = rul_results[wid].get("Confidence (%)", global_conf)
                


                self._data[wid]["risk"].append(risk)
                self._data[wid]["health"].append(health)
                self._data[wid]["conf"].append(conf)

        for key in ["temp", "pres", "flow", "risk", "health", "conf"]:
            for wid in self._well_ids:
                if wid in self._lines[key]:
                    self._lines[key][wid].set_data(list(self._times), list(self._data[wid][key]))
                    if self._lines[key][wid].get_visible():
                        self._update_kpis(key, wid, list(self._data[wid][key]))
            
            self._auto_scale_y_axis(key)

        # Auto-scroll X axis for LIVE
        t_max = t
        t_min = t_max - (self._live_window_minutes * 60.0 / 86400.0)
        
        needs_full_redraw = False
        if not self._is_panning:
            for ax in self._axes.values():
                old_min, old_max = ax.get_xlim()
                if t_max > old_max:
                    # Advance the window by 10% to prevent continuous full redraws
                    window = t_max - t_min
                    ax.set_xlim(t_min, t_max + window * 0.1)
                    needs_full_redraw = True

        if self._bg_cache is None or needs_full_redraw:
            for c in self._canvases.values(): c.draw()
            self._bg_cache = {k: c.copy_from_bbox(self._figs[k].bbox) for k, c in self._canvases.items()}
        else:
            for key in ["temp", "pres", "flow", "risk", "health", "conf"]:
                c = self._canvases[key]
                fig = self._figs[key]
                ax = self._axes[key]
                
                c.restore_region(self._bg_cache[key])
                for wid in self._well_ids:
                    if self._lines[key][wid].get_visible():
                        ax.draw_artist(self._lines[key][wid])
                c.blit(fig.bbox)
                c.flush_events()

    def export_image(self, format="png"):
        import os
        from tkinter import filedialog, messagebox
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=[(f"{format.upper()} files", f"*.{format}")],
            title=f"Export Chart as {format.upper()}"
        )
        if filename:
            try:
                # We can't export a single figure anymore. We must combine them or save the widget.
                # For simplicity, save the whole frame.
                import pyscreenshot as ImageGrab
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()
                img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                img.save(filename)
                messagebox.showinfo("Export Success", f"Chart exported to:\n{os.path.abspath(filename)}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export image: {e}")

    def get_visible_data(self):
        """Returns the currently visible data for exporting to CSV."""
        export_data = []
        import matplotlib.dates as mdates
        import pandas as pd
        
        # We need a unified timestamp list. The simplest is to gather all times and align them, 
        # but since LIVE mode appends synchronously and HISTORICAL sets it cleanly, 
        # we can just zip them.
        for wid in self._well_ids:
            if not self._lines["temp"][wid].get_visible():
                continue # Skip unchecked wells
            
            xdata = self._lines["temp"][wid].get_xdata()
            if not len(xdata): continue
            
            # Find the indices that fall within the current X-axis limits
            ax = self._axes["temp"]
            xmin, xmax = ax.get_xlim()
            
            for i, x in enumerate(xdata):
                if xmin <= x <= xmax:
                    dt = mdates.num2date(x)
                    row = {
                        "Timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "Well Name": wid,
                        "Temperature": self._data[wid]["temp"][i] if self._mode == "LIVE" else self._lines["temp"][wid].get_ydata()[i],
                        "Pressure": self._data[wid]["pres"][i] if self._mode == "LIVE" else self._lines["pres"][wid].get_ydata()[i],
                        "Flow Rate": self._data[wid]["flow"][i] if self._mode == "LIVE" else self._lines["flow"][wid].get_ydata()[i],
                        "AI Failure Risk": self._data[wid]["risk"][i] if self._mode == "LIVE" else self._lines["risk"][wid].get_ydata()[i],
                        "Equipment Health": self._data[wid]["health"][i] if self._mode == "LIVE" else self._lines["health"][wid].get_ydata()[i],
                        "AI Confidence": self._data[wid]["conf"][i] if self._mode == "LIVE" else self._lines["conf"][wid].get_ydata()[i],
                    }
                    export_data.append(row)
        return export_data

    def _toggle_fullscreen(self):
        if hasattr(self, '_fs_win') and self._fs_win.winfo_exists():
            self._fs_win.destroy()
            return
            
        self._fs_win = tk.Toplevel(self)
        self._fs_win.title("Fullscreen Charts")
        self._fs_win.state('zoomed')
        from gui.theme import BG_PRIMARY
        self._fs_win.configure(bg=BG_PRIMARY)
        
        fs_panel = TrendChartPanel(self._fs_win, well_ids=self._well_ids)
        fs_panel.pack(fill=tk.BOTH, expand=True)
        fs_panel._times = self._times.copy()
        fs_panel._data = self._data
        fs_panel._update_lines()
        
    def _export_csv(self):
        import csv
        import tkinter.filedialog as fd
        import tkinter.messagebox as messagebox
        
        path = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Export Chart Data")
        if not path: return
        
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                header = ["Timestamp"]
                for wid in self._well_ids:
                    header.extend([f"{wid}_Temp", f"{wid}_Pres", f"{wid}_Flow"])
                writer.writerow(header)
                
                for i, t in enumerate(self._times):
                    row = [t.isoformat()]
                    for wid in self._well_ids:
                        try:
                            row.extend([
                                self._data[wid]["temp"][i],
                                self._data[wid]["pres"][i],
                                self._data[wid]["flow"][i]
                            ])
                        except IndexError:
                            row.extend(["", "", ""])
                    writer.writerow(row)
            messagebox.showinfo("Export Successful", f"Chart data exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
