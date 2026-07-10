import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\visualization\diagram.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace update_from_twin and _animate_tick completely
new_methods = """
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
                if eq.status == "OFFLINE":
                    s_txt = "OFFLINE"
                else:
                    if eq.type == "WELL":
                        s_txt = f"T: {eq.sensors.get('Temperature', 0):.1f}°C | P: {eq.sensors.get('Pressure', 0):.1f}bar\\nF: {eq.sensors.get('Flow Rate', 0):.1f}m³/h"
                    elif eq.type == "PUMP":
                        s_txt = f"F: {eq.sensors.get('Flow Rate', 0):.1f}m³/h | I: {eq.motor_current:.1f}A\\nP: {eq.power_consumption:.1f}kW"
                    elif eq.type == "SEPARATOR":
                        s_txt = f"P: {eq.sensors.get('Pressure', 0):.1f}bar"
                    elif eq.type == "HX":
                        s_txt = f"Eff: {eq.sensors.get('Efficiency', 0):.1f}%"
                    elif eq.type == "NETWORK":
                        s_txt = f"ΔT: {eq.sensors.get('Delta T', 0):.1f}K"
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

        self._global_pump_running = global_pump

    def _animate_tick(self):
        if not hasattr(self, '_anim_state'):
            self.canvas.after(33, self._animate_tick)
            return
            
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        
        # 1. Flow Chevrons
        if self._global_pump_running:
            self._flow_offset = (self._flow_offset + 50 * dt) % 20
            self.canvas.delete("chevron")
            for temp_type in ("hot", "warm", "cool"):
                lines = self.canvas.find_withtag(f"pipe_{temp_type}")
                for line in lines:
                    coords = self.canvas.coords(line)
                    if not coords: continue
                    x, y1, _, y2 = coords
                    for y in range(int(y1) + int(self._flow_offset), int(y2) - 4, 20):
                        self.canvas.create_line(x - 4, y, x, y + 6, x + 4, y, fill=BORDER_LIGHT, width=2, tags=("chevron", "layer_pipeline"))

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
                anim["angle"] = (anim["angle"] + anim["speed"] * 100 * dt) % 360
                rad = math.radians(anim["angle"])
                rad2 = math.radians(anim["angle"] + 90)
                
                l1, l2 = self._pump_rotors[eq_id]
                rl = 14
                
                if eq_id == "P-101": cy = self._y_p101
                elif eq_id == "P-201": cy = self._y_p201
                elif eq_id == "P-301": cy = self._y_p301
                
                cx = self._width // 2
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

        self.canvas.after(33, self._animate_tick)
"""

content = re.sub(r'    # ── Dynamic updates from Digital Twin ──────────────────────────────────.*', new_methods, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied animation engine to diagram.py")
