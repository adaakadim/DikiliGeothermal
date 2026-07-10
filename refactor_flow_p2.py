import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\visualization\diagram.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update update_from_twin to handle pipe logic
update_twin_patch = """
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
                if t < 40: return "#3b82f6"
                if t < 70: return "#10b981"
                if t < 100: return "#fbbf24"
                if t < 130: return "#f59e0b"
                return "#ef4444"
                
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
            
        self._global_pump_running = global_pump"""

content = content.replace("        self._global_pump_running = global_pump", update_twin_patch)

# Update _animate_tick to remove global chevrons and add segmented logic
old_anim_block = """        # 1. Flow Chevrons
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
                        self.canvas.create_line(x - 4, y, x, y + 6, x + 4, y, fill=BORDER_LIGHT, width=2, tags=("chevron", "layer_pipeline"))"""

new_anim_block = """        # 1. Intelligent Pipeline Animation
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
                if pipe["flow_speed"] > 5:
                    pipe["flow_offset"] = (pipe["flow_offset"] + pipe["flow_speed"] * dt * 0.5) % 20
                    x = pipe["x"]
                    y1 = pipe["y1"]
                    y2 = pipe["y2"]
                    for y in range(int(y1) + int(pipe["flow_offset"]), int(y2) - 4, 20):
                        self.canvas.create_line(x - 4, y, x, y + 6, x + 4, y, fill=BORDER_LIGHT, width=2, tags=("chevron", "layer_pipeline"))"""

content = content.replace(old_anim_block, new_anim_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated update_from_twin and _animate_tick in diagram.py")
