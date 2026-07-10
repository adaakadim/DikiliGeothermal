"""
tests/test_correlation.py
=========================
Automated unit tests for the Correlation ID & Distributed Logging Framework.
"""

import sys
import logging
import pytest
import asyncio
import threading
import time
from unittest.mock import patch

from core.logging.correlation import (
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id,
    correlation_context,
    CorrelationLogFilter,
    CorrelationRingBufferHandler
)


@pytest.fixture(autouse=True)
def reset_context():
    clear_correlation_id()
    yield
    clear_correlation_id()

def test_correlation_id_generation():
    cid1 = set_correlation_id()
    assert cid1 is not None
    assert get_correlation_id() == cid1
    
    cid2 = set_correlation_id("custom-id-123")
    assert cid2 == "custom-id-123"
    assert get_correlation_id() == "custom-id-123"
    
    clear_correlation_id()
    assert get_correlation_id() is None

def test_correlation_context_manager():
    with correlation_context("test-ctx") as cid:
        assert cid == "test-ctx"
        assert get_correlation_id() == "test-ctx"
        
        with correlation_context("nested-ctx") as nested_cid:
            assert nested_cid == "nested-ctx"
            assert get_correlation_id() == "nested-ctx"
            
        # Should restore parent context
        assert get_correlation_id() == "test-ctx"
        
    # Should clear after exit
    assert get_correlation_id() is None

def test_logging_filter_enrichment():
    filter_obj = CorrelationLogFilter()
    record = logging.LogRecord("name", logging.INFO, "pathname", 1, "msg", (), None)
    
    # Without context
    filter_obj.filter(record)
    assert record.correlation_id == "NO-CORRELATION"
    
    # With context
    set_correlation_id("log-id-555")
    filter_obj.filter(record)
    assert record.correlation_id == "log-id-555"

def test_ring_buffer_handler():
    buffer = CorrelationRingBufferHandler(capacity=2)
    buffer.setFormatter(logging.Formatter("%(message)s [%(correlation_id)s]"))
    
    # Mock records
    r1 = logging.LogRecord("test", logging.INFO, "path", 1, "msg1", (), None)
    r1.correlation_id = "cid-A"
    
    r2 = logging.LogRecord("test", logging.INFO, "path", 2, "msg2", (), None)
    r2.correlation_id = "cid-B"
    
    r3 = logging.LogRecord("test", logging.INFO, "path", 3, "msg3", (), None)
    r3.correlation_id = "cid-A"
    
    buffer.emit(r1)
    buffer.emit(r2)
    buffer.emit(r3)
    
    # Buffer capacity is 2, so r1 should be evicted. Only r2 and r3 remain.
    events_a = buffer.get_events_by_correlation_id("cid-A")
    assert len(events_a) == 1
    assert events_a[0].msg == "msg3"
    
    events_b = buffer.get_events_by_correlation_id("cid-B")
    assert len(events_b) == 1
    assert events_b[0].msg == "msg2"

def test_asyncio_context_propagation():
    async def _async_test():
        async def worker(expected_cid):
            assert get_correlation_id() == expected_cid
            with correlation_context(expected_cid + "-nested"):
                assert get_correlation_id() == expected_cid + "-nested"
                await asyncio.sleep(0.01)
                assert get_correlation_id() == expected_cid + "-nested"
            assert get_correlation_id() == expected_cid

        set_correlation_id("async-root")
        t1 = asyncio.create_task(worker("async-root"))
        t2 = asyncio.create_task(worker("async-root"))
        
        await asyncio.gather(t1, t2)
        assert get_correlation_id() == "async-root"
        
    asyncio.run(_async_test())

def test_threading_isolation():
    def thread_worker(cid, results):
        set_correlation_id(cid)
        time.sleep(0.01)
        results.append(get_correlation_id())

    set_correlation_id("main-thread")
    
    results = []
    t1 = threading.Thread(target=thread_worker, args=("thread-1", results))
    t2 = threading.Thread(target=thread_worker, args=("thread-2", results))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    assert "thread-1" in results
    assert "thread-2" in results
    assert get_correlation_id() == "main-thread"
