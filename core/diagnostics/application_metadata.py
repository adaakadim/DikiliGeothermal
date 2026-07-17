"""
core/diagnostics/application_metadata.py
========================================
Centralized module for application identity and metadata.
"""

import logging
import platform
from datetime import datetime
from core.configuration import config as cm

logger = logging.getLogger(__name__)

class ApplicationMetadata:
    """
    Centralized metadata for the application identity.
    """
    
    def __init__(self):
        self.app_name = cm.get('app.name', 'DikiliGeothermal')
        self.version = cm.get('app.version', 'v1.0.0 Release Candidate')
        self.build_number = "1002"  # Or loaded from an internal build file
        self.release_date = "2026-07-08"
        self.python_version = platform.python_version()
        self.operating_system = f"{platform.system()} {platform.release()}"
        self.active_environment = cm.environment.upper()
        self.config_profile = getattr(cm, '_active_profile', 'Default')
        self.startup_time = datetime.now()

    def display(self):
        """
        Logs the application metadata clearly and cleanly to the logger.
        """
        logger.info("=" * 60)
        logger.info(f"  Application    : {self.app_name}")
        logger.info(f"  Version        : {self.version} (Build {self.build_number})")
        logger.info(f"  Release Date   : {self.release_date}")
        logger.info(f"  Python Version : {self.python_version}")
        logger.info(f"  OS             : {self.operating_system}")
        logger.info(f"  Environment    : {self.active_environment}")
        logger.info(f"  Config Profile : {self.config_profile}")
        logger.info(f"  Startup Time   : {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
