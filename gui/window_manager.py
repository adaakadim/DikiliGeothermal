"""
gui/window_manager.py
=====================
Tracks pop-up windows to prevent duplicates and restores previous positioning.
"""

import tkinter as tk
from typing import Dict

class WindowManager:
    _windows: Dict[str, tk.Toplevel] = {}

    @classmethod
    def register(cls, window_id: str, window: tk.Toplevel):
        """Registers a window. If already exists, closes old one (or we should focus)."""
        if window_id in cls._windows:
            try:
                cls._windows[window_id].destroy()
            except tk.TclError:
                pass
        cls._windows[window_id] = window
        window.protocol("WM_DELETE_WINDOW", lambda: cls._on_close(window_id, window))

    @classmethod
    def _on_close(cls, window_id: str, window: tk.Toplevel):
        if window_id in cls._windows:
            del cls._windows[window_id]
        window.destroy()

    @classmethod
    def focus_if_exists(cls, window_id: str) -> bool:
        """Returns True and focuses window if it exists, False otherwise."""
        if window_id in cls._windows:
            try:
                win = cls._windows[window_id]
                if win.winfo_exists():
                    if win.state() == "iconic":
                        win.deiconify()
                    win.lift()
                    win.focus_force()
                    return True
                else:
                    del cls._windows[window_id]
            except tk.TclError:
                del cls._windows[window_id]
        return False
