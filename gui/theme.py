"""
gui/theme.py
============
Industrial dark SCADA theme definition.

Centralises all colour, font, and styling constants used across the GUI
so the entire look can be adjusted from one place.
"""

from __future__ import annotations
import json
import os
from pathlib import Path

# ─── Theme Loading ────────────────────────────────────────────────────────────
THEME_CONFIG_PATH = Path("data/config/theme_config.json")

def load_theme_preference() -> str:
    """Read the user's preferred theme mode ('dark' or 'light')."""
    if THEME_CONFIG_PATH.exists():
        try:
            with open(THEME_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("mode", "dark")
        except Exception:
            pass
    return "dark"

def set_theme_preference(mode: str):
    """Save the user's preferred theme mode ('dark' or 'light')."""
    THEME_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(THEME_CONFIG_PATH, 'w') as f:
        json.dump({"mode": mode}, f, indent=4)

CURRENT_MODE = load_theme_preference()

# ─── Colour Palette ──────────────────────────────────────────────────────────

if CURRENT_MODE == "light":
    # Backgrounds
    BG_PRIMARY   = "#f0f2f5"    # Deepest background (main window)
    BG_SECONDARY = "#ffffff"    # Panel / frame backgrounds
    BG_TERTIARY  = "#f8fafc"    # Card / widget backgrounds
    BG_HEADER    = "#e2e8f0"    # Title bars, headers
    BG_INPUT     = "#ffffff"    # Entry fields

    # Borders & grid
    BORDER       = "#cbd5e1"
    BORDER_LIGHT = "#94a3b8"
    GRID_LINE    = "#e2e8f0"

    # Text
    TEXT_PRIMARY   = "#1e293b"   # Very dark slate — headings, values
    TEXT_SECONDARY = "#64748b"   # Slate grey — labels, hints
    TEXT_MUTED     = "#94a3b8"   # Very dim — disabled items
    
    # Accent colours for process diagram
    CLR_PIPE_BG    = "#cbd5e1"  # Pipe outline
    
    # Status colours (equipment, gauges, indicators)
    CLR_NORMAL   = "#94a3b8"    # Gray — operating normally (ISA-101 neutral)
    CLR_RUNNING  = "#94a3b8"    # Gray
    CLR_STOPPED  = "#cbd5e1"    # Light Gray
    CLR_WARNING  = "#d97706"    # Amber/yellow
    CLR_CRITICAL = "#dc2626"    # Red
    CLR_OFFLINE  = "#cbd5e1"    # Light Gray
    CLR_INFO     = "#0284c7"    # Blue
    CLR_COMMS_LOSS = "#d946ef"  # Magenta
    CLR_MAINTENANCE = "#0ea5e9" # Light Blue

else:
    # Backgrounds
    BG_PRIMARY   = "#0d1117"    # Deepest background (main window)
    BG_SECONDARY = "#161b22"    # Panel / frame backgrounds
    BG_TERTIARY  = "#1c2128"    # Card / widget backgrounds
    BG_HEADER    = "#21262d"    # Title bars, headers
    BG_INPUT     = "#0d1117"    # Entry fields

    # Borders & grid
    BORDER       = "#30363d"
    BORDER_LIGHT = "#484f58"
    GRID_LINE    = "#21262d"

    # Text
    TEXT_PRIMARY   = "#e6edf3"   # Bright white — headings, values
    TEXT_SECONDARY = "#8b949e"   # Dim grey — labels, hints
    TEXT_MUTED     = "#484f58"   # Very dim — disabled items
    
    # Accent colours for process diagram
    CLR_PIPE_BG    = "#30363d"  # Pipe outline

    # Status colours (equipment, gauges, indicators)
    CLR_NORMAL   = "#8b949e"    # Gray — operating normally (ISA-101 neutral)
    CLR_RUNNING  = "#8b949e"    # Gray
    CLR_STOPPED  = "#484f58"    # Dark Gray
    CLR_WARNING  = "#ffc107"    # Amber/yellow — operator attention
    CLR_CRITICAL = "#ff1744"    # Red — immediate action required
    CLR_OFFLINE  = "#484f58"    # Dark Gray — offline / disabled
    CLR_INFO     = "#2196f3"    # Blue — informational
    CLR_COMMS_LOSS = "#d946ef"  # Magenta
    CLR_MAINTENANCE = "#0284c7" # Blue

# Accent colours for process diagram
CLR_HOT_FLUID   = "#ff6d00"  # Hot geothermal fluid (orange)
CLR_WARM_FLUID  = "#ff9800"  # Warm supply
CLR_COOL_FLUID  = "#29b6f6"  # Cool return

# Per-well trace colours (matches existing matplotlib dashboard)
WELL_COLORS = {
    "W-01": "#3b82f6",     # Blue
    "W-02": "#10b981",     # Green
    "W-03": "#f97316",     # Orange
    "GW-01": "#3b82f6",
    "GW-02": "#10b981",
    "GW-03": "#f97316",
}

# Gauge arc segment colours
GAUGE_LOW     = "#29b6f6"   # Below normal range
GAUGE_NORMAL  = "#00e676"   # Normal operating range
GAUGE_HIGH    = "#ffc107"   # High warning
GAUGE_DANGER  = "#ff1744"   # Danger / critical

# Alarm priority colours
ALARM_COLORS = {
    "CRITICAL": CLR_CRITICAL,
    "HIGH":     "#ff6d00",
    "MEDIUM":   CLR_WARNING,
    "LOW":      CLR_INFO,
}


# ─── Fonts ────────────────────────────────────────────────────────────────────

# Monospace for numeric readouts
FONT_MONO_XL    = ("Consolas", 22, "bold")    # Large gauge values
FONT_MONO_LG    = ("Consolas", 16, "bold")    # KPI card values
FONT_MONO_MD    = ("Consolas", 12)            # Table values, process labels
FONT_MONO_SM    = ("Consolas", 10)            # Small annotations

# Sans-serif for labels and titles
FONT_TITLE      = ("Segoe UI", 14, "bold")    # Section titles
FONT_SUBTITLE   = ("Segoe UI", 11, "bold")    # Sub-headers
FONT_LABEL      = ("Segoe UI", 10)            # Widget labels
FONT_LABEL_SM   = ("Segoe UI", 9)             # Small labels
FONT_HEADER_BAR = ("Segoe UI", 12, "bold")    # Top status bar


# ─── Sizes ────────────────────────────────────────────────────────────────────

GAUGE_SIZE      = 160    # px — diameter of circular gauges
KPI_CARD_W      = 160    # px — KPI card width
KPI_CARD_H      = 90     # px — KPI card height
PUMP_ICON_SIZE  = 50     # px — pump icon diameter
VALVE_ICON_SIZE = 36     # px — valve icon size
PIPE_WIDTH      = 8      # px — pipe line width
CHEVRON_SIZE    = 12     # px — animated flow chevron size
STATUS_LED_R    = 8      # px — status LED radius

# Refresh interval (milliseconds) — matches SCADA scan cycle
REFRESH_MS      = 2000


# ─── Utility functions ───────────────────────────────────────────────────────

def style_matplotlib_toolbar(toolbar):
    """
    Restyles a Matplotlib NavigationToolbar2Tk to match the dark theme.
    Inverts the default black icons to white so they are readable, and sets the background.
    """
    import os
    import matplotlib
    import tkinter as tk
    from PIL import Image, ImageTk, ImageOps
    
    toolbar.configure(background=BG_SECONDARY, borderwidth=0)
    
    if not hasattr(toolbar, '_styled_imgs'):
        toolbar._styled_imgs = []
    else:
        toolbar._styled_imgs.clear()
        
    image_dir = os.path.join(matplotlib.get_data_path(), 'images')
    valid_tools = [t for t in toolbar.toolitems if t[0] is not None]
    
    # Extract buttons
    buttons = [w for w in toolbar.winfo_children() if isinstance(w, tk.Button) or isinstance(w, tk.Checkbutton)]
    
    for btn, tool in zip(buttons, valid_tools):
        name = tool[2]
        btn.configure(background=BG_SECONDARY, activebackground=BG_TERTIARY, relief="flat", borderwidth=0)
        
        # Load the icon and invert it (make black white)
        img_path = os.path.join(image_dir, name + '.png')
        if not os.path.exists(img_path):
            img_path = os.path.join(image_dir, name + '_large.png')
            
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert('RGBA')
                r, g, b, a = img.split()
                rgb = Image.merge('RGB', (r, g, b))
                inv = ImageOps.invert(rgb)
                final = Image.merge('RGBA', (*inv.split(), a))
                
                photo = ImageTk.PhotoImage(final)
                toolbar._styled_imgs.append(photo)
                btn.configure(image=photo)
            except Exception:
                pass

    # Restyle any extra labels in the toolbar (like coordinate displays)
    for w in toolbar.winfo_children():
        if isinstance(w, tk.Label):
            w.configure(background=BG_SECONDARY, foreground=TEXT_PRIMARY, font=FONT_MONO_SM)

def status_color(health_value: str) -> str:
    """Return the appropriate colour for a SystemHealth value string."""
    mapping = {
        "GOOD":     CLR_NORMAL,
        "WARNING":  CLR_WARNING,
        "CRITICAL": CLR_CRITICAL,
    }
    return mapping.get(health_value, CLR_OFFLINE)


def value_color(value: float, lo_warn: float, hi_warn: float,
                lo_crit: float | None = None, hi_crit: float | None = None) -> str:
    """
    Return a colour based on where *value* falls relative to thresholds.

    Parameters
    ----------
    value    : The measured value.
    lo_warn  : Low warning threshold.
    hi_warn  : High warning threshold.
    lo_crit  : Low critical threshold (optional; defaults to lo_warn).
    hi_crit  : High critical threshold (optional; defaults to hi_warn).
    """
    lo_c = lo_crit if lo_crit is not None else lo_warn
    hi_c = hi_crit if hi_crit is not None else hi_warn

    if value <= lo_c or value >= hi_c:
        return CLR_CRITICAL
    if value <= lo_warn or value >= hi_warn:
        return CLR_WARNING
    return CLR_NORMAL


def alarm_priority_color(priority_name: str) -> str:
    """Return colour for an AlarmPriority name string."""
    return ALARM_COLORS.get(priority_name, CLR_INFO)


def lerp_color(frac: float, c_start: str, c_end: str) -> str:
    """
    Linearly interpolate between two hex colour strings.

    Parameters
    ----------
    frac    : 0.0 = c_start, 1.0 = c_end
    c_start : Hex colour string (e.g. "#00e676")
    c_end   : Hex colour string (e.g. "#ff1744")
    """
    frac = max(0.0, min(1.0, frac))
    r1, g1, b1 = int(c_start[1:3], 16), int(c_start[3:5], 16), int(c_start[5:7], 16)
    r2, g2, b2 = int(c_end[1:3], 16),   int(c_end[3:5], 16),   int(c_end[5:7], 16)
    r = int(r1 + (r2 - r1) * frac)
    g = int(g1 + (g2 - g1) * frac)
    b = int(b1 + (b2 - b1) * frac)
    return f"#{r:02x}{g:02x}{b:02x}"
