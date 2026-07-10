"""
gui/ai_panel.py
===============
Provides the graphical components for AI prediction integration.
- AIAnalyticsPanel: Displays real-time ML metrics.
- AIEventLogPanel: Dedicated log for AI-driven events.
"""

from __future__ import annotations
import datetime
import tkinter as tk
import tkinter.ttk as ttk

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE, FONT_MONO_MD
)

class AIAnalyticsPanel(tk.Frame):
    """
    Displays real-time Random Forest predictions:
    Pump Failure Risk, Health Score, Confidence, and Plant Status.
    """
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        hdr = tk.Label(self, text="  AI PREDICTIVE ANALYTICS",
                       bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL, anchor="w")
        hdr.pack(fill="x", pady=(0, 2))

        self.container = tk.Frame(self, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.container.pack(fill="both", expand=True, pady=2)
        
        # We will use a 2-column grid for Key-Value pairs
        self.container.columnconfigure(0, weight=1, minsize=140)
        self.container.columnconfigure(1, weight=1, minsize=100)

        self._labels = {}
        
        rows = [
            ("pump_risk", "Pump Failure Risk:", "%"),
            ("health", "Equipment Health:", "%"),
            ("maint", "Maintenance:", ""),
            ("status", "Plant Status:", ""),
            ("confidence", "AI Confidence:", "%"),
            ("updated", "Last Update:", "")
        ]

        for i, (key, text, unit) in enumerate(rows):
            lbl_name = tk.Label(self.container, text=text, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w")
            lbl_name.grid(row=i, column=0, sticky="w", padx=(10, 5), pady=4)
            
            lbl_val = tk.Label(self.container, text=f"--- {unit}", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, anchor="e")
            lbl_val.grid(row=i, column=1, sticky="e", padx=(5, 10), pady=4)
            
            self._labels[key] = lbl_val

    def update_metrics(self, risk_pct: float, health_pct: float, maint: bool, status: str, confidence: float, timestamp: str):
        """Updates the labels and applies color thresholds."""
        
        # 1. Pump Risk
        risk_color = CLR_NORMAL
        if risk_pct >= 70: risk_color = CLR_CRITICAL
        elif risk_pct >= 40: risk_color = CLR_WARNING
        self._labels["pump_risk"].config(text=f"{risk_pct:.1f} %", fg=risk_color)

        # 2. Health
        health_color = CLR_NORMAL
        if health_pct <= 50: health_color = CLR_CRITICAL
        elif health_pct <= 80: health_color = CLR_WARNING
        self._labels["health"].config(text=f"{health_pct:.1f} %", fg=health_color)

        # 3. Maintenance
        maint_str = "ACTION REQUIRED" if maint else "NO ACTION"
        maint_color = CLR_CRITICAL if maint else CLR_NORMAL
        self._labels["maint"].config(text=maint_str, fg=maint_color)

        # 4. Status
        status_color = CLR_NORMAL
        if status == "CRITICAL": status_color = CLR_CRITICAL
        elif status == "WARNING": status_color = CLR_WARNING
        self._labels["status"].config(text=status, fg=status_color)

        # 5. Confidence
        self._labels["confidence"].config(text=f"{confidence:.1f} %", fg=TEXT_PRIMARY)

        # 6. Timestamp
        # Format the long timestamp neatly
        try:
            dt = datetime.datetime.fromisoformat(timestamp)
            ts_str = dt.strftime("%H:%M:%S")
        except:
            ts_str = timestamp
        self._labels["updated"].config(text=ts_str, fg=TEXT_MUTED)


class AIEventLogPanel(tk.Frame):
    """
    Dedicated scrolling log for AI prediction shifts and events.
    """
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        hdr = tk.Label(self, text="  AI EVENT LOG",
                       bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL, anchor="w")
        hdr.pack(fill="x", pady=(0, 2))

        container = tk.Frame(self, bg=BG_SECONDARY)
        container.pack(fill="both", expand=True)

        self._text = tk.Text(
            container,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM,
            wrap="word", borderwidth=0, highlightthickness=0,
            state="disabled", height=6,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)

        self._text.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side="right", fill="y")

        self._text.tag_configure("INFO", foreground=TEXT_SECONDARY)
        self._text.tag_configure("WARN", foreground=CLR_WARNING)
        self._text.tag_configure("CRIT", foreground=CLR_CRITICAL)
        self._text.tag_configure("TIME", foreground=TEXT_MUTED)
        
        self.log_event("AI Engine Initialized.", level="INFO")

    def log_event(self, message: str, level: str = "INFO"):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._text.configure(state="normal")
        
        if int(self._text.index("end-1c").split(".")[0]) > 100:
            self._text.delete("1.0", "2.0")

        self._text.insert("end", f"[{now}] ", "TIME")
        self._text.insert("end", f"{message}\n", level)
        
        self._text.configure(state="disabled")
        self._text.see("end")
