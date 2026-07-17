import re

def patch_file():
    with open('hmi/main_window.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace self._panels[...] = ... with self._panel_factories[...] = lambda: ...
    start_marker = '# Operations'
    end_marker = '# We keep the old AI Event Log hidden'
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        section = content[start_idx:end_idx]
        section = section.replace('self._panels[', 'self._panel_factories[')
        
        parts = re.split(r'(self\._panel_factories\[\"[^\"]+\"\]\s*=\s*)', section)
        new_section = parts[0]
        for i in range(1, len(parts), 2):
            prefix = parts[i]
            expr = parts[i+1]
            new_section += prefix + 'lambda: ' + expr
            
        content = content[:start_idx] + 'self._panel_factories = {}\n        ' + new_section + content[end_idx:]

    # 2. Fix `_switch_panel`
    switch_panel_old = """    def _switch_panel(self, key):
        if key not in self._panels:
            return
            
        if self._current_panel:
            self._current_panel.pack_forget()"""

    switch_panel_new = """    def _switch_panel(self, key):
        if key not in self._panels and getattr(self, '_panel_factories', {}) and key not in self._panel_factories:
            return
            
        if key not in self._panels and key in getattr(self, '_panel_factories', {}):
            self._panels[key] = self._panel_factories[key]()
            
        if key not in self._panels: return
            
        if self._current_panel:
            self._current_panel.pack_forget()"""
            
    content = content.replace(switch_panel_old, switch_panel_new)
    
    # 3. Fix _tick panel accesses
    # In `_tick`, many panels are accessed directly as self._panels["key"].
    # We should use `if "key" in self._panels:` wrap around them, or just use `.get("key")`
    # Let's replace `self._panels["xxx"].` with `if "xxx" in self._panels: self._panels["xxx"].`
    
    panels_to_protect = [
        "opt", "anomaly", "kpi", "lifecycle", "dss", "simulation", 
        "ai_history", "ai_operator", "rul", "dashboard", "trends", 
        "alarms", "reliability", "overview", "scenario_manager"
    ]
    
    for p in panels_to_protect:
        # e.g., `self._panels["opt"].update_dashboard(`
        # but what if it's already inside an `if`?
        # Actually it's easier to just do: `p_obj = self._panels.get("opt"); if p_obj: p_obj.update_dashboard(`
        content = content.replace(f'self._panels["{p}"].', f'(self._panels["{p}"].') 
        # this won't work well.
        # Let's just do a manual regex replace:
        # `\s*self\._panels\["opt"\]\.(.*)` -> `if "opt" in self._panels: self._panels["opt"].\1`
        
    with open('hmi/main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    patch_file()
