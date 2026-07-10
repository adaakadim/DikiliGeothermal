"""
gui/trend_detail_chart.py
=========================
A large, single-chart Matplotlib component for the Trend Detail View.
"""

from __future__ import annotations
from collections import deque
from datetime import datetime
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import tkinter as tk

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, GRID_LINE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_CRITICAL, CLR_WARNING, WELL_COLORS
)

# Shared constants
_MAX_POINTS = 1800

class TrendDetailChartPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, chart_key: str, spec: tuple, well_ids: list[str], **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        self._chart_key = chart_key
        self._title = spec[1]
        self._unit = spec[2]
        self._ylim = spec[3]
        self._thresholds = spec[4]
        self._well_ids = well_ids
        
        self._is_live = True
        self._live_times_ref = None
        self._live_data_ref = None
        
        self._hist_times = []
        self._hist_data = {wid: [] for wid in well_ids}
        
        # Build Figure
        self._fig = Figure(figsize=(10, 6), dpi=90)
        self._fig.patch.set_facecolor(BG_PRIMARY)
        self._fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)
        
        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.set_facecolor(BG_SECONDARY)
        self._ax.set_ylim(*self._ylim)
        self._ax.set_title(self._title, fontsize=12, fontweight="bold", color=TEXT_PRIMARY, pad=10, loc="left")
        self._ax.set_ylabel(self._unit, fontsize=10, color=TEXT_SECONDARY, labelpad=5)
        self._ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        self._ax.grid(True, color=GRID_LINE, linestyle="--", linewidth=0.5, alpha=0.4)
        
        for spine in self._ax.spines.values():
            spine.set_color(BORDER)
            spine.set_linewidth(1.0)
            
        self._date_formatter = mdates.DateFormatter('%H:%M:%S')
        locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
        self._ax.xaxis.set_major_locator(locator)
        self._ax.xaxis.set_major_formatter(self._date_formatter)
        
        # Lines
        self._lines = {}
        for wid in well_ids:
            color = WELL_COLORS.get(wid, TEXT_PRIMARY)
            line, = self._ax.plot([], [], color=color, linewidth=1.5, label=wid, solid_capstyle="round")
            self._lines[wid] = line
            
        # Thresholds
        for level, color in self._thresholds:
            label_txt = f"Warning Threshold ({level} {self._unit})" if color == CLR_WARNING else f"Critical Threshold ({level} {self._unit})"
            self._ax.axhline(level, color=color, linewidth=1.0, linestyle="--", alpha=0.6, label=label_txt)
            
        self._ax.legend(fontsize=9, loc="upper right", facecolor=BG_HEADER, edgecolor=BORDER, labelcolor=TEXT_SECONDARY, framealpha=0.9)
        
        # GUI Embedding
        self.pack_propagate(False)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.pack(fill="both", expand=True)
        
        toolbar_frame = tk.Frame(self, bg=BG_PRIMARY)
        toolbar_frame.pack(fill="x", side="bottom")
        self._toolbar = NavigationToolbar2Tk(self._canvas, toolbar_frame)
        self._toolbar.update()
        
        from gui.theme import style_matplotlib_toolbar
        style_matplotlib_toolbar(self._toolbar)
        
        # Hover setup
        self._annot = self._ax.annotate(
            "", xy=(0,0), xytext=(15,15), textcoords="offset points",
            bbox=dict(boxstyle="round", fc=BG_HEADER, ec=BORDER, alpha=0.95),
            arrowprops=dict(arrowstyle="->", color=TEXT_SECONDARY),
            color=TEXT_PRIMARY, fontsize=9
        )
        self._annot.set_visible(False)
        self._vline = self._ax.axvline(x=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
        self._hline = self._ax.axhline(y=0, color=TEXT_MUTED, linestyle=":", alpha=0.0, zorder=0)
        
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_hover)
        
        self._auto_scale_y = True
        self._is_panning = False
        self._pan_start_x = None
        self._pan_start_xlim = None
        self._fig.canvas.mpl_connect("scroll_event", self._on_scroll)
        self._fig.canvas.mpl_connect("button_press_event", self._on_press)
        self._fig.canvas.mpl_connect("button_release_event", self._on_release)
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_pan)
        self._fig.canvas.mpl_connect("draw_event", self._on_draw)
        
    def get_figure(self):
        return self._fig
        
    def initialize_from_live(self, times_ref, data_ref):
        self._is_live = True
        self._live_times_ref = times_ref
        self._live_data_ref = data_ref
        self._update_all_lines(auto_scroll=True)
        
    def sync_live_view(self):
        if self._is_live:
            self._update_all_lines(auto_scroll=True)
            
    def plot_historical_data(self, history_data):
        self._is_live = False
        self._hist_times.clear()
        for wid in self._well_ids:
            self._hist_data[wid].clear()
            
        if not history_data:
            self._update_all_lines()
            return
            
        times_map = {}
        for row in history_data:
            dt = datetime.fromisoformat(row['timestamp'].replace("Z", "+00:00"))
            t = mdates.date2num(dt)
            if t not in times_map:
                times_map[t] = {}
            times_map[t][row.get('well_id')] = row
            
        sorted_times = sorted(times_map.keys())
        for t in sorted_times:
            self._times.append(t)
            row_map = times_map[t]
            for wid in self._well_ids:
                row = row_map.get(wid, {})
                val = np.nan
                if self._chart_key == "temp": val = row.get("temperature_c", np.nan)
                elif self._chart_key == "pres": val = row.get("pressure_bar", np.nan)
                elif self._chart_key == "flow": val = row.get("flow_m3h", np.nan)
                elif self._chart_key == "risk": val = row.get("risk_score", 0.0)
                elif self._chart_key == "health": val = row.get("health_score", 100.0)
                elif self._chart_key == "conf": val = row.get("confidence", 85.0)
                self._hist_data[wid].append(val)
                
        self._update_all_lines(auto_scroll=False)
        
    def set_line_visibility(self, wid: str, visible: bool):
        if wid in self._lines:
            self._lines[wid].set_visible(visible)
            
            handles, labels = self._ax.get_legend_handles_labels()
            # Rebuild legend
            visible_handles = []
            visible_labels = []
            for h, l in zip(handles, labels):
                if l in self._well_ids:
                    if self._lines.get(l) and self._lines[l].get_visible():
                        visible_handles.append(h)
                        visible_labels.append(l)
                else:
                    visible_handles.append(h)
                    visible_labels.append(l)
            
            if self._ax.get_legend():
                self._ax.get_legend().remove()
            if visible_handles:
                self._ax.legend(visible_handles, visible_labels, fontsize=9, loc="upper right", facecolor=BG_HEADER, edgecolor=BORDER, labelcolor=TEXT_SECONDARY, framealpha=0.9)
                
            self._auto_scale_y_axis()
            self._canvas.draw_idle()
            
    def get_stats(self) -> dict:
        stats = {}
        data_source = self._live_data_ref if self._is_live else self._hist_data
        
        for wid in self._well_ids:
            if not self._lines[wid].get_visible():
                continue
                
            if not data_source or wid not in data_source:
                continue
                
            ydata = data_source[wid][self._chart_key] if self._is_live else data_source[wid]
            if len(ydata) == 0:
                continue
                
            valid_y = [v for v in ydata if not np.isnan(v)]
            if valid_y:
                stats[wid] = {
                    "curr": valid_y[-1],
                    "avg": np.mean(valid_y),
                    "min": np.min(valid_y),
                    "max": np.max(valid_y),
                    "std": np.std(valid_y)
                }
        return stats
        
    def get_visible_data(self) -> list[dict]:
        xlim = self._ax.get_xlim()
        export_data = []
        times = self._live_times_ref if self._is_live else self._hist_times
        data_source = self._live_data_ref if self._is_live else self._hist_data
        
        if not times or not data_source:
            return export_data
            
        for i, t in enumerate(times):
            if xlim[0] <= t <= xlim[1]:
                dt_str = mdates.num2date(t).strftime("%Y-%m-%d %H:%M:%S")
                for wid in self._well_ids:
                    if self._lines[wid].get_visible():
                        ydata = data_source[wid][self._chart_key] if self._is_live else data_source[wid]
                        if i < len(ydata):
                            v = ydata[i]
                            if not np.isnan(v):
                                export_data.append({
                                    "Timestamp": dt_str,
                                    "Well Name": wid,
                                    self._title: round(v, 2)
                                })
        return export_data
        
    def _update_all_lines(self, auto_scroll=False):
        times = self._live_times_ref if self._is_live else self._hist_times
        data_source = self._live_data_ref if self._is_live else self._hist_data
        
        if not times or not data_source:
            return
            
        for wid in self._well_ids:
            if wid in data_source:
                ydata = data_source[wid][self._chart_key] if self._is_live else data_source[wid]
                self._lines[wid].set_data(list(times), list(ydata))
            
        if auto_scroll and len(times) > 0 and not self._is_panning:
            t = times[-1]
            t_min = t - (_MAX_POINTS * 2.0 / 86400.0)
            self._ax.set_xlim(t_min, t + (10.0 / 86400.0))
            
        self._auto_scale_y_axis()
        self._canvas.draw_idle()
        
    def _auto_scale_y_axis(self):
        if not self._auto_scale_y: return
        all_y = []
        data_source = self._live_data_ref if self._is_live else self._hist_data
        
        if not data_source: return
        
        for wid in self._well_ids:
            if self._lines[wid].get_visible() and wid in data_source:
                ydata = data_source[wid][self._chart_key] if self._is_live else data_source[wid]
                all_y.extend([v for v in ydata if not np.isnan(v)])
                
        if not all_y: return
        min_y, max_y = min(all_y), max(all_y)
        range_y = max_y - min_y
        
        thresh_list = [t[0] for t in self._thresholds]
        fixed_min = min(thresh_list) if thresh_list else min_y
        fixed_max = max(thresh_list) if thresh_list else max_y
        
        if range_y == 0:
            pad = max(abs(min_y) * 0.1, 1.0)
            t_min = min(min_y - pad, fixed_min)
            t_max = max(max_y + pad, fixed_max)
        else:
            pad = range_y * 0.20
            t_min = min(min_y - pad, fixed_min)
            t_max = max(max_y + pad, fixed_max)
            
        if t_max < fixed_max: t_max = fixed_max + (fixed_max - t_min) * 0.10
        if t_min > fixed_min: t_min = fixed_min - (t_max - fixed_min) * 0.10
        
        self._ax.set_ylim(t_min, t_max)
        
    def _on_hover(self, event):
        if event.inaxes != self._ax:
            self._annot.set_visible(False)
            self._vline.set_alpha(0.0)
            self._hline.set_alpha(0.0)
            self._canvas.draw_idle()
            return
            
        x_mouse, y_mouse = event.xdata, event.ydata
        nearest_line = None
        min_dist = float('inf')
        nearest_point = None
        nearest_wid = None
        
        for wid in self._well_ids:
            line = self._lines[wid]
            if not line.get_visible(): continue
            xdata, ydata = line.get_data()
            if len(xdata) == 0: continue
            
            # Find nearest x
            idx = np.searchsorted(xdata, x_mouse)
            if idx == 0: i = 0
            elif idx == len(xdata): i = len(xdata) - 1
            else:
                i = idx if (xdata[idx] - x_mouse) < (x_mouse - xdata[idx-1]) else idx - 1
                
            dist = abs(xdata[i] - x_mouse) + abs(ydata[i] - y_mouse) / (self._ax.get_ylim()[1] - self._ax.get_ylim()[0])
            if dist < min_dist:
                min_dist = dist
                nearest_line = line
                nearest_point = (xdata[i], ydata[i])
                nearest_wid = wid
                
        if nearest_line and min_dist < 0.1:
            px, py = nearest_point
            
            # Crosshair
            self._vline.set_xdata([px, px])
            self._vline.set_alpha(0.8)
            self._hline.set_ydata([py, py])
            self._hline.set_alpha(0.8)
            
            # Annot
            self._annot.xy = (px, py)
            dt_str = mdates.num2date(px).strftime("%H:%M:%S")
            
            status = "Normal"
            for level, color in self._thresholds:
                if color == CLR_CRITICAL:
                    if (py >= level and level > np.mean(self._ax.get_ylim())) or (py <= level and level < np.mean(self._ax.get_ylim())): status = "Critical"
                elif color == CLR_WARNING and status == "Normal":
                    if (py >= level and level > np.mean(self._ax.get_ylim())) or (py <= level and level < np.mean(self._ax.get_ylim())): status = "Warning"
            
            color_str = "#10b981" if status == "Normal" else ("#f59e0b" if status == "Warning" else "#ef4444")
            
            text = f"Time: {dt_str}\nWell: {nearest_wid}\nValue: {py:.2f} {self._unit}\nStatus: {status}"
            self._annot.set_text(text)
            self._annot.get_bbox_patch().set_edgecolor(color_str)
            self._annot.set_visible(True)
        else:
            self._annot.set_visible(False)
            self._vline.set_alpha(0.0)
            self._hline.set_alpha(0.0)
            
        self._canvas.draw_idle()
        
    def _on_scroll(self, event):
        if not event.inaxes: return
        self._auto_scale_y = False
        factor = 0.8 if event.button == 'up' else 1.2
        xlim = self._ax.get_xlim()
        xdata = event.xdata
        new_xlim = (xdata - (xdata - xlim[0]) * factor, xdata + (xlim[1] - xdata) * factor)
        self._ax.set_xlim(new_xlim)
        self._canvas.draw_idle()
        
    def _on_press(self, event):
        if event.dblclick:
            self._auto_scale_y = True
            self._update_all_lines(auto_scroll=True)
            return
        if event.button == 1 and event.inaxes:
            self._is_panning = True
            self._auto_scale_y = False
            self._pan_start_x = event.xdata
            self._pan_start_xlim = self._ax.get_xlim()
            
    def _on_release(self, event):
        if event.button == 1:
            self._is_panning = False
            self._pan_start_x = None
            
    def _on_pan(self, event):
        if self._is_panning and event.xdata and self._pan_start_x:
            dx = event.xdata - self._pan_start_x
            xlim = self._pan_start_xlim
            self._ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
            self._canvas.draw_idle()
            
    def _on_draw(self, event):
        pass
