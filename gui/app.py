"""
gui/app.py
==========
Legacy wrapper to launch the new HMI Main Window.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hmi.main_window import SCADAGuiApp

if __name__ == "__main__":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    
    import logging
    from core.config.system_config import SystemConfig
    from core.logging.logger_setup import setup_logging
    
    # 1. Startup Validation
    Path("config").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # 2. Enterprise Logging
    setup_logging()
    logger = logging.getLogger("DikiliGeothermal.GUI")
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    # Application Metadata
    from core.diagnostics.application_metadata import ApplicationMetadata
    metadata = ApplicationMetadata()
    metadata.display()

    # System Startup Diagnostics
    from core.diagnostics.startup_diagnostics import StartupDiagnostics
    diagnostics = StartupDiagnostics()
    try:
        diagnostics.run_checks()
    except RuntimeError as e:
        logger.critical(f"Startup aborted: {e}")
        import sys
        sys.exit(1)
    
    config = SystemConfig.load()
    well_ids = [w.well_id for w in config.wells]
    
    app = SCADAGuiApp(well_ids=well_ids)
    app.run()
