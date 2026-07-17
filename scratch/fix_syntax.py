import sys

def fix():
    with open('hmi/main_window.py', 'r', encoding='utf-8') as f:
        c = f.read()
    c = c.replace('\"\"] =', '\"] =')
    
    # Check for `self._ai_event_log = self._panels["events"]` syntax error if events hasn't been instantiated
    # It should be `self._ai_event_log = self._panels.get("events")`
    c = c.replace('self._ai_event_log = self._panels["events"]', 'self._ai_event_log = self._panels.get("events")')
    
    with open('hmi/main_window.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == "__main__":
    fix()
