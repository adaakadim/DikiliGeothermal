"""
core/logging/logger_setup.py
============================
Centralized logging framework for Dikili Geothermal SCADA.
Configures rotating file handlers and standard console output.
"""

import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_level: str = None):
    """
    Configure enterprise-grade system-wide logging.
    Routes logs to specialized files based on module namespace.
    """
    from core.configuration import config
    
    if log_level is None:
        log_level = config.get("logging.level", "INFO")
        
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Define format
    enable_tracing = config.get("logging.tracing.enable_correlation", True)
    enrich_logs = config.get("logging.tracing.enrich_logs", True)
    buffer_size = config.get("logging.tracing.in_memory_buffer_size", 1000)
    
    base_fmt = config.get("logging.format", "%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    if enable_tracing and enrich_logs and "%(correlation_id)s" not in base_fmt:
        base_fmt = base_fmt.replace("%(name)s -", "%(name)s [%(correlation_id)s] -")
        
    date_fmt = config.get("logging.date_format", "%Y-%m-%d %H:%M:%S")
    formatter = logging.Formatter(fmt=base_fmt, datefmt=date_fmt)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Prevent multiple initializations that cause duplicate logs and file locks
    if getattr(root_logger, "_is_setup", False):
        return
    root_logger._is_setup = True
    
    # Clear existing handlers to avoid duplicates during reloads
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
            root_logger.removeHandler(handler)
            
    # Add correlation factory globally if tracing is enabled
    from core.logging.correlation import get_correlation_id, CorrelationRingBufferHandler
    if enable_tracing:
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            cid = get_correlation_id()
            record.correlation_id = cid if cid else "NO-CORRELATION"
            return record
        logging.setLogRecordFactory(record_factory)
        
        # Memory ring buffer for diagnostics
        ring_buffer = CorrelationRingBufferHandler(capacity=buffer_size)
        ring_buffer.setLevel(level)
        ring_buffer.setFormatter(formatter)
        root_logger.addHandler(ring_buffer)
        
        # Expose the ring buffer globally for diagnostics access
        import core.logging.correlation as corr_module
        corr_module.global_ring_buffer = ring_buffer
        
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    max_bytes = config.get("logging.rotation.max_bytes", 10485760)
    backup_count = config.get("logging.rotation.backup_count", 5)
    
    def add_file_handler(filename: str, log_level: int, filter_func=None):
        handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        if filter_func:
            handler.addFilter(filter_func)
        root_logger.addHandler(handler)

    # Error Log (WARNING and above, global)
    add_file_handler("error.log", logging.WARNING)
    
    # Module-specific logs
    add_file_handler("security_audit.log", level, lambda r: r.name.startswith("security.audit"))
    add_file_handler("ai.log", level, lambda r: r.name.startswith("analytics.ai"))
    add_file_handler("scada.log", level, lambda r: r.name.startswith(("scada", "hardware", "control")))
    add_file_handler("digital_twin.log", level, lambda r: r.name.startswith("digital_twin"))
    add_file_handler("simulation.log", level, lambda r: r.name.startswith("simulation"))
    add_file_handler("system.log", level, lambda r: not r.name.startswith(("analytics.ai", "scada", "hardware", "control", "digital_twin", "simulation", "security.audit")))
    
    # Silence overly verbose third-party loggers
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    logging.getLogger(__name__).info("Enterprise logging framework initialized.")
    
    logging.info(f"Logging framework initialized at level {log_level}.")
