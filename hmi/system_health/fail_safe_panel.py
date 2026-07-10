import tkinter as tk
from tkinter import ttk
from datetime import datetime

from gui.theme import BG_PRIMARY, BG_SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY, BORDER
from gui.theme import FONT_TITLE, FONT_LABEL, FONT_MONO_MD
from core.safety.fail_safe import SafeMode, FailSafeManager

class FailSafePanel(tk.Frame):
    def __init__(self, parent, fail_safe_manager: FailSafeManager, *args, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, *args, **kwargs)
        self.manager = fail_safe_manager
        
        # Color mapping for modes
        self.mode_colors = {
            SafeMode.NORMAL: "#10b981",    # Emerald
            SafeMode.WARNING: "#f59e0b",   # Amber
            SafeMode.SAFE_MODE: "#3b82f6", # Blue
            SafeMode.CRITICAL: "#ef4444",  # Red
            SafeMode.EMERGENCY: "#7f1d1d"  # Dark Red
        }

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_SECONDARY, pady=10, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x", padx=10, pady=10)
        
        tk.Label(header, text="FAIL-SAFE & SAFE OPERATION MANAGER", 
                 bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(side="left", padx=10)

        # Mode display
        self.mode_var = tk.StringVar(value="UNKNOWN")
        self.mode_lbl = tk.Label(header, textvariable=self.mode_var,
                                 bg=BG_SECONDARY, fg="#fff", font=("Segoe UI", 14, "bold"),
                                 padx=15, pady=5, relief="flat")
        self.mode_lbl.pack(side="right", padx=15)
        
        # Main content area
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=10, pady=0)
        
        # Active Failures
        active_frame = tk.LabelFrame(content, text=" Active Failures & Overrides ",
                                     bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=5)
        active_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.active_tree = ttk.Treeview(active_frame, columns=("Component", "Description"), show="headings", height=8)
        self.active_tree.heading("Component", text="Component ID")
        self.active_tree.heading("Description", text="Failure Description")
        self.active_tree.column("Component", width=120, anchor="center")
        self.active_tree.column("Description", width=400, anchor="w")
        self.active_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Recovered / Recent Events
        history_frame = tk.LabelFrame(content, text=" Recovery History ",
                                      bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=5)
        history_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.history_tree = ttk.Treeview(history_frame, columns=("Time", "Mode", "Event"), show="headings", height=8)
        self.history_tree.heading("Time", text="Time")
        self.history_tree.heading("Mode", text="Mode")
        self.history_tree.heading("Event", text="Description")
        self.history_tree.column("Time", width=140, anchor="center")
        self.history_tree.column("Mode", width=100, anchor="center")
        self.history_tree.column("Event", width=300, anchor="w")
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status footer
        self.footer_var = tk.StringVar(value="System functioning normally.")
        footer = tk.Label(self, textvariable=self.footer_var,
                          bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_MONO_MD, anchor="w")
        footer.pack(fill="x", padx=15, pady=10)

    def _update_loop(self):
        self.update_data()
        self.after(1000, self._update_loop)

    def update_data(self):
        # Update current mode
        current_mode = self.manager.current_mode
        self.mode_var.set(f" MODE: {current_mode.name} ")
        self.mode_lbl.config(bg=self.mode_colors.get(current_mode, "#7f1d1d"))
        
        # Update active failures
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)
            
        if self.manager.active_failures:
            for comp, desc in self.manager.active_failures.items():
                self.active_tree.insert("", "end", values=(comp, desc))
        else:
            self.active_tree.insert("", "end", values=("--", "No active failures detected."))
            
        # Update history
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        for event in reversed(self.manager.events[-20:]): # Show last 20 events
            dt_str = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
            self.history_tree.insert("", "end", values=(dt_str, event.mode.name, event.description))
            
        # Footer
        if self.manager._pending_recovery:
            elapsed = time.time() - self.manager._recovery_start_time
            rem = max(0.0, getattr(self.manager.config, 'recovery_validation_time_sec', 15.0) - elapsed)
            self.footer_var.set(f"Validating system integrity for recovery... {rem:.1f}s remaining")
        elif not self.manager.is_ai_allowed():
            self.footer_var.set("⚠ AI Engine & Optimizations suspended due to unsafe mode.")
        else:
            self.footer_var.set("All systems operational. AI prediction engine active.")
