"""
core/logging/correlation.py
===========================
Centralized correlation context manager for distributed logging and tracing.
Provides thread-safe and asyncio-safe Correlation ID propagation.
"""

import uuid
import contextvars
from contextlib import contextmanager
import logging
from collections import deque
from threading import Lock
from typing import Optional, List

# Thread-safe and asyncio-safe context variable for correlation ID
_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('correlation_id', default=None)

def set_correlation_id(cid: Optional[str] = None) -> str:
    """Sets the correlation ID for the current context. Generates a new one if not provided."""
    if not cid:
        cid = str(uuid.uuid4())
    _correlation_id.set(cid)
    return cid

def get_correlation_id() -> Optional[str]:
    """Retrieves the current correlation ID."""
    return _correlation_id.get()

def clear_correlation_id() -> None:
    """Clears the correlation ID from the current context."""
    _correlation_id.set(None)

@contextmanager
def correlation_context(cid: Optional[str] = None):
    """
    Context manager to safely set and revert the correlation ID.
    Perfect for nested operations or temporarily handling a sub-task.
    """
    token = _correlation_id.set(cid or str(uuid.uuid4()))
    try:
        yield get_correlation_id()
    finally:
        _correlation_id.reset(token)

class CorrelationLogFilter(logging.Filter):
    """Injects the correlation ID into all LogRecord objects."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        cid = get_correlation_id()
        record.correlation_id = cid if cid else "NO-CORRELATION"
        return True

class CorrelationRingBufferHandler(logging.Handler):
    """
    In-memory ring buffer that stores recent log records.
    Allows diagnostic modules to retrieve all logs associated with a specific correlation ID.
    """
    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self._lock = Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # We must format the record now to resolve the message before storing,
            # but we will store the actual record for querying.
            self.format(record)
            with self._lock:
                self.buffer.append(record)
        except Exception:
            self.handleError(record)
            
    def get_events_by_correlation_id(self, cid: str) -> List[logging.LogRecord]:
        """Retrieve all captured events matching a given correlation ID."""
        with self._lock:
            # Create a shallow copy to iterate over safely
            return [record for record in self.buffer if getattr(record, 'correlation_id', None) == cid]
