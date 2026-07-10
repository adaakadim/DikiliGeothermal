"""
hmi/system_health/health_panel.py
=================================
Platform Health & System Monitoring Center.
Displays internal software diagnostics, resource usage, and module health.
"""

import os
import sys
import time
import platform
import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, CLR_CRITICAL, CLR_WARNING, CLR_NORMAL, FONT_SUBTITLE, FONT_LABEL, FONT_MONO_MD
from gui.i18n import tr

class HealthPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, start_time: float, historian, alarm_manager, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self.pack_propagate(False)
        self._start_time = start_time
        self._historian = historian
        self._alarm_manager = alarm_manager
        
        # Internal performance tracking
        self._prediction_times = []
        self._total_predictions = 0
        self._sim_fps_buffer = []
        self._last_tick = time.time()
        
        lbl = tk.Label(self, text=tr("SYSTEM MONITORING & PLATFORM HEALTH"), bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(pady=10, anchor="w", padx=20)
        
        # We will use a main canvas to allow scrolling if needed, or just a grid if it fits.
        # Given 10 sections, a scrollable canvas or a Notebook is best. Let's use Notebook.
        style = ttk.Style()
        style.configure("Health.TNotebook", background=BG_PRIMARY, borderwidth=0)
        style.configure("Health.TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_PRIMARY, padding=[10, 5], font=FONT_LABEL)
        style.map("Health.TNotebook.Tab", background=[("selected", BG_HEADER)])
        
        self.notebook = ttk.Notebook(self, style="Health.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._build_dashboard_tab()
        self._build_modules_tab()
        self._build_future_tab()
        
    def _build_dashboard_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Core Performance"))
        
        # Split into left and right columns
        left_col = tk.Frame(frame, bg=BG_PRIMARY)
        left_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_col = tk.Frame(frame, bg=BG_PRIMARY)
        right_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # --- App Performance ---
        app_frm = tk.LabelFrame(left_col, text="Application Performance", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        app_frm.pack(fill="x", pady=5)
        self.lbl_cpu = self._make_kv(app_frm, "CPU Usage", "0.0%")
        self.lbl_ram = self._make_kv(app_frm, "Memory (RAM)", "0 MB")
        self.lbl_threads = self._make_kv(app_frm, "Active Threads", "0")
        self._make_kv(app_frm, "Process ID", str(os.getpid()))
        self._make_kv(app_frm, "Python Version", platform.python_version())
        self._make_kv(app_frm, "Operating System", platform.system() + " " + platform.release())
        
        # --- System Health ---
        sys_frm = tk.LabelFrame(left_col, text="System Health Dashboard", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        sys_frm.pack(fill="x", pady=5)
        self.lbl_health_score = self._make_kv(sys_frm, "Overall System Health", "100%", color=CLR_NORMAL)
        self.lbl_uptime = self._make_kv(sys_frm, "Platform Uptime", "00:00:00")
        self.lbl_app_status = self._make_kv(sys_frm, "Application Status", "RUNNING", color=CLR_NORMAL)
        
        # --- AI Performance ---
        ai_frm = tk.LabelFrame(right_col, text="AI Engine Performance", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        ai_frm.pack(fill="x", pady=5)
        self.lbl_ai_last = self._make_kv(ai_frm, "Last Prediction", "Never")
        self.lbl_ai_avg = self._make_kv(ai_frm, "Avg Latency", "0 ms")
        self.lbl_ai_count = self._make_kv(ai_frm, "Total Predictions", "0")
        self._make_kv(ai_frm, "Active Model", "dikili_rf_v2.pkl")
        self._make_kv(ai_frm, "SHAP Explainability", "AVAILABLE")
        
        # --- Event Counters ---
        evt_frm = tk.LabelFrame(right_col, text="Event Counters", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        evt_frm.pack(fill="x", pady=5)
        self.lbl_cnt_alarms = self._make_kv(evt_frm, "Total Alarms (Active)", "0")
        self.lbl_cnt_events = self._make_kv(evt_frm, "Total Events Logged", "0")
        
    def _build_modules_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Module Status & DB"))
        
        left_col = tk.Frame(frame, bg=BG_PRIMARY)
        left_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_col = tk.Frame(frame, bg=BG_PRIMARY)
        right_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # --- Historian Performance ---
        hist_frm = tk.LabelFrame(left_col, text="Historian Performance", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        hist_frm.pack(fill="x", pady=5)
        self.lbl_db_size = self._make_kv(hist_frm, "Database Size", "Unknown")
        self.lbl_db_records = self._make_kv(hist_frm, "Stored Records (Approx)", "Unknown")
        self.lbl_db_health = self._make_kv(hist_frm, "Storage Health", "OPTIMAL", color=CLR_NORMAL)
        
        # --- Simulation Performance ---
        sim_frm = tk.LabelFrame(left_col, text="Simulation Engine", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        sim_frm.pack(fill="x", pady=5)
        self.lbl_sim_fps = self._make_kv(sim_frm, "Simulation FPS", "0.0")
        self.lbl_sim_delay = self._make_kv(sim_frm, "Processing Delay", "0 ms")
        
        # --- Live Status Indicators ---
        stat_frm = tk.LabelFrame(right_col, text="Live Status Indicators", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL)
        stat_frm.pack(fill="x", pady=5)
        
        modules = ["Configuration", "Logging", "Simulation", "Dashboard", "Historian", "Alarm Manager", "Digital Twin", "AI Engine", "Decision Support", "Optimization", "SHAP"]
        self.status_indicators = {}
        
        for i, mod in enumerate(modules):
            tk.Label(stat_frm, text=mod, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).grid(row=i, column=0, sticky="e", padx=10, pady=2)
            lbl = tk.Label(stat_frm, text="READY", bg=BG_SECONDARY, fg=CLR_NORMAL, font=FONT_MONO_MD)
            lbl.grid(row=i, column=1, sticky="w", padx=10, pady=2)
            self.status_indicators[mod] = lbl

    def _build_future_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Extensibility"))
        
        lbl = tk.Label(frame, text="Future Architecture Interfaces Prepared", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        lbl.pack(pady=20)
        
        features = [
            ("Cloud Deployment Interface", "NOT CONFIGURED"),
            ("Docker Container Telemetry", "NOT CONFIGURED"),
            ("Remote Monitoring Access", "NOT CONFIGURED"),
            ("Distributed AI Services", "NOT CONFIGURED"),
            ("Multi-Node SCADA Sync", "NOT CONFIGURED")
        ]
        
        container = tk.Frame(frame, bg=BG_SECONDARY, padx=20, pady=20)
        container.pack()
        
        for name, stat in features:
            f = tk.Frame(container, bg=BG_SECONDARY)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=name, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL, width=30, anchor="w").pack(side="left")
            tk.Label(f, text=stat, bg=BG_SECONDARY, fg=TEXT_MUTED, font=FONT_MONO_MD).pack(side="left")

    def _make_kv(self, parent, key, val, color=TEXT_PRIMARY):
        f = tk.Frame(parent, bg=BG_SECONDARY)
        f.pack(fill="x", pady=2, padx=10)
        tk.Label(f, text=key+":", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left")
        lbl = tk.Label(f, text=val, bg=BG_SECONDARY, fg=color, font=FONT_MONO_MD)
        lbl.pack(side="right")
        return lbl

    def _update_historian_metrics(self):
        if not self._historian or not self._historian._conn:
            self.lbl_db_health.config(text="OFFLINE", fg=CLR_CRITICAL)
            self.status_indicators["Historian"].config(text="ERROR", fg=CLR_CRITICAL)
            return
            
        try:
            db_path = getattr(self._historian, 'db_path', "data/historian.db")
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                self.lbl_db_size.config(text=f"{size_mb:.2f} MB")
                
                # If size is approaching 1GB, internal alert
                if size_mb > 900:
                    self.lbl_db_health.config(text="WARNING (Near Limit)", fg=CLR_WARNING)
                    self._alarm_manager.record_event("SYSTEM", "DIAGNOSTICS", f"Historian size approaching 1GB ({size_mb:.1f} MB)")
            
            c = self._historian._conn.cursor()
            c.execute("SELECT COUNT(*) FROM sensor_readings")
            count = c.fetchone()[0]
            self.lbl_db_records.config(text=f"{count:,}")
        except Exception:
            pass

    def update_metrics(self, ai_result=None):
        """Called periodically by main window loop"""
        now = time.time()
        
        # App Performance (psutil)
        if HAS_PSUTIL:
            proc = psutil.Process(os.getpid())
            cpu = proc.cpu_percent()
            mem = proc.memory_info().rss / (1024 * 1024)
            th_count = proc.num_threads()
            
            self.lbl_cpu.config(text=f"{cpu:.1f}%")
            self.lbl_ram.config(text=f"{mem:.1f} MB")
            self.lbl_threads.config(text=str(th_count))
            
            # Software Alerts
            if cpu > 85.0:
                self._alarm_manager.record_event("SYSTEM", "DIAGNOSTICS", f"High CPU Usage detected: {cpu:.1f}%")
            if mem > 1024: # 1GB
                self._alarm_manager.record_event("SYSTEM", "DIAGNOSTICS", f"High Memory Usage detected: {mem:.1f} MB")
        
        # Uptime
        uptime = int(now - self._start_time)
        hours = uptime // 3600
        mins = (uptime % 3600) // 60
        secs = uptime % 60
        self.lbl_uptime.config(text=f"{hours:02d}:{mins:02d}:{secs:02d}")
        
        # AI Performance
        if ai_result:
            self._total_predictions += 1
            latency = ai_result.get("processing_time_ms", 0) # If available
            self._prediction_times.append(latency)
            if len(self._prediction_times) > 100: self._prediction_times.pop(0)
            avg_lat = sum(self._prediction_times) / len(self._prediction_times) if self._prediction_times else 0
            
            self.lbl_ai_last.config(text=datetime.now().strftime("%H:%M:%S"))
            self.lbl_ai_count.config(text=str(self._total_predictions))
            self.lbl_ai_avg.config(text=f"{avg_lat:.1f} ms")
            
            if avg_lat > 2000:
                self._alarm_manager.record_event("SYSTEM", "DIAGNOSTICS", f"AI Latency high: {avg_lat:.0f} ms")
        
        # Simulation FPS
        dt = now - self._last_tick
        self._last_tick = now
        fps = 1.0 / dt if dt > 0 else 0
        self._sim_fps_buffer.append(fps)
        if len(self._sim_fps_buffer) > 10: self._sim_fps_buffer.pop(0)
        avg_fps = sum(self._sim_fps_buffer)/len(self._sim_fps_buffer)
        self.lbl_sim_fps.config(text=f"{avg_fps:.1f}")
        self.lbl_sim_delay.config(text=f"{dt*1000:.0f} ms")
        
        # Event Counters
        stats = self._alarm_manager.get_statistics()
        self.lbl_cnt_alarms.config(text=str(stats.get('active_count', 0)))
        self.lbl_cnt_events.config(text=str(len(self._alarm_manager.event_history)))
        
        # Less frequent updates (e.g. DB size)
        if uptime % 5 == 0:
            self._update_historian_metrics()
