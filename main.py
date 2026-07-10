"""
DikiliGeothermal SCADA System
==============================
Industrial geothermal district heating monitoring & control system
Location: Dikili, Izmir, Turkey

Entry Point: main.py
"""

import sys
import time
import signal
import logging
from pathlib import Path

# Ensure project root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from scada.system import SCADASystem
from core.config.system_config import SystemConfig
from analytics.reporter import ReportGenerator
from control.scheduler import ControlScheduler

# ─── Graceful Shutdown ────────────────────────────────────────────────────────
def signal_handler(sig, frame):
    logging.getLogger("main").info("Shutdown signal received. Stopping SCADA system...")
    scada.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from core.logging.logger_setup import setup_logging

    # 1. Startup Validation
    # Ensure config and logs directories exist
    Path("config").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # 2. Initialize Enterprise Logging
    setup_logging()
    logger = logging.getLogger("DikiliGeothermal")
    
    # 3. Application Metadata
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

    # Load system configuration backward-compatibility wrapper
    config = SystemConfig.load()

    # Initialise SCADA system
    scada = SCADASystem(config)
    scheduler = ControlScheduler(scada)
    reporter = ReportGenerator(scada)

    # Start subsystems
    scada.start()
    scheduler.start()

    logger.info("SCADA system online. Press Ctrl+C to stop.")

    try:
        while scada.is_running():
            scada.tick()
            reporter.update()
            time.sleep(config.scan_interval)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt — shutting down.")
        scada.stop()
