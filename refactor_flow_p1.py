import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\visualization\diagram.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update _draw_pipe_vertical
pipe_func = """    def _draw_pipe_vertical(self, x: int, y1: int, y2: int, pipe_id: str, default_temp: str = "hot"):
        colors = {"hot": CLR_HOT_FLUID, "warm": CLR_WARM_FLUID, "cool": CLR_COOL_FLUID}
        bg_col = colors.get(default_temp, CLR_PIPE_BG)
        bg = self.canvas.create_rectangle(x - PIPE_WIDTH // 2, y1, x + PIPE_WIDTH // 2, y2, fill=bg_col, outline=BORDER, tags=("layer_pipeline", f"pipe_bg_{pipe_id}"))
        line = self.canvas.create_line(x, y1, x, y2, fill="", tags=("pipe_line", "layer_pipeline", f"pipe_line_{pipe_id}"))
        
        if not hasattr(self, '_pipe_segments'): self._pipe_segments = {}
        self._pipe_segments[pipe_id] = {
            "bg": bg, "line": line, "x": x, "y1": y1, "y2": y2,
            "flow_offset": 0.0, "flow_speed": 0.0, 
            "current_color": bg_col, "target_color": bg_col
        }"""
        
content = re.sub(r'    def _draw_pipe_vertical\(self, x: int, y1: int, y2: int, temp: str = "hot"\):.*?self\.canvas\.create_line\(x, y1, x, y2, fill="", tags=\(f"pipe_{temp}", "layer_pipeline"\)\)', pipe_func, content, flags=re.DOTALL)

# 2. Update calls to _draw_pipe_vertical
content = content.replace('self._draw_pipe_vertical(cx, y_well + h2, y_p101 - pr, "hot")', 'self._draw_pipe_vertical(cx, y_well + h2, y_p101 - pr, "prod_1", "hot")')
content = content.replace('self._draw_pipe_vertical(cx, y_p101 + pr, y_sep - h2, "hot")', 'self._draw_pipe_vertical(cx, y_p101 + pr, y_sep - h2, "prod_2", "hot")')
content = content.replace('self._draw_pipe_vertical(cx, y_sep + h2, y_hx - h2, "hot")', 'self._draw_pipe_vertical(cx, y_sep + h2, y_hx - h2, "prod_3", "hot")')
content = content.replace('self._draw_pipe_vertical(cx, y_hx + h2, y_p201 - pr, "warm")', 'self._draw_pipe_vertical(cx, y_hx + h2, y_p201 - pr, "dh_1", "warm")')
content = content.replace('self._draw_pipe_vertical(cx, y_p201 + pr, y_dh - h2, "warm")', 'self._draw_pipe_vertical(cx, y_p201 + pr, y_dh - h2, "dh_2", "warm")')
content = content.replace('self._draw_pipe_vertical(cx, y_dh + h2, y_p301 - pr, "cool")', 'self._draw_pipe_vertical(cx, y_dh + h2, y_p301 - pr, "ret_1", "cool")')
content = content.replace('self._draw_pipe_vertical(cx, y_p301 + pr, y_rw - h2, "cool")', 'self._draw_pipe_vertical(cx, y_p301 + pr, y_rw - h2, "ret_2", "cool")')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated pipe segments in diagram.py")
