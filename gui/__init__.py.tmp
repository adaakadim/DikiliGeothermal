"""
gui/__init__.py
===============
Graphical SCADA interface package for the Dikili Geothermal plant.

This package provides a professional, industrial-grade graphical dashboard
built on tkinter + matplotlib, designed to run alongside (not replace)
the existing terminal dashboard.
"""


def get_app():
    """Lazy import to avoid circular reference when running as __main__."""
    from gui.app import SCADAGuiApp
    return SCADAGuiApp


__all__ = ["get_app"]

