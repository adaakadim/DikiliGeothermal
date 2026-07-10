"""
gui/panels.py
=============
Side panels for the graphical SCADA interface:
  - EventLogPanel
  - EquipmentTreePanel
"""

from __future__ import annotations

import datetime
import tkinter as tk
import tkinter.ttk as ttk

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE,
)


# ═════════════════════════════════════════════════════════════════════════════
#  EVENT LOG PANEL
# ═════════════════════════════════════════════════════════════════════════════

class EventLogPanel(tk.Frame):
    """
    Live scrolling text area for system events.
    Colors text based on severity (INFO, WARN, CRIT).
    """

    def __init__(self, parent: tk.Widget, height: int = 150, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # Header
        hdr = tk.Label(self, text="  LIVE EVENT LOG",
                       bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL,
                       anchor="w")
        hdr.pack(fill="x", pady=(0, 2))

        # Text area with scrollbar
        container = tk.Frame(self, bg=BG_SECONDARY)
        container.pack(fill="both", expand=True)

        self._text = tk.Text(
            container,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM,
            wrap="word", borderwidth=0, highlightthickness=0,
            state="disabled", height=8,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)

        self._text.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side="right", fill="y")

        # Tags for colored text
        self._text.tag_configure("INFO", foreground=TEXT_SECONDARY)
        self._text.tag_configure("WARN", foreground=CLR_WARNING)
        self._text.tag_configure("CRIT", foreground=CLR_CRITICAL)
        self._text.tag_configure("TIME", foreground=TEXT_MUTED)
        
        self.log_event("System initialized.", level="INFO")

    def log_event(self, message: str, level: str = "INFO"):
        """
        Append a timestamped event to the log.
        level: "INFO", "WARN", or "CRIT"
        """
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._text.configure(state="normal")
        
        # Keep log size bounded (approx 200 lines)
        if int(self._text.index("end-1c").split(".")[0]) > 200:
            self._text.delete("1.0", "2.0")

        self._text.insert("end", f"[{now}] ", "TIME")
        self._text.insert("end", f"{message}\n", level)
        
        self._text.configure(state="disabled")
        self._text.see("end")


# ═════════════════════════════════════════════════════════════════════════════
#  EQUIPMENT TREE PANEL
# ═════════════════════════════════════════════════════════════════════════════

class EquipmentTreePanel(tk.Frame):
    """
    Hierarchical view of all plant equipment.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # Header
        hdr = tk.Label(self, text="  EQUIPMENT HIERARCHY",
                       bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL,
                       anchor="w")
        hdr.pack(fill="x", pady=(0, 2))

        # Setup custom styles for treeview
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("EqTree.Treeview",
                        background=BG_SECONDARY,
                        foreground=TEXT_PRIMARY,
                        fieldbackground=BG_SECONDARY,
                        borderwidth=0,
                        font=FONT_LABEL_SM,
                        rowheight=24)
        style.map("EqTree.Treeview",
                  background=[("selected", BG_HEADER)],
                  foreground=[("selected", TEXT_PRIMARY)])

        # Treeview
        self._tree = ttk.Treeview(self, style="EqTree.Treeview", show="tree")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill="both", expand=True, padx=(1, 0))
        scrollbar.pack(side="right", fill="y")

        self._populate()

    def _populate(self):
        """Build the static equipment hierarchy."""
        plant = self._tree.insert("", "end", text="Dikili Geothermal Plant", open=True)
        
        wells = self._tree.insert(plant, "end", text="Production Wells", open=True)
        self._tree.insert(wells, "end", text="GW-01")
        self._tree.insert(wells, "end", text="GW-02")
        self._tree.insert(wells, "end", text="GW-03")
        
        prim_pumps = self._tree.insert(plant, "end", text="Primary Pump Station", open=True)
        self._tree.insert(prim_pumps, "end", text="Pump-1")
        self._tree.insert(prim_pumps, "end", text="Pump-2")
        self._tree.insert(prim_pumps, "end", text="Pump-3")
        
        hx = self._tree.insert(plant, "end", text="Heat Exchanger", open=True)
        self._tree.insert(hx, "end", text="HX Primary Side")
        self._tree.insert(hx, "end", text="HX Secondary Side")
        
        dist_pumps = self._tree.insert(plant, "end", text="Distribution Pump Station", open=True)
        self._tree.insert(dist_pumps, "end", text="Dist-Pump-1")
        self._tree.insert(dist_pumps, "end", text="Dist-Pump-2")
        
        dh = self._tree.insert(plant, "end", text="District Heating Network", open=True)
        self._tree.insert(dh, "end", text="Supply Manifold")
        self._tree.insert(dh, "end", text="Return Manifold")
