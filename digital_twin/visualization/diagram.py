"""
digital_twin/visualization/diagram.py
=====================================
Geothermal process flow diagram drawn on a tkinter Canvas.
Refactored for the Phase 5.1 Engineering Layout.
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from typing import Callable, Any

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    CLR_HOT_FLUID, CLR_WARM_FLUID, CLR_COOL_FLUID, CLR_PIPE_BG,
    FONT_MONO_MD, FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE,
    PIPE_WIDTH
)
from digital_twin.visualization.popups import HoverTooltip

# ─── Layout constants ────────────────────────────────────────────────────────

# Constants are now calculated dynamically in _draw_static based on canvas size

class ProcessDiagram(tk.Frame):
    def __init__(self, parent: tk.Widget, width: int = 800, height: int = 750,
                 on_equip_click: Callable[[str, str], None] | None = None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        
        lbl = tk.Label(self, text="DIGITAL TWIN ENGINEERING PLATFORM", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(fill="x", pady=(4, 4))

        self.canvas = tk.Canvas(self, width=width, height=height,
                                bg=BG_PRIMARY, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        
        self._width  = width
        self._height = height
        self._flow_offset = 0
        self._pump_angle = 0
        self._pump_running = False
        self._on_click_cb = on_equip_click
        self._on_click_cb = on_equip_click
        self._selected_equip_id = None
        self._focus_pulse_alpha = 0.0

        self._equip_boxes: dict[str, int] = {}
        self._pump_rotors: dict[str, list[int]] = {}
        self._labels: dict[str, dict[str, int]] = {}
        self._tooltips: list[HoverTooltip] = []
        
        from core.configuration import config
        max_fps = config.get("performance.rendering.max_fps", 10.0)
        from digital_twin.rendering_scheduler import RenderingScheduler
        self._rendering_scheduler = RenderingScheduler(max_fps=max_fps)
        
        from digital_twin.layout_engine import LayoutEngine
        self._layout_engine = LayoutEngine()

        
        from digital_twin.layer_manager import LayerManager
        self._layer_manager = LayerManager()
        self.layers = {l["layer_name"]: self._layer_manager.is_layer_visible(l["layer_name"]) for l in self._layer_manager.get_all_layers()}

        self._draw_static()
        self._apply_initial_layers()
        self._animate_tick()

    def _apply_initial_layers(self):
        for k, v in self.layers.items():
            self.set_layer_visibility(k, v)
            
    def set_layer_visibility(self, layer_name: str, visible: bool):
        self.layers[layer_name] = visible
        if visible:
            self._layer_manager.show_layer(layer_name)
        else:
            self._layer_manager.hide_layer(layer_name)
        state = "normal" if visible else "hidden"
        self.canvas.itemconfig(f"layer_{layer_name}", state=state)

    def _on_resize(self, event):
        if abs(self._width - event.width) > 5 or abs(self._height - event.height) > 5:
            self._width = event.width
            self._height = event.height
            self.canvas.delete("all")
            self._equip_boxes.clear()
            self._tooltips.clear()
            self._pump_rotors.clear()
            self._labels.clear()
            self._draw_static()
            if hasattr(self, '_facility') and self._facility:
                self.update_from_twin(self._facility)

    def focus_equipment(self, eq_id: str):
        """Highlights the equipment and opens its popup."""
        self._selected_equip_id = eq_id
        import time
        self._highlight_expire_time = time.time() + 3.0
        
        # Hide all focus boxes first
        for key in self._equip_boxes.keys():
            self.canvas.itemconfig(f"focus&&{key}", state="hidden")
            
        # Show the focus box for the selected equipment
        self.canvas.itemconfig(f"focus&&{eq_id}", state="normal")
            
        # Trigger the click callback to open the popup
        if self._on_click_cb and eq_id in self._equip_boxes:
            # We don't have the exact name handy here, so we pass eq_id as name too
            # The popup gets the real name from facility anyway
            self._on_click_cb(eq_id, eq_id)

    def _register_interactive(self, tag: str, equip_id: str, equip_type: str):
        """Binds click and hover events to a canvas tag."""
        # Click event
        def _handle_click(e, eid=equip_id, etyp=equip_type):
            self._selected_equip_id = eid
            import time
            self._highlight_expire_time = time.time() + 3.0
            
            # Hide old focuses
            for key in self._equip_boxes.keys():
                self.canvas.itemconfig(f"focus&&{key}", state="hidden")
            self.canvas.itemconfig(f"focus&&{eid}", state="normal")
            
            if self._on_click_cb:
                self._on_click_cb(eid, etyp)
            if hasattr(self, '_facility') and self._facility:
                self.update_from_twin(self._facility)
                
        self.canvas.tag_bind(tag, "<Button-1>", _handle_click)
        self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"), add="+")
        self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""), add="+")

        # Fallback hover tooltip
        def make_tooltip_text(eid=equip_id, etyp=equip_type):
            if not hasattr(self, '_facility') or not self._facility:
                return f"{etyp} | {eid}\nNo data available"
            eq = self._facility.get_equipment(eid)
            if not eq:
                return f"{etyp} | {eid}\nNo data available"
            return f"Click for detailed engineering panel"
            
        self._tooltips.append(HoverTooltip(self.canvas, tag, make_tooltip_text))

    def _draw_box(self, cx, cy, wid, name, tag):
        w = 276
        h = 56
        box = self.canvas.create_rectangle(
            cx - w // 2, cy - h // 2,
            cx + w // 2, cy + h // 2,
            fill=BG_TERTIARY, outline=CLR_NORMAL, width=2, tags=("equip", tag)
        )
        self._equip_boxes[wid] = box
        self._register_interactive(tag, wid, name)
        self.canvas.create_text(cx, cy - 12, text=name.upper(), fill=TEXT_PRIMARY, font=("Segoe UI", 14, "bold"), anchor="center", tags=(tag,))
        lbl = self.canvas.create_text(cx, cy + 12, text="---", fill=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), anchor="center", tags=(tag,))
        
        # Layer labels - Placed on left/right flanks to prevent vertical overlap
        sensor_lbl = self.canvas.create_text(cx - w // 2 - 20, cy - 15, text="", fill=TEXT_SECONDARY, font=FONT_MONO_MD, anchor="e", justify="left", tags=(tag, "layer_sensor"))
        alarm_lbl = self.canvas.create_text(cx, cy + h // 2 + 15, text="", fill=CLR_CRITICAL, font=("Segoe UI", 11, "bold"), anchor="center", justify="center", tags=(tag, "layer_alarm"))
        maint_lbl = self.canvas.create_text(cx + w // 2 + 20, cy - 15, text="", fill="#34d399", font=FONT_MONO_MD, anchor="w", tags=(tag, "layer_maintenance"))
        thermal_lbl = self.canvas.create_text(cx + w // 2 + 20, cy + 15, text="", fill="#f87171", font=FONT_MONO_MD, anchor="w", tags=(tag, "layer_thermal"))
        
        self._labels[wid] = {
            "info": lbl,
            "sensor": sensor_lbl,
            "alarm": alarm_lbl,
            "maintenance": maint_lbl,
            "thermal": thermal_lbl
        }
        
        # Add a hidden focus highlight rectangle
        focus_box = self.canvas.create_rectangle(
            cx - w // 2 - 4, cy - h // 2 - 4,
            cx + w // 2 + 4, cy + h // 2 + 4,
            outline="#facc15", width=3, state="hidden", tags=(tag, f"focus&&{wid}")
        )
        
        return box

    def _draw_pump(self, cx, cy, pid, name, tag):
        r = 35
        box = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=BG_TERTIARY, outline=CLR_NORMAL, width=2, tags=("equip", tag)
        )
        self._equip_boxes[pid] = box
        self._register_interactive(tag, pid, name)
        
        # Draw dynamic rotor lines (will animate)
        l1 = self.canvas.create_line(cx-20, cy, cx+20, cy, fill=TEXT_PRIMARY, width=2, tags=(tag,))
        l2 = self.canvas.create_line(cx, cy-20, cx, cy+20, fill=TEXT_PRIMARY, width=2, tags=(tag,))
        self._pump_rotors[pid] = [l1, l2, cx, cy]
        
        # Text to right (still fine if horizontal pipes go top/bottom or left)
        self.canvas.create_text(cx + r + 20, cy - 12, text=name.upper(), fill=TEXT_PRIMARY, font=("Segoe UI", 14, "bold"), anchor="w", tags=(tag,))
        lbl = self.canvas.create_text(cx + r + 20, cy + 12, text="---", fill=TEXT_SECONDARY, font=("Segoe UI", 12, "bold"), anchor="w", tags=(tag,))
        
        # Layer labels
        sensor_lbl = self.canvas.create_text(cx - r - 20, cy - 15, text="", fill=TEXT_SECONDARY, font=FONT_MONO_MD, anchor="e", justify="left", tags=(tag, "layer_sensor"))
        alarm_lbl = self.canvas.create_text(cx + r + 20, cy + r + 15, text="", fill=CLR_CRITICAL, font=("Segoe UI", 11, "bold"), anchor="w", justify="left", tags=(tag, "layer_alarm"))
        maint_lbl = self.canvas.create_text(cx + r + 160, cy - 15, text="", fill="#34d399", font=FONT_MONO_MD, anchor="w", tags=(tag, "layer_maintenance"))
        thermal_lbl = self.canvas.create_text(cx + r + 160, cy + 15, text="", fill="#f87171", font=FONT_MONO_MD, anchor="w", tags=(tag, "layer_thermal"))

        self._labels[pid] = {
            "info": lbl,
            "sensor": sensor_lbl,
            "alarm": alarm_lbl,
            "maintenance": maint_lbl,
            "thermal": thermal_lbl
        }
        
        # Add a hidden focus highlight oval
        focus_box = self.canvas.create_oval(
            cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4,
            outline="#facc15", width=3, state="hidden", tags=(tag, f"focus&&{pid}")
        )
        
        return box

    def _draw_static(self):
        # Dynamic responsive vertical scaling
        eff_height = max(self._height, 800)
        start_y = 80 # Down slightly to center vertically
        total_span = eff_height - 140 # Increase spacing span
        s = total_span / 650.0

        # Store for animation
        p101_meta = self._layout_engine.get_equipment("P-101")
        p201_meta = self._layout_engine.get_equipment("P-201")
        p301_meta = self._layout_engine.get_equipment("P-301")
        
        self._y_p101 = start_y + p101_meta["y_offset"] * s
        self._y_p201 = start_y + p201_meta["y_offset"] * s
        self._y_p301 = start_y + p301_meta["y_offset"] * s

        # Draw pipelines first (so equipment boxes stack on top of them)
        for pipe in self._layout_engine.get_all_pipelines():
            from_x = int(self._width * pipe.get("from_x_factor", pipe.get("x_factor", 0.5)))
            to_x = int(self._width * pipe.get("to_x_factor", pipe.get("x_factor", 0.5)))
            from_y = int(start_y + pipe["from_y_offset"] * s + pipe.get("from_add", 0))
            to_y = int(start_y + pipe["to_y_offset"] * s + pipe.get("to_add", 0))
            
            # Additional rigid horizontal offset (if needed for elbows)
            from_x += pipe.get("from_x_add", 0)
            to_x += pipe.get("to_x_add", 0)
            
            self._draw_pipe_segment(from_x, from_y, to_x, to_y, pipe["id"], pipe.get("temp", "hot"))

        # Draw equipment
        for eq in self._layout_engine.get_all_equipment():
            x = int(self._width * eq["x_factor"])
            y = int(start_y + eq["y_offset"] * s)
            
            eq_type = eq["type"]
            if eq_type == "box":
                self._draw_box(x, y, eq["id"], eq["name"], eq["tag"])
            elif eq_type == "pump":
                self._draw_pump(x, y, eq["id"], eq["name"], eq["tag"])
            elif eq_type == "valve":
                self._draw_valve(x, y, eq["id"], eq["name"], eq["tag"])



    def _draw_valve(self, cx, cy, vid, name, tag):
        w = 24
        h = 20
        # Bowtie shape
        bg = self.canvas.create_polygon(cx-w, cy-h, cx-w, cy+h, cx+w, cy-h, cx+w, cy+h, fill=BG_SECONDARY, outline=BORDER, width=2, tags=(tag, "valve_bg", vid))
        # Center circle
        c = self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=TEXT_PRIMARY, tags=(tag, "valve_center", vid))
        
        lbl = self.canvas.create_text(cx + w + 15, cy, text=name, fill=TEXT_SECONDARY, font=FONT_MONO_MD, anchor="w", justify="left", tags=(tag,))
        self._equip_boxes[vid] = bg
        
        # Flap for animation
        flap = self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill=CLR_CRITICAL, width=3, tags=(tag, "valve_flap", vid))
        
        # Status icon
        icon = self.canvas.create_text(cx - 30, cy, text="", fill=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="e", tags=(tag, "status_icon", vid))
        
        if not hasattr(self, '_valves'): self._valves = {}
        self._valves[vid] = {"flap": flap, "angle": 90, "target_angle": 90, "icon": icon, "bg": bg, "cx": cx, "cy": cy}

    def _draw_pipe_segment(self, start_x: int, start_y: int, end_x: int, end_y: int, pipe_id: str, default_temp: str = "hot"):
        colors = {"hot": CLR_HOT_FLUID, "warm": CLR_WARM_FLUID, "cool": CLR_COOL_FLUID}
        bg_col = colors.get(default_temp, CLR_PIPE_BG)
        
        is_vert = abs(start_x - end_x) < 2
        
        if is_vert:
            bg = self.canvas.create_rectangle(start_x - PIPE_WIDTH // 2, min(start_y, end_y), start_x + PIPE_WIDTH // 2, max(start_y, end_y), fill=bg_col, outline=BORDER, tags=("layer_pipeline", f"pipe_bg_{pipe_id}"))
        else:
            bg = self.canvas.create_rectangle(min(start_x, end_x), start_y - PIPE_WIDTH // 2, max(start_x, end_x), start_y + PIPE_WIDTH // 2, fill=bg_col, outline=BORDER, tags=("layer_pipeline", f"pipe_bg_{pipe_id}"))
            
        line = self.canvas.create_line(start_x, start_y, end_x, end_y, fill="", tags=("pipe_line", "layer_pipeline", f"pipe_line_{pipe_id}"))
        
        if not hasattr(self, '_pipe_segments'): self._pipe_segments = {}
        self._pipe_segments[pipe_id] = {
            "bg": bg, "line": line, "x1": start_x, "y1": start_y, "x2": end_x, "y2": end_y,
            "flow_offset": 0.0, "flow_speed": 0.0, 
            "current_color": bg_col, "target_color": bg_col,
            "is_vert": is_vert
        }


    # ── Animation Color Interpolation ──────────────────────────────────────────

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3: hex_color = ''.join(c + c for c in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def _interpolate_color(self, c1, c2, factor):
        rgb1 = self._hex_to_rgb(c1)
        rgb2 = self._hex_to_rgb(c2)
        r = rgb1[0] + (rgb2[0] - rgb1[0]) * factor
        g = rgb1[1] + (rgb2[1] - rgb1[1]) * factor
        b = rgb1[2] + (rgb2[2] - rgb1[2]) * factor
        return self._rgb_to_hex((r, g, b))

    # ── Dynamic updates from Digital Twin ──────────────────────────────────

    def update_from_twin(self, facility):
        self._rendering_scheduler.schedule(lambda: self._actual_update_from_twin(facility))

    def _actual_update_from_twin(self, facility):
        if not self.winfo_ismapped(): return
        self._facility = facility
        if not hasattr(self, '_anim_state'):
            self._anim_state = {}
            self._last_time = time.time()
            self._global_pump_running = False

        global_pump = False
        
        for eq_id, box in self._equip_boxes.items():
            eq = facility.get_equipment(eq_id)
            if not eq: continue
            
            # AI Risk Visualization Color
            target_color = CLR_NORMAL
            if eq.status == "OFFLINE":
                target_color = CLR_OFFLINE
            elif eq.alarms or eq.status == "CRITICAL":
                target_color = CLR_CRITICAL
            elif eq.failure_risk > 0:
                if eq.failure_risk < 20: target_color = "#10b981" # Green
                elif eq.failure_risk < 40: target_color = "#fbbf24" # Yellow
                elif eq.failure_risk < 60: target_color = "#f59e0b" # Orange
                elif eq.failure_risk < 80: target_color = "#ef4444" # Red
                else: target_color = CLR_CRITICAL
            elif eq.status == "WARNING":
                target_color = CLR_WARNING
            elif eq.status == "MAINTENANCE REQUIRED":
                target_color = "#ffaa00"
            elif eq.status == "STANDBY":
                target_color = "#3b82f6" # Blue
            elif eq.status == "NORMAL":
                target_color = "#10b981" # Green
                
            # Status icon text
            icon_char = "🟢"
            if eq.status == "OFFLINE": icon_char = "⚪"
            if eq.status == "STANDBY": icon_char = "🔵"
            if eq.status == "WARNING": icon_char = "🟡"
            if eq.status == "MAINTENANCE REQUIRED": icon_char = "🔧"
            if eq.alarms: icon_char = "⚠️"
            elif eq.failure_risk > 40: icon_char = "🧠"
                
            anim = self._anim_state.setdefault(eq_id, {
                "current_color": CLR_OFFLINE,
                "target_color": target_color,
                "alarms": len(eq.alarms) > 0,
                "speed": 0,
                "is_emergency": eq.failure_risk >= 80 or len(eq.alarms) > 0
            })
            anim["target_color"] = target_color
            anim["alarms"] = len(eq.alarms) > 0
            anim["is_emergency"] = eq.failure_risk >= 80 or len(eq.alarms) > 0
            anim["icon"] = icon_char
            
            if eq.type == "PUMP" or eq.type == "WELL":
                flow = eq.sensors.get("Flow Rate", 0)
                anim["speed"] = flow / 50.0  # arbitrary scale for rotation
                if flow > 10:
                    global_pump = True
                    
            if eq.type == "VALVE":
                if eq.status == "FULLY OPEN": anim["target_angle"] = 0
                elif eq.status == "CLOSED": anim["target_angle"] = 90
                else: anim["target_angle"] = 45 # Partially open

            # Update static text labels if they exist
            lbls = self._labels.get(eq_id)
            if lbls:
                status_txt = "❗ WARNING" if eq.status == "WARNING" else eq.status
                self.canvas.itemconfig(lbls["info"], text=status_txt)
                if eq.status == "OFFLINE":
                    s_txt = "OFFLINE"
                else:
                    if eq.type == "WELL":
                        s_txt = f"{'Temp':<7}: {eq.sensors.get('Temperature', 0):>5.1f} °C\n{'Press':<7}: {eq.sensors.get('Pressure', 0):>5.1f} bar\n{'Flow':<7}: {eq.sensors.get('Flow Rate', 0):>5.1f} m³/h"
                    elif eq.type == "PUMP":
                        s_txt = f"{'Flow':<7}: {eq.sensors.get('Flow Rate', 0):>5.1f} m³/h\n{'Current':<7}: {eq.motor_current:>5.1f} A\n{'Power':<7}: {eq.power_consumption:>5.1f} kW"
                    elif eq.type == "SEPARATOR":
                        s_txt = f"{'Press':<7}: {eq.sensors.get('Pressure', 0):>5.1f} bar"
                    elif eq.type == "HX":
                        s_txt = f"{'Eff':<7}: {eq.sensors.get('Efficiency', 0):>5.1f} %"
                    elif eq.type == "NETWORK":
                        s_txt = f"{'Delta T':<7}: {eq.sensors.get('Delta T', 0):>5.1f} K"
                    else:
                        s_txt = ""
                
                self.canvas.itemconfig(lbls["sensor"], text=s_txt)
                self.canvas.itemconfig(lbls["alarm"], text="⚠️ " + eq.alarms[0] if eq.alarms else "")
                
                nm = getattr(eq, 'next_planned_maintenance', '')
                self.canvas.itemconfig(lbls["maintenance"], text=f"Maint: {nm}" if nm and nm != "Unknown" else "")
                
                t_txt = ""
                if eq.type == "HX": t_txt = f"ThermPwr: {eq.sensors.get('Thermal Power', 0):.1f} MW"
                elif eq.type == "NETWORK": t_txt = f"HeatFlow: {eq.sensors.get('Heat Flow', 0):.1f} MW"
                self.canvas.itemconfig(lbls["thermal"], text=t_txt)


        # --- NEW: Pipeline AI & Speed Logic ---
        if hasattr(self, '_pipe_segments'):
            gw = facility.get_equipment("GW-01")
            gw_flow = gw.sensors.get("Flow Rate", 0) if gw else 0
            gw_temp = gw.sensors.get("Temperature", 95) if gw else 95
            
            p101 = facility.get_equipment("P-101")
            p101_flow = p101.sensors.get("Flow Rate", 0) if p101 else gw_flow
            
            p201 = facility.get_equipment("P-201")
            p201_flow = p201.sensors.get("Flow Rate", 0) if p201 else 0
            
            p301 = facility.get_equipment("P-301")
            p301_flow = p301.sensors.get("Flow Rate", 0) if p301 else 0
            
            v101 = facility.get_equipment("V-101")
            if v101 and v101.status == "CLOSED": p101_flow = 0
            
            v201 = facility.get_equipment("V-201")
            if v201 and v201.status == "CLOSED": p201_flow = 0
            
            def get_temp_col(t):
                if t < 40: return "#118ab2"
                if t < 55: return "#06d6a0"
                if t < 75: return "#ffd166"
                if t < 90: return "#ffa600"
                return "#ff4d4d"
                
            prod_c = get_temp_col(gw_temp)
            dh_c = get_temp_col(max(gw_temp - 40, 20))
            ret_c = get_temp_col(max(gw_temp - 60, 10))
            
            def sp(pid, spd, col):
                if pid in self._pipe_segments:
                    self._pipe_segments[pid]["target_speed"] = spd
                    self._pipe_segments[pid]["target_color"] = col
                    self._pipe_segments[pid]["ai_risk"] = False
                    
            sp("prod_1", gw_flow, prod_c)
            sp("prod_2", p101_flow, prod_c)
            sp("prod_3", p101_flow, prod_c)
            sp("dh_1", p201_flow, dh_c)
            sp("dh_2", p201_flow, dh_c)
            sp("ret_1", p301_flow, ret_c)
            sp("ret_2", p301_flow, ret_c)
            
            # AI Overlays
            def set_ai(pids, eq_ids):
                risk = any((facility.get_equipment(e).failure_risk > 50 if facility.get_equipment(e) else False) for e in eq_ids)
                for pid in pids:
                    if pid in self._pipe_segments: self._pipe_segments[pid]["ai_risk"] = risk
                    
            set_ai(["prod_1", "prod_2", "prod_3"], ["GW-01", "P-101", "SEP-01"])
            set_ai(["dh_1", "dh_2"], ["HX-101", "P-201"])
            set_ai(["ret_1", "ret_2"], ["P-301", "RW-01"])
            
        self._global_pump_running = global_pump

    def _animate_tick(self):
        self._rendering_scheduler.trigger_pending()
        if not hasattr(self, '_anim_state'):
            self.canvas.after(33, self._animate_tick)
            return
            
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        
        # 1. Intelligent Pipeline Animation
        pulse = (math.sin(now * 5) + 1) / 2
        
        self.canvas.delete("chevron")
        if hasattr(self, '_pipe_segments'):
            for pid, pipe in self._pipe_segments.items():
                # Interpolate speed and color
                spd = pipe.setdefault("flow_speed", 0)
                tspd = pipe.setdefault("target_speed", 0)
                pipe["flow_speed"] += (tspd - spd) * dt * 2.0 # Smooth acceleration
                
                curr_c = pipe["current_color"]
                tar_c = pipe["target_color"]
                if curr_c != tar_c:
                    pipe["current_color"] = self._interpolate_color(curr_c, tar_c, min(dt * 2.0, 1.0))
                
                draw_col = pipe["current_color"]
                if pipe.get("ai_risk", False):
                    draw_col = self._interpolate_color(draw_col, "#f59e0b", pulse * 0.5) # subtle orange pulse
                    
                self.canvas.itemconfig(pipe["bg"], fill=draw_col)
                
                # Chevrons
                if pipe["flow_speed"] > 0.1:
                    pipe["flow_offset"] = (pipe["flow_offset"] + pipe["flow_speed"] * dt * 0.1) % 20
                    x1, y1, x2, y2 = pipe["x1"], pipe["y1"], pipe["x2"], pipe["y2"]
                    length = int(math.hypot(x2 - x1, y2 - y1))
                    
                    if length > 0:
                        dx = (x2 - x1) / length
                        dy = (y2 - y1) / length
                        
                        off = int(pipe["flow_offset"])
                        for dist in range(off, length - 4, 20):
                            cx = x1 + dx * dist
                            cy = y1 + dy * dist
                            
                            if pipe["is_vert"]:
                                dir_sign = 1 if dy > 0 else -1
                                self.canvas.create_line(cx - 4, cy, cx, cy + 6 * dir_sign, cx + 4, cy, fill=BORDER_LIGHT, width=2, tags=("chevron", "layer_pipeline"))
                            else:
                                dir_sign = 1 if dx > 0 else -1
                                self.canvas.create_line(cx, cy - 4, cx + 6 * dir_sign, cy, cx, cy + 4, fill=BORDER_LIGHT, width=2, tags=("chevron", "layer_pipeline"))

        # 2. Equipment Animations (Colors, Alarms, Rotors, Valves)
        pulse = (math.sin(now * 5) + 1) / 2 # 0.0 to 1.0 fast pulse for alarms
        
        for eq_id, anim in self._anim_state.items():
            # Color Interpolation
            curr = anim["current_color"]
            target = anim["target_color"]
            if curr != target:
                anim["current_color"] = self._interpolate_color(curr, target, min(dt * 3.0, 1.0))
            
            draw_color = anim["current_color"]
            
            # Blinking Red / Alarm Pulse effect
            if anim["is_emergency"]:
                # Interpolate to white during pulse peak
                draw_color = self._interpolate_color(target, "#ffffff", pulse * 0.7)
                
            # Apply color to box/pump outline
            self.canvas.itemconfig(f"box_bg&&{eq_id}", outline=draw_color)
            self.canvas.itemconfig(f"pump_bg&&{eq_id}", outline=draw_color)
            self.canvas.itemconfig(f"valve_bg&&{eq_id}", outline=draw_color)
            
            # Apply glow effect
            if anim["speed"] > 0 or anim["is_emergency"]:
                self.canvas.itemconfig(f"glow&&{eq_id}", state="normal", outline=draw_color)
            else:
                self.canvas.itemconfig(f"glow&&{eq_id}", state="hidden")
                
            # Apply icon
            self.canvas.itemconfig(f"status_icon&&{eq_id}", text=anim["icon"])

            # Pump Rotors
            if anim["speed"] > 0 and eq_id in self._pump_rotors:
                # Add individual angle tracker
                if "angle" not in anim: anim["angle"] = 0
                anim["angle"] = (anim["angle"] + anim["speed"] * 30 * dt) % 360
                rad = math.radians(anim["angle"])
                rad2 = math.radians(anim["angle"] + 90)
                
                l1, l2, cx, cy = self._pump_rotors[eq_id]
                rl = 14
                
                self.canvas.coords(l1, cx - rl*math.cos(rad), cy - rl*math.sin(rad), cx + rl*math.cos(rad), cy + rl*math.sin(rad))
                self.canvas.coords(l2, cx - rl*math.cos(rad2), cy - rl*math.sin(rad2), cx + rl*math.cos(rad2), cy + rl*math.sin(rad2))

            # Valves
            if hasattr(self, '_valves') and eq_id in self._valves:
                v = self._valves[eq_id]
                t_angle = anim.get("target_angle", 90)
                # Smooth rotation
                diff = t_angle - v["angle"]
                v["angle"] += diff * min(dt * 5.0, 1.0)
                
                rad = math.radians(v["angle"])
                rl = 8
                self.canvas.coords(v["flap"], v["cx"] - rl*math.cos(rad), v["cy"] - rl*math.sin(rad), v["cx"] + rl*math.cos(rad), v["cy"] + rl*math.sin(rad))

        # 3. Focus Highlight Pulse
        if hasattr(self, '_selected_equip_id') and self._selected_equip_id:
            if hasattr(self, '_highlight_expire_time') and now > self._highlight_expire_time:
                self.canvas.itemconfig(f"focus&&{self._selected_equip_id}", state="hidden")
                self._selected_equip_id = None
            else:
                pulse_color = self._interpolate_color("#22d3ee", "#34d399", pulse) # Cyan to Green glow
                w = 4 + 4 * pulse
                self.canvas.itemconfig(f"focus&&{self._selected_equip_id}", state="normal", width=w, outline=pulse_color)

        self.canvas.after(33, self._animate_tick)

    def get_rendering_metrics(self) -> dict:
        """Expose rendering diagnostics."""
        return self._rendering_scheduler.get_metrics()

