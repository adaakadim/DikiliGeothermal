import re
import math

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\visualization\diagram.py'

# I will write a custom script to inject the required animation logic into diagram.py

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
if 'import time' not in content:
    content = content.replace('import math\n', 'import math\nimport time\n')

# 2. Add Valve drawing to _draw_static
# y_well, y_p101, etc.
valve_logic = """
        # --- NEW: Valves ---
        y_v101 = y_well + 30 * s
        self._draw_valve(cx, y_v101, "V-101", "Production Valve", "interactive_V-101")
        
        y_v201 = y_p201 + 50 * s
        self._draw_valve(cx, y_v201, "V-201", "DH Return Valve", "interactive_V-201")
        # -------------------
"""
content = content.replace('        self._draw_pump(cx, y_p101', valve_logic + '        self._draw_pump(cx, y_p101')

# Add _draw_valve method
draw_valve_method = """
    def _draw_valve(self, cx, cy, vid, name, tag):
        w = 16
        h = 12
        # Bowtie shape
        bg = self.canvas.create_polygon(cx-w, cy-h, cx-w, cy+h, cx+w, cy-h, cx+w, cy+h, fill=BG_SECONDARY, outline=BORDER, width=2, tags=(tag, "valve_bg", vid))
        # Center circle
        c = self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=TEXT_PRIMARY, tags=(tag, "valve_center", vid))
        
        lbl = self.canvas.create_text(cx + 30, cy, text=name, fill=TEXT_SECONDARY, font=FONT_MONO_SM, anchor="w", tags=(tag,))
        self._equip_boxes[vid] = bg
        
        # Flap for animation
        flap = self.canvas.create_line(cx, cy - 8, cx, cy + 8, fill=CLR_CRITICAL, width=3, tags=(tag, "valve_flap", vid))
        
        # Status icon
        icon = self.canvas.create_text(cx - 30, cy, text="", fill=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="e", tags=(tag, "status_icon", vid))
        
        if not hasattr(self, '_valves'): self._valves = {}
        self._valves[vid] = {"flap": flap, "angle": 90, "target_angle": 90, "icon": icon, "bg": bg, "cx": cx, "cy": cy}
"""
content = content.replace('    def _draw_pipe_vertical', draw_valve_method + '\n    def _draw_pipe_vertical')

# 3. Enhance _draw_pump and _draw_box with status icons and glows
# For _draw_pump:
pump_enhancement = """
        # Outer glow
        glow = self.canvas.create_oval(cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6, fill="", outline=CLR_NORMAL, width=2, state="hidden", tags=(tag, "glow", pid))
        
        box = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=BG_SECONDARY, outline=BORDER, width=2, tags=(tag, "pump_bg", pid))
        
        # Status icon
        icon = self.canvas.create_text(cx - r - 20, cy - 20, text="", fill=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="e", tags=(tag, "status_icon", pid))
"""
content = re.sub(r'        box = self\.canvas\.create_oval\(cx - r, cy - r.*?pump_bg"\)\)', pump_enhancement, content, flags=re.DOTALL)

# For _draw_box:
box_enhancement = """
        w = 140
        h = 24
        
        # Outer glow
        glow = self.canvas.create_rectangle(cx - w - 4, cy - h - 4, cx + w + 4, cy + h + 4, fill="", outline=CLR_NORMAL, width=2, state="hidden", tags=(tag, "glow", wid))
        
        box = self.canvas.create_rectangle(cx - w, cy - h, cx + w, cy + h, fill=BG_SECONDARY, outline=BORDER, width=2, tags=(tag, "box_bg", wid))
        
        # Status icon
        icon = self.canvas.create_text(cx - w - 10, cy, text="", fill=TEXT_PRIMARY, font=FONT_LABEL_SM, anchor="e", tags=(tag, "status_icon", wid))
"""
content = re.sub(r'        w = 140\n        h = 24\n        \n        box = self\.canvas\.create_rectangle\(cx - w.*?box_bg"\)\)', box_enhancement, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied initial static drawing enhancements.")
