"""
security/audit.py
=================
Enterprise Security Audit Trail layer.
Records security-sensitive operations with structured JSON outputs.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any

logger = logging.getLogger("security.audit")

class AuditLogger:
    @staticmethod
    def log_event(
        action: str,
        module: str,
        result: str,
        severity: str,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[str] = None
    ):
        """
        Log a security-sensitive event to the audit trail.
        Uses structured JSON payload for future log consolidation/SIEM ingestion.
        """
        record = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_id": session_id or "NO_SESSION",
            "username": username or "SYSTEM",
            "action": action,
            "module": module,
            "result": result,
            "severity": severity.upper(),
            "details": details or ""
        }
        
        # Select logging severity
        lvl = logging.INFO
        sev = severity.upper()
        if sev == "WARN" or sev == "WARNING":
            lvl = logging.WARNING
        elif sev == "CRIT" or sev == "CRITICAL" or sev == "FATAL":
            lvl = logging.CRITICAL
            
        logger.log(lvl, json.dumps(record))
        
        # SIEM Export interface hook
        AuditLogger.export_to_siem(record)

    @staticmethod
    def export_to_siem(record: dict):
        """
        Placeholder interface for SIEM (Splunk/ELK/Datadog) syslog ingestion.
        """
        pass
