"""
gui/widgets.py
==============
Custom dashboard widgets for the Dikili Geothermal SCADA GUI.

Implements reusable components using Tkinter Canvas (wrapped in Frames
to avoid Tcl naming conflicts):
  - GaugeWidget
  - KPICard
  - PumpIcon
  - ValveIcon
  - PipeSegment
  - StatusIndicator
"""

from __future__ import annotations

import math
import tkinter as tk

from gui.theme import (
    BG_SECONDARY, BG_TERTIARY, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    CLR_RUNNING, CLR_STOPPED, CLR_MAINTENANCE, CLR_COMMS_LOSS,
    CLR_HOT_FLUID, CLR_COOL_FLUID,
    FONT_MONO_MD, FONT_MONO_LG, FONT_LABEL_SM, FONT_LABEL,
    GAUGE_SIZE, KPI_CARD_W, KPI_CARD_H,
    PUMP_ICON_SIZE, VALVE_ICON_SIZE, PIPE_WIDTH, STATUS_LED_R,
    value_color,
)

# ═════════════════════════════════════════════════════════════════════════════
#  GAUGE WIDGET
# ═════════════════════════════════════════════════════════════════════════════

class GaugeWidget(tk.Frame):
    """Circular gauge showing value on an arc with colored zones."""
    def __init__(self, parent: tk.Widget, label: str, unit: str,
                 min_val: float, max_val: float,
                 warn_lo: float, warn_hi: float,
                 crit_lo: float | None = None, crit_hi: float | None = None,
                 size: int = GAUGE_SIZE, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, **kwargs)
        
        cw = size + 20
        ch = size + 50
        self.canvas = tk.Canvas(self, width=cw, height=ch, bg=BG_SECONDARY, highlightthickness=0)
        self.canvas.pack()

        self._label   = label
        self._unit    = unit
        self._min     = min_val
        self._max     = max_val
        self._warn_lo = warn_lo
        self._warn_hi = warn_hi
        self._crit_lo = crit_lo if crit_lo is not None else warn_lo
        self._crit_hi = crit_hi if crit_hi is not None else warn_hi
        self._size    = size
        self._value   = min_val
        self._cx      = cw // 2
        self._cy      = size // 2 + 10
        self._radius  = (size - 20) // 2

        self._draw_static()
        self._needle_id = None
        self._value_id  = None
        self.set_value(min_val)

    def _draw_static(self):
        cx, cy, r = self._cx, self._cy, self._radius
        bbox = (cx - r, cy - r, cx + r, cy + r)
        span = 240
        start = -210
        thickness = 8

        def draw_band(v1, v2, color):
            v1_c = max(self._min, min(self._max, v1))
            v2_c = max(self._min, min(self._max, v2))
            if v1_c >= v2_c: return
            p1 = (v1_c - self._min) / (self._max - self._min)
            p2 = (v2_c - self._min) / (self._max - self._min)
            extent = (p2 - p1) * span
            astart = start - (p1 * span)
            self.canvas.create_arc(*bbox, start=astart, extent=-extent, style="arc",
                                   outline=color, width=thickness)

        draw_band(self._min, self._crit_lo, CLR_CRITICAL)
        draw_band(self._crit_lo, self._warn_lo, CLR_WARNING)
        draw_band(self._warn_lo, self._warn_hi, CLR_NORMAL)
        draw_band(self._warn_hi, self._crit_hi, CLR_WARNING)
        draw_band(self._crit_hi, self._max, CLR_CRITICAL)

        self.canvas.create_text(cx, ch := (cy + r + 24), text=self._label,
                                fill=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="center")

    def set_value(self, value: float):
        self._value = max(self._min, min(self._max, value))
        self.canvas.delete(self._needle_id)
        self.canvas.delete(self._value_id)

        cx, cy = self._cx, self._cy
        span = 240
        start = -210
        fraction = (self._value - self._min) / (self._max - self._min)
        angle_deg = start - (fraction * span)
        angle_rad = math.radians(angle_deg)

        needle_color = value_color(self._value, self._warn_lo, self._warn_hi, self._crit_lo, self._crit_hi)
        
        nx = cx + (self._radius - 12) * math.cos(angle_rad)
        ny = cy - (self._radius - 12) * math.sin(angle_rad)
        self._needle_id = self.canvas.create_line(cx, cy, nx, ny, fill=needle_color, width=3, arrow="last", arrowshape=(8, 10, 3))
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=BORDER_LIGHT, outline="")
        self._value_id = self.canvas.create_text(cx, cy + 22, text=f"{self._value:.1f} {self._unit}",
                                                 fill=needle_color, font=FONT_MONO_MD, anchor="center")

# ═════════════════════════════════════════════════════════════════════════════
#  KPI CARD
# ═════════════════════════════════════════════════════════════════════════════

class KPICard(tk.Frame):
    def __init__(self, parent: tk.Widget, label: str = "KPI", unit: str = "",
                 card_width: int = KPI_CARD_W, card_height: int = KPI_CARD_H, **kwargs):
        super().__init__(parent, bg=BG_TERTIARY, **kwargs)
        self.canvas = tk.Canvas(self, width=card_width, height=card_height,
                                bg=BG_TERTIARY, highlightthickness=1, highlightbackground=BORDER)
        self.canvas.pack()

        self._width = card_width
        self._height = card_height
        self._label = label
        self._unit  = unit
        self._prev_value: float | None = None

        self.canvas.create_text(self._width // 2, 14, text=label, fill=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="center")
        self._val_id = self.canvas.create_text(self._width // 2, self._height // 2 + 2, text="---",
                                               fill=TEXT_PRIMARY, font=FONT_MONO_LG, anchor="center")
        self._unit_id = self.canvas.create_text(self._width // 2, self._height - 14, text=unit,
                                                fill=TEXT_MUTED, font=FONT_LABEL_SM, anchor="center")
        self._trend_id = None

    def set_value(self, value: float, color: str = TEXT_PRIMARY):
        # Format dynamically but pad to 7 characters for visual stability
        if value >= 1000:
            val_str = f"{value:>7,.0f}"
        elif value >= 100:
            val_str = f"{value:>7.1f}"
        else:
            val_str = f"{value:>7.2f}"
            
        self.canvas.itemconfig(self._val_id, text=val_str, fill=color)

        if self._prev_value is not None:
            diff = value - self._prev_value
            self.canvas.delete(self._trend_id)
            if abs(diff) > 0.01:
                icon = "▲" if diff > 0 else "▼"
                tcolor = CLR_CRITICAL if diff > 0 and color == CLR_CRITICAL else (CLR_NORMAL if diff > 0 else CLR_WARNING)
                self._trend_id = self.canvas.create_text(self._width - 14, self._height // 2 + 2, text=icon, fill=tcolor, font=FONT_LABEL_SM)
        self._prev_value = value

# ═════════════════════════════════════════════════════════════════════════════
#  PUMP ICON
# ═════════════════════════════════════════════════════════════════════════════

class PumpIcon(tk.Frame):
    def __init__(self, parent: tk.Widget, label: str = "P1", size: int = PUMP_ICON_SIZE, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, **kwargs)
        self.canvas = tk.Canvas(self, width=size + 4, height=size + 20, bg=BG_SECONDARY, highlightthickness=0)
        self.canvas.pack()

        self._size   = size
        self._label  = label
        self._angle  = 0.0
        self._state  = "RUNNING"
        self._cx     = size // 2 + 2
        self._cy     = size // 2 + 2
        self._r      = size // 2 - 2

        self.canvas.create_text(self._cx, size + 12, text=label, fill=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="center")
        self._draw()

    def _draw(self):
        self.canvas.delete("pump_parts")
        cx, cy, r = self._cx, self._cy, self._r

        colors = {"RUNNING": CLR_RUNNING, "STARTING": CLR_WARNING, "FAULT": CLR_CRITICAL, "OFF": CLR_STOPPED}
        badges = {"RUNNING": "R", "STARTING": "S", "FAULT": "A", "OFF": "-"}
        
        color = colors.get(self._state, CLR_STOPPED)
        badge = badges.get(self._state, "-")

        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=BORDER_LIGHT, width=2, tags="pump_parts")
        self.canvas.create_oval(cx - r+2, cy - r+2, cx + r-2, cy + r-2, fill=BG_TERTIARY, outline="", tags="pump_parts")

        if self._state != "OFF" and self._state != "FAULT":
            a1 = math.radians(self._angle)
            a2 = math.radians(self._angle + 120)
            a3 = math.radians(self._angle + 240)
            r_in = 4
            r_out = r - 4
            for a in (a1, a2, a3):
                x1, y1 = cx + r_in * math.cos(a), cy + r_in * math.sin(a)
                x2, y2 = cx + r_out * math.cos(a), cy + r_out * math.sin(a)
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3, tags="pump_parts")

        # Draw status badge (ISA-101 Accessibility)
        bw = 12
        bx, by = cx + r - bw, cy + r - bw
        self.canvas.create_rectangle(bx, by, bx + bw, by + bw, fill=color, outline=BORDER, tags="pump_parts")
        self.canvas.create_text(bx + bw/2, by + bw/2, text=badge, fill="#ffffff", font=("Consolas", 8, "bold"), tags="pump_parts")

    def set_state(self, state: str, speed_rpm: float = 1450.0):
        self._state = state
        if state == "RUNNING" or state == "STARTING":
            step = 15.0 if speed_rpm > 1000 else 8.0
            self._angle = (self._angle + step) % 360
        self._draw()

# ═════════════════════════════════════════════════════════════════════════════
#  VALVE ICON
# ═════════════════════════════════════════════════════════════════════════════

class ValveIcon(tk.Frame):
    def __init__(self, parent: tk.Widget, label: str = "V1", size: int = VALVE_ICON_SIZE, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, **kwargs)
        self.canvas = tk.Canvas(self, width=size + 4, height=size + 16, bg=BG_SECONDARY, highlightthickness=0)
        self.canvas.pack()

        self._size   = size
        self._label  = label
        self._state  = "OPEN"
        self._cx     = size // 2 + 2
        self._cy     = size // 2 + 2

        self.canvas.create_text(self._cx, size + 10, text=label, fill=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="center")
        self._draw()

    def _draw(self):
        self.canvas.delete("valve_parts")
        cx, cy = self._cx, self._cy
        hs = self._size // 2 - 2

        colors = {"OPEN": CLR_RUNNING, "CLOSED": CLR_STOPPED, "THROTTLED": CLR_WARNING, "FAULT": CLR_CRITICAL}
        badges = {"OPEN": "O", "CLOSED": "C", "THROTTLED": "T", "FAULT": "F"}
        
        color = colors.get(self._state, CLR_STOPPED)
        badge = badges.get(self._state, "-")

        self.canvas.create_polygon(cx - hs, cy - hs, cx, cy, cx - hs, cy + hs, fill=color, outline=BORDER_LIGHT, width=1, tags="valve_parts")
        self.canvas.create_polygon(cx + hs, cy - hs, cx, cy, cx + hs, cy + hs, fill=color, outline=BORDER_LIGHT, width=1, tags="valve_parts")
        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=BORDER, outline="")

        # Draw status badge (ISA-101 Accessibility)
        bw = 12
        bx, by = cx + hs - bw + 2, cy - hs - 2
        self.canvas.create_rectangle(bx, by, bx + bw, by + bw, fill=color, outline=BORDER, tags="valve_parts")
        self.canvas.create_text(bx + bw/2, by + bw/2, text=badge, fill="#ffffff", font=("Consolas", 8, "bold"), tags="valve_parts")

    def set_state(self, state: str):
        self._state = state
        self._draw()

# ═════════════════════════════════════════════════════════════════════════════
#  PIPE SEGMENT
# ═════════════════════════════════════════════════════════════════════════════

class PipeSegment(tk.Frame):
    def __init__(self, parent: tk.Widget, length: int = 80, orientation: str = "vertical", fluid_type: str = "hot", **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, **kwargs)
        w = PIPE_WIDTH + 8 if orientation == "vertical" else length
        h = length if orientation == "vertical" else PIPE_WIDTH + 8
        self.canvas = tk.Canvas(self, width=w, height=h, bg=BG_SECONDARY, highlightthickness=0)
        self.canvas.pack()

        self._length      = length
        self._orientation = orientation
        self._fluid_color = CLR_HOT_FLUID if fluid_type == "hot" else CLR_COOL_FLUID
        self._flow_offset = 0
        self._flowing     = True
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        w, h = int(self.canvas["width"]), int(self.canvas["height"])
        pw = PIPE_WIDTH
        
        if self._orientation == "vertical":
            cx = w // 2
            self.canvas.create_rectangle(cx - pw//2, 0, cx + pw//2, h, fill=self._fluid_color, outline=BORDER)
            if self._flowing:
                for y in range(self._flow_offset, h, 20):
                    self.canvas.create_line(cx - pw//2 + 2, y, cx + pw//2 - 2, y + 6, fill=BORDER_LIGHT, width=2)
                    self.canvas.create_line(cx - pw//2 + 2, y + 6, cx + pw//2 - 2, y, fill=BORDER_LIGHT, width=2)
        else:
            cy = h // 2
            self.canvas.create_rectangle(0, cy - pw//2, w, cy + pw//2, fill=self._fluid_color, outline=BORDER)
            if self._flowing:
                for x in range(self._flow_offset, w, 20):
                    self.canvas.create_line(x, cy - pw//2 + 2, x + 6, cy + pw//2 - 2, fill=BORDER_LIGHT, width=2)
                    self.canvas.create_line(x + 6, cy - pw//2 + 2, x, cy + pw//2 - 2, fill=BORDER_LIGHT, width=2)

    def set_flowing(self, is_flowing: bool):
        self._flowing = is_flowing
        if self._flowing:
            self._flow_offset = (self._flow_offset + 5) % 20
        self._draw()

# ═════════════════════════════════════════════════════════════════════════════
#  STATUS INDICATOR
# ═════════════════════════════════════════════════════════════════════════════

class StatusIndicator(tk.Frame):
    def __init__(self, parent: tk.Widget, size: int = STATUS_LED_R * 2 + 4, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, **kwargs)
        self.canvas = tk.Canvas(self, width=size, height=size, bg=BG_SECONDARY, highlightthickness=0)
        self.canvas.pack()
        self._size = size
        self.set_status("OFFLINE")

    def set_status(self, health: str):
        colors = {"GOOD": CLR_RUNNING, "WARNING": CLR_WARNING, "CRITICAL": CLR_CRITICAL, "OFFLINE": CLR_STOPPED}
        color = colors.get(health, CLR_STOPPED)
        
        self.canvas.delete("all")
        s = self._size
        m = 2 # margin
        
        if health == "WARNING":
            # Triangle pointing up
            self.canvas.create_polygon(s/2, m, s-m, s-m, m, s-m, fill=color, outline=BORDER_LIGHT, width=1)
        elif health == "CRITICAL":
            # Diamond
            self.canvas.create_polygon(s/2, m, s-m, s/2, s/2, s-m, m, s/2, fill=color, outline=BORDER_LIGHT, width=1)
        elif health == "GOOD":
            # Circle
            self.canvas.create_oval(m, m, s-m, s-m, fill=color, outline=BORDER_LIGHT, width=1)
        else: 
            # Square for Offline/Unknown
            self.canvas.create_rectangle(m, m, s-m, s-m, fill=color, outline=BORDER_LIGHT, width=1)

# ═════════════════════════════════════════════════════════════════════════════
#  TOGGLE SWITCH
# ═════════════════════════════════════════════════════════════════════════════

class ToggleSwitch(tk.Canvas):
    def __init__(self, parent: tk.Widget, is_on: bool = False, command=None, width=40, height=20, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_SECONDARY, highlightthickness=0, cursor="hand2", **kwargs)
        self._is_on = is_on
        self._command = command
        self._sw_w = width
        self._sw_h = height
        self._radius = height // 2 - 2
        
        self.bind("<Button-1>", self._toggle)
        self._draw()
        
    def _draw(self):
        self.delete("all")
        bg_color = CLR_NORMAL if self._is_on else BORDER
        # Draw pill shape
        self.create_oval(2, 2, self._sw_h, self._sw_h, fill=bg_color, outline=bg_color)
        self.create_oval(self._sw_w - self._sw_h, 2, self._sw_w - 2, self._sw_h, fill=bg_color, outline=bg_color)
        self.create_rectangle(self._sw_h // 2, 2, self._sw_w - self._sw_h // 2, self._sw_h, fill=bg_color, outline=bg_color)
        
        # Draw circle
        circle_x = self._sw_w - self._radius - 4 if self._is_on else self._radius + 4
        self.create_oval(circle_x - self._radius, self._sw_h//2 - self._radius, 
                         circle_x + self._radius, self._sw_h//2 + self._radius, 
                         fill="#ffffff", outline="#ffffff")
        
    def _toggle(self, event):
        self._is_on = not self._is_on
        self._draw()
        if self._command:
            self._command(self._is_on)


# ═════════════════════════════════════════════════════════════════════════════
#  THEME TOGGLE (Sun / Moon)
# ═════════════════════════════════════════════════════════════════════════════
import math

class ThemeToggle(tk.Canvas):
    """Premium dark/light theme toggle with sun and moon icons."""

    def __init__(self, parent: tk.Widget, is_dark: bool = True, command=None, **kwargs):
        self.W = 72
        self.H = 34
        super().__init__(parent, width=self.W, height=self.H, bg=BG_SECONDARY, 
                         highlightthickness=0, cursor="hand2", **kwargs)
        self._is_dark = is_dark
        self._command = command
        self.bind("<Button-1>", self._toggle)
        self._draw()

    # ── colours ──────────────────────────────────────────────────────────
    _DARK_BG     = "#2d3748"
    _DARK_BORDER = "#4a5568"
    _DARK_KNOB   = "#e2e8f0"
    _MOON_CLR    = "#e2e8f0"

    _LIGHT_BG     = "#e8ecf1"
    _LIGHT_BORDER = "#cbd5e0"
    _LIGHT_KNOB   = "#f6ad55"
    _LIGHT_RING   = "#ed8936"
    _SUN_RAY      = "#f6ad55"

    def _draw(self):
        self.delete("all")
        w, h = self.W, self.H
        r = h // 2  # pill corner radius

        if self._is_dark:
            bg, border = self._DARK_BG, self._DARK_BORDER
        else:
            bg, border = self._LIGHT_BG, self._LIGHT_BORDER

        # ── pill background ──────────────────────────────────────────────
        self.create_oval(1, 1, h - 1, h - 1, fill=bg, outline=border, width=2)
        self.create_oval(w - h + 1, 1, w - 1, h - 1, fill=bg, outline=border, width=2)
        self.create_rectangle(r, 1, w - r, h - 1, fill=bg, outline=bg)
        # top/bottom border lines for the rectangle gap
        self.create_line(r, 1, w - r, 1, fill=border, width=2)
        self.create_line(r, h - 1, w - r, h - 1, fill=border, width=2)

        if self._is_dark:
            self._draw_dark_state(w, h)
        else:
            self._draw_light_state(w, h)

    def _draw_dark_state(self, w, h):
        """Knob on the LEFT, moon icon on the RIGHT."""
        cx_knob = h // 2 + 1
        cy = h // 2
        kr = 10  # knob radius

        # Knob (circle with ring)
        self.create_oval(cx_knob - kr, cy - kr, cx_knob + kr, cy + kr,
                         fill=self._DARK_BG, outline=self._DARK_KNOB, width=2)
        # Inner dot for knob
        self.create_oval(cx_knob - 4, cy - 4, cx_knob + 4, cy + 4,
                         fill=self._DARK_BG, outline=self._DARK_KNOB, width=1.5)

        # Moon icon on the right
        mx = w - h // 2 - 1
        mr = 7
        # Main moon circle
        self.create_oval(mx - mr, cy - mr, mx + mr, cy + mr,
                         fill=self._MOON_CLR, outline=self._MOON_CLR)
        # Cutout circle to create crescent
        self.create_oval(mx - mr + 4, cy - mr - 2, mx + mr + 2, cy + mr - 4,
                         fill=self._DARK_BG, outline=self._DARK_BG)

    def _draw_light_state(self, w, h):
        """Sun icon on the LEFT, knob on the RIGHT."""
        cx_knob = w - h // 2 - 1
        cy = h // 2
        kr = 10

        # Knob (filled circle with ring)
        self.create_oval(cx_knob - kr, cy - kr, cx_knob + kr, cy + kr,
                         fill=self._LIGHT_KNOB, outline=self._LIGHT_RING, width=2)

        # Sun icon on the left
        sx = h // 2 + 1
        sr = 5
        # Sun body
        self.create_oval(sx - sr, cy - sr, sx + sr, cy + sr,
                         fill=self._SUN_RAY, outline=self._LIGHT_RING, width=1)
        # Sun rays
        ray_len = 4
        for i in range(8):
            angle = i * (math.pi / 4)
            x1 = sx + math.cos(angle) * (sr + 2)
            y1 = cy + math.sin(angle) * (sr + 2)
            x2 = sx + math.cos(angle) * (sr + ray_len)
            y2 = cy + math.sin(angle) * (sr + ray_len)
            self.create_line(x1, y1, x2, y2, fill=self._SUN_RAY, width=2, capstyle="round")

    def _toggle(self, event):
        self._is_dark = not self._is_dark
        self._draw()
        if self._command:
            self._command(self._is_dark)
