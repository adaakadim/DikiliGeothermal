import sys

with open('C:/Users/kadim/.gemini/antigravity-ide/scratch/DikiliGeothermal/gui/widgets.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

correct_tail = """    def _draw(self):
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
        self._led_id = self.canvas.create_oval(2, 2, size - 2, size - 2, fill=CLR_OFFLINE, outline=BORDER_LIGHT, width=1)

    def set_status(self, health: str):
        colors = {"GOOD": CLR_NORMAL, "WARNING": CLR_WARNING, "CRITICAL": CLR_CRITICAL, "OFFLINE": CLR_OFFLINE}
        self.canvas.itemconfig(self._led_id, fill=colors.get(health, CLR_OFFLINE))

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
"""

with open('C:/Users/kadim/.gemini/antigravity-ide/scratch/DikiliGeothermal/gui/widgets.py', 'w', encoding='utf-8') as f:
    f.writelines(lines[:264])
    f.write(correct_tail)
