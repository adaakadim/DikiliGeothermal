import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\visualization\diagram.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update _draw_box
box_repl = """        self.canvas.create_text(cx, cy - 12, text=name.upper(), fill=TEXT_PRIMARY, font=FONT_LABEL, anchor="center", tags=(tag,))
        lbl = self.canvas.create_text(cx, cy + 12, text="---", fill=TEXT_SECONDARY, font=FONT_MONO_MD, anchor="center", tags=(tag,))
        
        # Layer labels - Moved sensor to left, removed AI
        sensor_lbl = self.canvas.create_text(cx - 150, cy, text="", fill=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="e", tags=(tag, "layer_sensor"))
        alarm_lbl = self.canvas.create_text(cx, cy - 30, text="", fill=CLR_CRITICAL, font=FONT_LABEL_SM, anchor="s", tags=(tag, "layer_alarm"))
        maint_lbl = self.canvas.create_text(cx + 150, cy - 10, text="", fill="#34d399", font=FONT_MONO_SM, anchor="sw", tags=(tag, "layer_maintenance"))
        thermal_lbl = self.canvas.create_text(cx + 150, cy + 10, text="", fill="#f87171", font=FONT_MONO_SM, anchor="nw", tags=(tag, "layer_thermal"))
        
        self._labels[wid] = {
            "info": lbl,
            "sensor": sensor_lbl,
            "alarm": alarm_lbl,
            "maintenance": maint_lbl,
            "thermal": thermal_lbl
        }
        return box"""
content = re.sub(r'        self\.canvas\.create_text\(cx, cy - 12.*?return box', box_repl, content, flags=re.DOTALL)


# 2. Update _draw_pump
pump_repl = """        self.canvas.create_text(cx + r + 20, cy - 8, text=name.upper(), fill=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="w", tags=(tag,))
        lbl = self.canvas.create_text(cx + r + 20, cy + 8, text="---", fill=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="w", tags=(tag,))
        
        # Layer labels - Moved sensor to left, removed AI
        sensor_lbl = self.canvas.create_text(cx - r - 20, cy, text="", fill=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="e", tags=(tag, "layer_sensor"))
        alarm_lbl = self.canvas.create_text(cx, cy - r - 10, text="", fill=CLR_CRITICAL, font=FONT_LABEL_SM, anchor="s", tags=(tag, "layer_alarm"))
        maint_lbl = self.canvas.create_text(cx + r + 150, cy - 10, text="", fill="#34d399", font=FONT_MONO_SM, anchor="sw", tags=(tag, "layer_maintenance"))
        thermal_lbl = self.canvas.create_text(cx + r + 150, cy + 10, text="", fill="#f87171", font=FONT_MONO_SM, anchor="nw", tags=(tag, "layer_thermal"))

        self._labels[pid] = {
            "info": lbl,
            "sensor": sensor_lbl,
            "alarm": alarm_lbl,
            "maintenance": maint_lbl,
            "thermal": thermal_lbl
        }
        return box"""
content = re.sub(r'        self\.canvas\.create_text\(cx \+ r \+ 20, cy - 8.*?return box', pump_repl, content, flags=re.DOTALL)


# 3. Update update_from_twin to remove ai_txt update
twin_orig = """                self.canvas.itemconfig(lbls["sensor"], text=s_txt)
                
                ai_txt = f"Risk: {eq.failure_risk:.1f}% | Hlth: {eq.health_score:.1f}%\\nConf: {eq.ai_confidence:.1f}%" if eq.failure_risk > 0 or eq.ai_confidence > 0 else ""
                self.canvas.itemconfig(lbls["ai"], text=ai_txt)
                
                alarm_txt = "⚠️ " + eq.alarms[0] if eq.alarms else "" """
                
twin_repl = """                self.canvas.itemconfig(lbls["sensor"], text=s_txt)
                
                alarm_txt = "⚠️ " + eq.alarms[0] if eq.alarms else "" """
content = content.replace(twin_orig, twin_repl)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("diagram.py updated.")
