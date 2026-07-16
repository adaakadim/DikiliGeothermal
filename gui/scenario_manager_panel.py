import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb
from datetime import datetime

from gui.theme import FONT_TITLE, FONT_LABEL, BG_PRIMARY
from simulation.models.scenario_manager import ScenarioManager, Scenario

class ScenarioManagerPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, scenario_manager: ScenarioManager, on_scenario_event_cb=None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        self.manager = scenario_manager
        self.on_scenario_event_cb = on_scenario_event_cb
        
        self._build_ui()
        self.refresh_list()
        
    def _build_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="SCENARIO MANAGER", font=FONT_TITLE).pack(side=tk.LEFT)
        
        # Split pane
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Top: Scenario List
        list_frame = ttk.LabelFrame(paned, text="Available Scenarios", padding=10)
        paned.add(list_frame, weight=3)
        
        columns = ("name", "category", "status", "severity", "duration")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Scenario Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("status", text="Status")
        self.tree.heading("severity", text="Severity")
        self.tree.heading("duration", text="Duration (m)")
        
        self.tree.column("name", width=250)
        self.tree.column("category", width=100)
        self.tree.column("status", width=100)
        self.tree.column("severity", width=100)
        self.tree.column("duration", width=100)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Controls
        ctrl_frame = ttk.Frame(list_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(ctrl_frame, text="▶ Activate", command=self._activate).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="⏹ Stop", command=self._stop).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="⏸ Pause", command=self._pause).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="🔄 Reset", command=self._reset).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(ctrl_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        ttk.Button(ctrl_frame, text="➕ Build Custom", command=self._build_custom).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="🗑 Delete Custom", command=self._delete).pack(side=tk.LEFT, padx=5)
        
        # Bottom: Timeline
        timeline_frame = ttk.LabelFrame(paned, text="Active Scenario Timeline", padding=10)
        paned.add(timeline_frame, weight=1)
        
        self.lbl_active_name = ttk.Label(timeline_frame, text="No Active Scenario", font=FONT_TITLE)
        self.lbl_active_name.pack(anchor="w", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(timeline_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        stats_frame = ttk.Frame(timeline_frame)
        stats_frame.pack(fill=tk.X)
        self.lbl_start = ttk.Label(stats_frame, text="Start: --:--:--")
        self.lbl_start.pack(side=tk.LEFT)
        
        self.lbl_state = ttk.Label(stats_frame, text="State: STOPPED")
        self.lbl_state.pack(side=tk.LEFT, expand=True)
        
        self.lbl_end = ttk.Label(stats_frame, text="End: --:--:--")
        self.lbl_end.pack(side=tk.RIGHT)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for sid, sc in self.manager.scenarios.items():
            self.tree.insert("", "end", iid=sid, values=(sc.name, sc.category, sc.status, sc.severity, sc.duration_mins))
            
    def _get_selected(self):
        sel = self.tree.selection()
        if sel:
            return sel[0]
        return None
        
    def _activate(self):
        sid = self._get_selected()
        if not sid: return
        sc = self.manager.scenarios[sid]
        
        if sc.name == "Emergency Shutdown":
            if not mb.askyesno("Confirm Shutdown", "Are you sure you want to trigger Emergency Shutdown?"):
                return
                
        self.manager.activate(sid)
        if self.on_scenario_event_cb:
            self.on_scenario_event_cb(sc, "ACTIVATED")
        self.refresh_list()
        
    def _stop(self):
        sc = self.manager.active_scenario
        if sc:
            self.manager.stop()
            if self.on_scenario_event_cb:
                self.on_scenario_event_cb(sc, "STOPPED")
            self.refresh_list()
            
    def _pause(self):
        self.manager.pause()
        self.refresh_list()
        
    def _reset(self):
        sid = self._get_selected()
        if not sid: return
        if mb.askyesno("Confirm Reset", "Reset this scenario to start?"):
            self.manager.reset_scenario(sid)
            self.refresh_list()
            
    def _delete(self):
        sid = self._get_selected()
        if not sid: return
        if self.manager.scenarios[sid].category != "CUSTOM":
            mb.showerror("Error", "Only Custom Scenarios can be deleted.")
            return
            
        if mb.askyesno("Confirm Delete", "Delete this custom scenario forever?"):
            self.manager.delete(sid)
            self.refresh_list()
            
    def _build_custom(self):
        CustomScenarioBuilder(self.winfo_toplevel(), self.manager, self.refresh_list)

    def update_dashboard(self):
        """Called by tick loop to update timeline"""
        self.refresh_list() # Just to update statuses
        
        sc = self.manager.active_scenario
        if not sc:
            self.lbl_active_name.config(text="No Active Scenario")
            self.progress_var.set(0)
            self.lbl_start.config(text="Start: --:--:--")
            self.lbl_state.config(text="State: STOPPED")
            self.lbl_end.config(text="End: --:--:--")
        else:
            self.lbl_active_name.config(text=f"Active: {sc.name}")
            prog = sc.get_progress_pct()
            self.progress_var.set(prog)
            
            st = sc.start_time.strftime("%H:%M:%S") if sc.start_time else "--:--:--"
            self.lbl_start.config(text=f"Start: {st}")
            self.lbl_state.config(text=f"State: {sc.status} ({prog:.1f}%)")
            
            if sc.start_time and sc.duration_mins > 0:
                from datetime import timedelta
                et = (sc.start_time + timedelta(minutes=sc.duration_mins)).strftime("%H:%M:%S")
                self.lbl_end.config(text=f"End: {et}")
            else:
                self.lbl_end.config(text="End: Indefinite")


class CustomScenarioBuilder(tk.Toplevel):
    def __init__(self, parent, manager: ScenarioManager, on_save_cb):
        super().__init__(parent)
        self.title("Build Custom Scenario")
        self.geometry("400x500")
        self.manager = manager
        self.on_save_cb = on_save_cb
        
        self.configure(bg=BG_PRIMARY)
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
        
    def _build_ui(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="Name:").pack(anchor="w", pady=(0, 5))
        self.ent_name = ttk.Entry(f, width=40)
        self.ent_name.pack(fill=tk.X, pady=(0, 15))
        self.ent_name.insert(0, "My Custom Scenario")
        
        ttk.Label(f, text="Equipment:").pack(anchor="w", pady=(0, 5))
        self.cb_eq = ttk.Combobox(f, values=["ALL", "PW-101", "PW-102", "P-101", "HX-101", "VALVES", "SENSORS"], state="readonly")
        self.cb_eq.pack(fill=tk.X, pady=(0, 15))
        self.cb_eq.set("ALL")
        
        ttk.Label(f, text="Subsystem:").pack(anchor="w", pady=(0, 5))
        self.cb_sys = ttk.Combobox(f, values=["GLOBAL", "RESERVOIR", "PRODUCTION", "INJECTION", "DISTRICT_HEATING"], state="readonly")
        self.cb_sys.pack(fill=tk.X, pady=(0, 15))
        self.cb_sys.set("GLOBAL")
        
        ttk.Label(f, text="Severity:").pack(anchor="w", pady=(0, 5))
        self.cb_sev = ttk.Combobox(f, values=["LOW", "MEDIUM", "HIGH", "CRITICAL"], state="readonly")
        self.cb_sev.pack(fill=tk.X, pady=(0, 15))
        self.cb_sev.set("HIGH")
        
        ttk.Label(f, text="Duration (Minutes):").pack(anchor="w", pady=(0, 5))
        self.var_dur = tk.IntVar(value=30)
        ttk.Entry(f, textvariable=self.var_dur).pack(fill=tk.X, pady=(0, 20))
        
        btn_frame = ttk.Frame(f)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Save Scenario", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
    def _save(self):
        name = self.ent_name.get()
        if not name:
            mb.showerror("Error", "Name required.")
            return
            
        sc = Scenario(
            name=name,
            affected_equipment=self.cb_eq.get(),
            affected_subsystem=self.cb_sys.get(),
            severity=self.cb_sev.get(),
            duration_mins=self.var_dur.get()
        )
        self.manager.add_custom(sc)
        self.on_save_cb()
        self.destroy()
