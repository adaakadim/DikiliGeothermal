import re

def patch():
    with open('hmi/main_window.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Phase 1: Convert instantiation to factories
    start_marker = 'self._panels["config_center"] = ConfigurationCenterPanel(self._content_area)'
    end_marker = 'self._ai_event_log = self._panels["events"]'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        section = content[start_idx:end_idx]
        
        parts = section.split('self._panels["')
        new_section = parts[0]
        
        for p in parts[1:]:
            eq_idx = p.find('] = ')
            if eq_idx != -1:
                key = p[:eq_idx]
                expr = p[eq_idx+4:]
                new_section += f'self._panel_factories["{key}"] = lambda: {expr}'
            else:
                new_section += 'self._panels["' + p
                
        init_str = "self._panel_factories = {}\n        "
        content = content[:start_idx] + init_str + new_section + content[end_idx:]

    # Phase 2: Update _switch_panel
    old_switch = """    def _switch_panel(self, key):
        if key not in self._panels:
            return
            
        if self._current_panel:
            self._current_panel.pack_forget()"""
            
    new_switch = """    def _switch_panel(self, key):
        if key not in self._panels and key not in getattr(self, '_panel_factories', {}):
            return
            
        if key not in self._panels and key in getattr(self, '_panel_factories', {}):
            self._panels[key] = self._panel_factories[key]()
            
        if key not in self._panels:
            return
            
        if self._current_panel:
            self._current_panel.pack_forget()"""
            
    content = content.replace(old_switch, new_switch)

    # Phase 3: Update `_tick` references
    def replacer(match):
        indent = match.group(1)
        panel = match.group(2)
        rest = match.group(3)
        return f'{indent}if "{panel}" in self._panels:\n{indent}    self._panels["{panel}"].{rest}'
        
    content = re.sub(r'^(\s*)self\._panels\["([^"]+)"\]\.(.*?)$', replacer, content, flags=re.MULTILINE)
    
    with open('hmi/main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch()
