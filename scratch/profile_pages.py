import time
import sys
import psutil
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from hmi.main_window import SCADAGuiApp
from core.config.system_config import SystemConfig

def measure_panel_init():
    root = tk.Tk()
    config = SystemConfig.load()
    
    # We will instantiate each panel manually and measure time
    panels = {
        "dashboard": "scada.dashboard.SCADADashboard",
        "alarms": "gui.alarm_panel.AlarmPanel",
        "trends": "gui.trend_panel.TrendPanel",
        "kpi": "gui.kpi_dashboard.KPIDashboard",
        "digital_twin": "gui.digital_twin_panel.DigitalTwinPanel",
        "ai_operator": "gui.ai_operator_panel.AIOperatorPanel",
        "scenario": "gui.scenario_manager_panel.ScenarioManagerPanel",
        "reporting": "gui.reporting_panel.ReportingPanel",
        "config": "gui.config_center_panel.ConfigCenterPanel",
        "playback": "gui.historical_playback_panel.HistoricalPlaybackPanel"
    }
    
    print("PAGE LOAD TIMES:")
    for name, class_path in panels.items():
        module_name, class_name = class_path.rsplit('.', 1)
        try:
            mod = __import__(module_name, fromlist=[class_name])
            cls = getattr(mod, class_name)
            
            t0 = time.perf_counter()
            if name == "dashboard":
                p = cls(root, ["W-01", "W-02", "W-03"])
            elif name == "alarms":
                # Need an alarm manager
                from scada.alarm_manager import AlarmManager
                p = cls(root, AlarmManager())
            elif name == "reporting":
                # Need dummy objects
                class Dummy: pass
                d = Dummy()
                d._generate = lambda: None
                p = cls(root, d)
            else:
                try:
                    p = cls(root)
                except TypeError:
                    p = cls(root, None) # Try passing None if it requires an argument
                    
            t1 = time.perf_counter()
            print(f"[{name.upper()}] Load Time: {(t1 - t0)*1000:.2f} ms")
        except Exception as e:
            print(f"[{name.upper()}] Load Error: {e}")

if __name__ == "__main__":
    process = psutil.Process(os.getpid())
    t0 = time.perf_counter()
    measure_panel_init()
    t1 = time.perf_counter()
    print(f"\nTotal Initialization Time: {(t1 - t0):.2f} s")
    print(f"Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
