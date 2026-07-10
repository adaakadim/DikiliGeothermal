"""
gui/alarm_panel.py
==================
Alarm table panel for the graphical SCADA interface.

Displays active alarms in a Treeview table with columns for
alarm name, priority (colour-coded), elapsed time, and status.
Refreshes every scan cycle from an AlarmManager instance.
"""

from __future__ import annotations

import time
import tkinter as tk
import tkinter.ttk as ttk
from typing import Optional

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_MONO_SM, FONT_LABEL, FONT_LABEL_SM, FONT_SUBTITLE,
    ALARM_COLORS, alarm_priority_color,
)


class AlarmPanel(tk.Frame):
    """
    Scrollable alarm table showing active alarms from an AlarmManager.

    Parameters
    ----------
    parent : Parent widget.
    height : Visible height of the table in pixels.
    """

    def __init__(self, parent: tk.Widget, height: int = 160, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)

        # ── Header ─────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_HEADER, height=28)
        header.pack(fill="x")
        header.pack_propagate(False)

        self._header_label = tk.Label(
            header,
            text="  ALARM PANEL  |  NO ACTIVE ALARMS",
            bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL,
            anchor="w",
        )
        self._header_label.pack(fill="x", padx=4, pady=2)

        # ── Status LED in header ───────────────────────────────────────────
        self._led = tk.Canvas(header, width=16, height=16,
                              bg=BG_HEADER, highlightthickness=0)
        self._led.place(relx=1.0, x=-24, rely=0.5, anchor="center")
        self._led_oval = self._led.create_oval(2, 2, 14, 14,
                                                fill=CLR_NORMAL, outline="")

        # ── Configure ttk styles for dark theme ───────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Alarm.Treeview",
                         background=BG_SECONDARY,
                         foreground=TEXT_PRIMARY,
                         fieldbackground=BG_SECONDARY,
                         borderwidth=0,
                         font=FONT_MONO_SM,
                         rowheight=22)

        style.configure("Alarm.Treeview.Heading",
                         background=BG_HEADER,
                         foreground=TEXT_SECONDARY,
                         font=FONT_LABEL_SM,
                         borderwidth=1,
                         relief="flat")

        style.map("Alarm.Treeview",
                  background=[("selected", "#21262d")],
                  foreground=[("selected", TEXT_PRIMARY)])

        style.map("Alarm.Treeview.Heading",
                  background=[("active", BG_HEADER)])

        # ── Treeview ──────────────────────────────────────────────────────
        columns = ("priority", "category", "tag", "description", "age", "status")
        self._tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            style="Alarm.Treeview",
            height=6,
        )

        self._tree.heading("priority",    text="PRI")
        self._tree.heading("category",    text="TYPE")
        self._tree.heading("tag",         text="TAG")
        self._tree.heading("description", text="DESCRIPTION")
        self._tree.heading("age",         text="AGE")
        self._tree.heading("status",      text="STATUS")

        self._tree.column("priority",    width=60,  anchor="center")
        self._tree.column("category",    width=100, anchor="center")
        self._tree.column("tag",         width=80,  anchor="center")
        self._tree.column("description", width=250, anchor="w")
        self._tree.column("age",         width=60,  anchor="center")
        self._tree.column("status",      width=90,  anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill="both", expand=True, padx=(1, 0))
        scrollbar.pack(side="right", fill="y")

        # Tag colours for priority levels
        for pri_name, pri_color in ALARM_COLORS.items():
            self._tree.tag_configure(pri_name, foreground=pri_color)

        # "No alarms" tag
        self._tree.tag_configure("NONE", foreground=TEXT_MUTED)

    def update_alarms(self, alarm_manager) -> None:
        """
        Refresh the alarm table from an AlarmManager instance.

        Parameters
        ----------
        alarm_manager : An ``AlarmManager`` instance with ``active_alarms`` property.
        """
        # Clear existing rows
        for item in self._tree.get_children():
            self._tree.delete(item)

        alarms = alarm_manager.active_alarms

        if not alarms:
            self._header_label.config(
                text="  ALARM PANEL  |  NO ACTIVE ALARMS  —  ALL SYSTEMS NOMINAL",
                fg=CLR_NORMAL,
            )
            self._led.itemconfig(self._led_oval, fill=CLR_NORMAL)

            self._tree.insert("", "end", values=(
                "", "", "", "No active alarms — all systems operating normally", "", ""
            ), tags=("NONE",))
            return

        # Update header
        n_alarms = len(alarms)
        has_critical = any(a.priority.name == "CRITICAL" for a in alarms)

        if has_critical:
            self._header_label.config(
                text=f"  ALARM PANEL  |  *** {n_alarms} ACTIVE ALARM{'S' if n_alarms != 1 else ''} ***  CRITICAL",
                fg=CLR_CRITICAL,
            )
            self._led.itemconfig(self._led_oval, fill=CLR_CRITICAL)
        else:
            self._header_label.config(
                text=f"  ALARM PANEL  |  {n_alarms} ACTIVE ALARM{'S' if n_alarms != 1 else ''}",
                fg=CLR_WARNING,
            )
            self._led.itemconfig(self._led_oval, fill=CLR_WARNING)

        # Populate rows
        for alarm in alarms[:20]:  # Cap at 20 rows for performance
            age_s = int(alarm.age_seconds)
            age_str = f"{age_s // 60:02d}:{age_s % 60:02d}"

            cat_str = "PREDICTIVE" if alarm.category.name == "PREDICTIVE_AI" else alarm.category.name

            self._tree.insert("", "end", values=(
                alarm.priority.name,
                cat_str,
                alarm.tag_id,
                alarm.description[:60],
                age_str,
                alarm.state.value,
            ), tags=(alarm.priority.name,))
