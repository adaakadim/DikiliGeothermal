import tkinter as tk
from tkinter import ttk
from datetime import datetime
import math

from gui.theme import BG_PRIMARY, BG_SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY, BORDER
from gui.theme import FONT_TITLE, FONT_LABEL, FONT_MONO_MD
from core.diagnostics.communication_monitor import CommunicationMonitor, ModuleStatus

class CommunicationPanel(tk.Frame):
    def __init__(self, parent, comm_monitor: CommunicationMonitor, *args, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, *args, **kwargs)
        self.monitor = comm_monitor
        
        self.status_colors = {
            ModuleStatus.ONLINE: "#10b981",    # Emerald
            ModuleStatus.OFFLINE: "#64748b",   # Slate
            ModuleStatus.STARTING: "#3b82f6",  # Blue
            ModuleStatus.STOPPING: "#f59e0b",  # Amber
            ModuleStatus.WARNING: "#f59e0b",   # Amber
            ModuleStatus.FAILED: "#ef4444",    # Red
            ModuleStatus.UNKNOWN: "#64748b"    # Slate
        }
        
        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        # 1. Header (Health Score)
        header_frame = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(header_frame, text="COMMUNICATION & NETWORK DIAGNOSTICS", 
                 bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(side="left", padx=15, pady=15)
                 
        self.health_var = tk.StringVar(value="Health: 100%")
        self.health_lbl = tk.Label(header_frame, textvariable=self.health_var,
                                   bg=BG_SECONDARY, fg="#10b981", font=("Segoe UI", 16, "bold"))
        self.health_lbl.pack(side="right", padx=20)

        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=10, pady=0)
        
        # 2. Module Status Grid (Left)
        status_frame = tk.LabelFrame(content, text=" Module Status & Latency ",
                                     bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=5)
        status_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        columns = ("Module", "Status", "Latency (ms)", "Heartbeat", "Score")
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.status_tree.heading(col, text=col)
            
        self.status_tree.column("Module", width=180, anchor="w")
        self.status_tree.column("Status", width=100, anchor="center")
        self.status_tree.column("Latency (ms)", width=120, anchor="center")
        self.status_tree.column("Heartbeat", width=100, anchor="center")
        self.status_tree.column("Score", width=100, anchor="center")
        
        self.status_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 3. Communication Event History (Right)
        history_frame = tk.LabelFrame(content, text=" Network Event History ",
                                      bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=5)
        history_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        hist_cols = ("Time", "Module", "Event", "Message")
        self.history_tree = ttk.Treeview(history_frame, columns=hist_cols, show="headings", height=10)
        
        for col in hist_cols:
            self.history_tree.heading(col, text=col)
            
        self.history_tree.column("Time", width=100, anchor="center")
        self.history_tree.column("Module", width=140, anchor="w")
        self.history_tree.column("Event", width=120, anchor="center")
        self.history_tree.column("Message", width=250, anchor="w")
        
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 4. Latency Graph (Bottom)
        graph_frame = tk.LabelFrame(self, text=" Internal Network Latency (Simulated ms) ",
                                    bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=5)
        graph_frame.pack(fill="x", padx=10, pady=10)
        
        self.canvas = tk.Canvas(graph_frame, bg=BG_SECONDARY, height=120, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)
        self.latency_history = []

    def _update_loop(self):
        self.update_data()
        self.after(2000, self._update_loop)

    def update_data(self):
        # Overall Health Score
        score = self.monitor.get_overall_health_score()
        self.health_var.set(f"Health: {score:.1f}%")
        
        if score >= 90:
            self.health_lbl.config(fg="#10b981") # Excellent
        elif score >= 75:
            self.health_lbl.config(fg="#3b82f6") # Good
        elif score >= 50:
            self.health_lbl.config(fg="#f59e0b") # Fair
        else:
            self.health_lbl.config(fg="#ef4444") # Critical/Poor
            
        # Update Status Grid
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
            
        for name, mod in self.monitor.modules.items():
            lat_str = f"{mod.current_latency:.1f}" if mod.status == ModuleStatus.ONLINE else "---"
            interval_str = f"{mod.heartbeat_interval:.1f}s"
            score_str = f"{mod.calculate_health_score():.0f}%"
            self.status_tree.insert("", "end", values=(
                name, mod.status.name, lat_str, interval_str, score_str
            ))
            
        # Update Event History
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        for event in reversed(self.monitor.events[-15:]):
            dt_str = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
            self.history_tree.insert("", "end", values=(
                dt_str, event.module_name, event.event_type, event.message
            ))
            
        self._draw_graph()

    def _draw_graph(self):
        self.canvas.delete("all")
        
        # Calculate average latency of all ONLINE modules
        online_mods = [m for m in self.monitor.modules.values() if m.status == ModuleStatus.ONLINE]
        if online_mods:
            avg_lat = sum(m.current_latency for m in online_mods) / len(online_mods)
        else:
            avg_lat = 0.0
            
        self.latency_history.append(avg_lat)
        if len(self.latency_history) > 60:
            self.latency_history.pop(0)
            
        if not self.latency_history:
            return
            
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 800
        
        max_val = max(100.0, max(self.latency_history) * 1.2) # min 100ms scale
        
        dx = w / max(1, len(self.latency_history) - 1)
        
        pts = []
        for i, val in enumerate(self.latency_history):
            x = i * dx
            y = h - (val / max_val * h)
            pts.extend([x, y])
            
        if len(pts) >= 4:
            self.canvas.create_line(pts, fill="#3b82f6", width=2, smooth=True)
            
        # Draw current latency text
        self.canvas.create_text(w - 20, 20, text=f"{self.latency_history[-1]:.1f} ms",
                                fill="#e2e8f0", font=FONT_MONO_MD, anchor="e")
