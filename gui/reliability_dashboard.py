import tkinter as tk
from tkinter import ttk
import csv
import json
from datetime import datetime
import os

from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, BORDER_LIGHT
from gui.theme import FONT_TITLE, FONT_LABEL, FONT_MONO_MD, FONT_MONO_SM, FONT_HEADER_BAR
from gui.theme import CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE, CLR_INFO
from core.data_quality.validation_engine import ValidationEngine, HealthState
from core.diagnostics.communication_monitor import CommunicationMonitor, ModuleStatus
from core.safety.fail_safe import FailSafeManager, SafeMode
from core.diagnostics.auto_recovery import SelfDiagnosticsEngine

class ReliabilityDashboard(tk.Frame):
    def __init__(self, parent, val_engine: ValidationEngine, comm_monitor: CommunicationMonitor, fail_safe: FailSafeManager, auto_rec: SelfDiagnosticsEngine, *args, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, *args, **kwargs)
        
        self.val_engine = val_engine
        self.comm_monitor = comm_monitor
        self.fail_safe = fail_safe
        self.auto_rec = auto_rec
        
        self.export_dir = "scratch"
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            
        self._build_ui()
        self._timeline_events = []
        
    def _build_ui(self):
        # ─── Top Toolbar (Export) ───
        toolbar = tk.Frame(self, bg=BG_HEADER, height=45)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        
        tk.Label(toolbar, text=" INDUSTRIAL RELIABILITY DASHBOARD ", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_HEADER_BAR).pack(side="left", padx=10)
        
        # Export Buttons
        btn_frame = tk.Frame(toolbar, bg=BG_HEADER)
        btn_frame.pack(side="right", padx=10)
        
        tk.Button(btn_frame, text="Export CSV", bg="#374151", fg="white", font=FONT_LABEL, cursor="hand2", relief="flat", command=self.export_csv).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export Excel", bg="#10b981", fg="white", font=FONT_LABEL, cursor="hand2", relief="flat", command=self.export_excel).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export PDF", bg="#ef4444", fg="white", font=FONT_LABEL, cursor="hand2", relief="flat", command=self.export_pdf).pack(side="left", padx=5)
        
        # ─── Main Content Area ───
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top Row (Overall + Summary + Sensors)
        row1 = tk.Frame(content, bg=BG_PRIMARY)
        row1.pack(fill="x", expand=False, pady=(0, 10))
        
        self._build_overall_health(row1)
        self._build_reliability_summary(row1)
        self._build_sensor_health(row1)
        
        # Middle Row (Comms + FailSafe + AutoRec)
        row2 = tk.Frame(content, bg=BG_PRIMARY)
        row2.pack(fill="x", expand=False, pady=(0, 10))
        
        self._build_comm_panel(row2)
        self._build_failsafe_panel(row2)
        self._build_autorec_panel(row2)
        
        # Bottom Row (Timeline)
        row3 = tk.Frame(content, bg=BG_PRIMARY)
        row3.pack(fill="both", expand=True)
        
        self._build_timeline(row3)
        
    def _build_overall_health(self, parent):
        frame = tk.LabelFrame(parent, text=" Overall System Health ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.lbl_overall_status = tk.Label(frame, text="UNKNOWN", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=("Segoe UI", 24, "bold"))
        self.lbl_overall_status.pack(expand=True, pady=10)
        
    def _build_reliability_summary(self, parent):
        frame = tk.LabelFrame(parent, text=" Reliability Summary ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.lbl_rel_healthy = tk.Label(frame, text="Healthy: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_rel_healthy.pack(anchor="w", padx=10, pady=2)
        self.lbl_rel_warn = tk.Label(frame, text="Warning: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_rel_warn.pack(anchor="w", padx=10, pady=2)
        self.lbl_rel_failed = tk.Label(frame, text="Failed: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_rel_failed.pack(anchor="w", padx=10, pady=2)
        self.lbl_rel_score = tk.Label(frame, text="Score: 100%", bg=BG_SECONDARY, fg=CLR_NORMAL, font=FONT_MONO_MD)
        self.lbl_rel_score.pack(anchor="w", padx=10, pady=2)
        
    def _build_sensor_health(self, parent):
        frame = tk.LabelFrame(parent, text=" Sensor Health Panel ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        self.lbl_sens_online = tk.Label(frame, text="Online: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_sens_online.pack(anchor="w", padx=10, pady=2)
        self.lbl_sens_offline = tk.Label(frame, text="Offline: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_sens_offline.pack(anchor="w", padx=10, pady=2)
        self.lbl_sens_warn = tk.Label(frame, text="Warning/Invalid: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_sens_warn.pack(anchor="w", padx=10, pady=2)
        self.lbl_sens_score = tk.Label(frame, text="DQ Score: 100%", bg=BG_SECONDARY, fg=CLR_NORMAL, font=FONT_MONO_MD)
        self.lbl_sens_score.pack(anchor="w", padx=10, pady=2)

    def _build_comm_panel(self, parent):
        frame = tk.LabelFrame(parent, text=" Communication Health ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.lbl_comm_status = tk.Label(frame, text="Modules Online: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_comm_status.pack(anchor="w", padx=10, pady=2)
        self.lbl_comm_lat = tk.Label(frame, text="Avg Latency: 0ms", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_comm_lat.pack(anchor="w", padx=10, pady=2)
        self.lbl_comm_drop = tk.Label(frame, text="Dropped Messages: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_comm_drop.pack(anchor="w", padx=10, pady=2)
        
    def _build_failsafe_panel(self, parent):
        frame = tk.LabelFrame(parent, text=" Fail-Safe Status ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.lbl_fs_mode = tk.Label(frame, text="Mode: NORMAL", bg=BG_SECONDARY, fg=CLR_NORMAL, font=("Segoe UI", 12, "bold"))
        self.lbl_fs_mode.pack(anchor="w", padx=10, pady=(5, 2))
        self.lbl_fs_act = tk.Label(frame, text="Active Failures: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_fs_act.pack(anchor="w", padx=10, pady=2)
        self.lbl_fs_prot = tk.Label(frame, text="Protected Modules: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_fs_prot.pack(anchor="w", padx=10, pady=2)
        
    def _build_autorec_panel(self, parent):
        frame = tk.LabelFrame(parent, text=" Auto Recovery Status ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        self.lbl_ar_rec = tk.Label(frame, text="Recovered Services: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_ar_rec.pack(anchor="w", padx=10, pady=2)
        self.lbl_ar_att = tk.Label(frame, text="Recovery Attempts: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_ar_att.pack(anchor="w", padx=10, pady=2)
        self.lbl_ar_rate = tk.Label(frame, text="Success Rate: 100%", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_ar_rate.pack(anchor="w", padx=10, pady=2)
        self.lbl_ar_pend = tk.Label(frame, text="Pending Recoveries: 0", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD)
        self.lbl_ar_pend.pack(anchor="w", padx=10, pady=2)
        
    def _build_timeline(self, parent):
        frame = tk.LabelFrame(parent, text=" Reliability Event Timeline ", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
        frame.pack(fill="both", expand=True)
        
        cols = ("Time", "Source", "Level", "Message")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=8)
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Source", text="Engine")
        self.tree.heading("Level", text="Status")
        self.tree.heading("Message", text="Description")
        
        self.tree.column("Time", width=150, anchor="center")
        self.tree.column("Source", width=120, anchor="center")
        self.tree.column("Level", width=100, anchor="center")
        self.tree.column("Message", width=600, anchor="w")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
    def update_dashboard(self):
        # ─── Gather Data ───
        
        # Sensor Data
        sens_online = 0
        sens_offline = 0
        sens_warn = 0
        for s in self.val_engine._sensors.values():
            if s.health == HealthState.ONLINE: sens_online += 1
            elif s.health == HealthState.OFFLINE: sens_offline += 1
            elif s.health in (HealthState.WARNING, HealthState.FAILED): sens_warn += 1
        dq_score = self.val_engine.global_quality_score
        
        # Comm Data
        comm_online = sum(1 for m in self.comm_monitor.modules.values() if m.status == ModuleStatus.ONLINE)
        total_lat = sum(m.current_latency for m in self.comm_monitor.modules.values() if m.status == ModuleStatus.ONLINE)
        avg_lat = total_lat / max(1, comm_online)
        comm_drop = sum(getattr(m, 'error_count', getattr(m, 'retry_count', 0)) for m in self.comm_monitor.modules.values())
        
        # Auto Rec Data
        ar_report = self.auto_rec.get_diagnostic_report()
        ar_success = ar_report["Recovered Modules"]
        ar_fail = ar_report["Failed Recoveries"]
        ar_att = ar_success + ar_fail
        ar_rate = (ar_success / ar_att * 100) if ar_att > 0 else 100.0
        ar_pend = len(ar_report["Pending Issues"])
        
        # Fail Safe Data
        fs_mode = self.fail_safe.current_mode
        fs_act = len(self.fail_safe.active_failures)
        fs_prot = 8 # Estimated core protected modules
        
        # Summary & Overall
        total_healthy = sens_online + comm_online
        total_warn = sens_warn + len(ar_report["Pending Issues"])
        total_failed = sens_offline + ar_fail
        rel_score = max(0.0, 100.0 - (total_warn * 2 + total_failed * 10))
        
        if fs_mode == SafeMode.CRITICAL or total_failed > 2:
            overall_status = "CRITICAL"
            overall_clr = CLR_CRITICAL
        elif fs_mode == SafeMode.SAFE_MODE or fs_mode == SafeMode.WARNING or total_warn > 0 or total_failed > 0:
            overall_status = "WARNING"
            overall_clr = CLR_WARNING
        elif rel_score > 90:
            overall_status = "EXCELLENT"
            overall_clr = CLR_NORMAL
        else:
            overall_status = "GOOD"
            overall_clr = CLR_INFO
            
        # ─── Update UI Elements ───
        
        self.lbl_overall_status.config(text=overall_status, fg=overall_clr)
        
        self.lbl_rel_healthy.config(text=f"Healthy: {total_healthy}")
        self.lbl_rel_warn.config(text=f"Warning: {total_warn}")
        self.lbl_rel_failed.config(text=f"Failed: {total_failed}")
        self.lbl_rel_score.config(text=f"Score: {rel_score:.1f}%", fg=value_color_rel(rel_score))
        
        self.lbl_sens_online.config(text=f"Online: {sens_online}")
        self.lbl_sens_offline.config(text=f"Offline: {sens_offline}")
        self.lbl_sens_warn.config(text=f"Warning/Invalid: {sens_warn}")
        self.lbl_sens_score.config(text=f"DQ Score: {dq_score:.1f}%", fg=value_color_rel(dq_score))
        
        self.lbl_comm_status.config(text=f"Modules Online: {comm_online}")
        self.lbl_comm_lat.config(text=f"Avg Latency: {avg_lat:.1f}ms")
        self.lbl_comm_drop.config(text=f"Dropped Messages: {comm_drop}")
        
        self.lbl_fs_mode.config(text=f"Mode: {fs_mode.name}", fg=mode_color(fs_mode))
        self.lbl_fs_act.config(text=f"Active Failures: {fs_act}")
        self.lbl_fs_prot.config(text=f"Protected Modules: {fs_prot}")
        
        self.lbl_ar_rec.config(text=f"Recovered Services: {ar_success}")
        self.lbl_ar_att.config(text=f"Recovery Attempts: {ar_att}")
        self.lbl_ar_rate.config(text=f"Success Rate: {ar_rate:.1f}%")
        self.lbl_ar_pend.config(text=f"Pending Recoveries: {ar_pend}")
        
        self._sync_timeline()
        
    def _sync_timeline(self):
        # We can pull events from Auto Recovery and Fail-Safe
        current_events = []
        for r in self.auto_rec.recovery_history[-10:]:
            ts = datetime.fromtimestamp(r.timestamp).strftime("%H:%M:%S")
            status = "SUCCESS" if r.success else "FAILED"
            msg = f"{r.module_name}: {r.action_taken}"
            current_events.append((ts, "Auto Recovery", status, msg))
            
        for e in self.fail_safe.events[-10:]:
            ts = datetime.fromtimestamp(e.timestamp).strftime("%H:%M:%S")
            current_events.append((ts, "Fail-Safe", e.mode.name, e.description))
            
        current_events.sort(key=lambda x: x[0], reverse=True)
        
        if current_events != self._timeline_events:
            self._timeline_events = current_events
            for item in self.tree.get_children():
                self.tree.delete(item)
            for ev in current_events:
                self.tree.insert("", "end", values=ev)
                
    def _get_export_data(self):
        """Prepare snapshot data for export."""
        return [
            ["Metric", "Value"],
            ["Overall System Health", self.lbl_overall_status.cget("text")],
            ["Reliability Score", self.lbl_rel_score.cget("text")],
            ["Sensor Data Quality", self.lbl_sens_score.cget("text")],
            ["Modules Online", self.lbl_comm_status.cget("text")],
            ["Average Latency", self.lbl_comm_lat.cget("text")],
            ["Fail-Safe Mode", self.lbl_fs_mode.cget("text")],
            ["Recovery Success Rate", self.lbl_ar_rate.cget("text")],
            ["Pending Recoveries", self.lbl_ar_pend.cget("text")]
        ]

    def export_csv(self):
        path = os.path.join(self.export_dir, f"reliability_report_{int(datetime.now().timestamp())}.csv")
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(self._get_export_data())
            import tkinter.messagebox as mb
            mb.showinfo("Export Successful", f"CSV exported to:\n{path}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Export Failed", f"Failed to export CSV: {e}")

    def export_excel(self):
        # We simulate Excel export via a Tab-Separated Values file or simple HTML, 
        # but to keep it simple and dependency-free, we write a TSV named .xls which Excel opens easily.
        path = os.path.join(self.export_dir, f"reliability_report_{int(datetime.now().timestamp())}.xls")
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(self._get_export_data())
            import tkinter.messagebox as mb
            mb.showinfo("Export Successful", f"Excel exported to:\n{path}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Export Failed", f"Failed to export Excel: {e}")

    def export_pdf(self):
        # Simulate PDF with a formatted text report
        path = os.path.join(self.export_dir, f"reliability_report_{int(datetime.now().timestamp())}.pdf.txt")
        try:
            with open(path, 'w') as f:
                f.write("="*50 + "\n")
                f.write(" INDUSTRIAL RELIABILITY REPORT \n")
                f.write("="*50 + "\n")
                for row in self._get_export_data():
                    f.write(f"{row[0]:<25} | {row[1]}\n")
                f.write("="*50 + "\n")
            import tkinter.messagebox as mb
            mb.showinfo("Export Successful", f"PDF (Text format) exported to:\n{path}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Export Failed", f"Failed to export PDF: {e}")

def value_color_rel(score):
    if score >= 90: return CLR_NORMAL
    if score >= 70: return CLR_WARNING
    return CLR_CRITICAL

def mode_color(mode):
    if mode == SafeMode.NORMAL: return CLR_NORMAL
    if mode in (SafeMode.CRITICAL, SafeMode.EMERGENCY): return CLR_CRITICAL
    return CLR_WARNING
