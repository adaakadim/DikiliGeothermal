"""
core/performance/memory_monitor.py
==================================
Lightweight Memory Monitor for tracking long-running SCADA HMI memory usage.
Uses Windows ctypes API for precise RSS / Working Set queries without psutil.
"""

import gc
import logging
import sys
from typing import Tuple, Dict, Any

logger = logging.getLogger("core.performance")

# Win32 structures for GetProcessMemoryInfo
_is_windows = sys.platform.startswith("win")
if _is_windows:
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

class MemoryMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MemoryMonitor, cls).__new__(cls)
            cls._instance._peak_usage_mb = 0.0
        return cls._instance

    def __init__(self):
        from core.configuration import config
        self._warning_threshold_mb = config.get("performance.memory_warning_mb", 500.0)

    def get_memory_usage_mb(self) -> Tuple[float, float]:
        """
        Query current memory (RSS Working Set) and peak memory usage in Megabytes.
        Returns: (current_mb, peak_mb)
        """
        current_bytes = 0
        peak_bytes = 0
        
        if _is_windows:
            try:
                process = ctypes.windll.kernel32.GetCurrentProcess()
                counters = PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(counters)
                if ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
                    current_bytes = counters.WorkingSetSize
                    peak_bytes = counters.PeakWorkingSetSize
            except Exception as e:
                logger.debug(f"Failed to query Windows memory info: {e}")
                
        # Fallback to sys.getsizeof or mock/dummy values if not Windows or if call fails
        if current_bytes == 0:
            # Unix fallback: resource module
            try:
                import resource
                # resource.getrusage returns in kilobytes on Linux, bytes on macOS
                usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                current_bytes = usage * 1024 if sys.platform != "darwin" else usage
                peak_bytes = current_bytes
            except Exception:
                # Absolute fallback
                current_bytes = 100 * 1024 * 1024 # 100MB dummy
                peak_bytes = 100 * 1024 * 1024

        curr_mb = current_bytes / (1024.0 * 1024.0)
        peak_mb = peak_bytes / (1024.0 * 1024.0)
        
        if peak_mb > self._peak_usage_mb:
            self._peak_usage_mb = peak_mb
            
        return curr_mb, max(peak_mb, self._peak_usage_mb)

    def check_memory_thresholds(self):
        """Scans current usage and logs warnings if threshold limit is crossed."""
        curr_mb, peak_mb = self.get_memory_usage_mb()
        if curr_mb > self._warning_threshold_mb:
            logger.warning(
                f"[MEMORY ALERT] High Memory Usage Detected! "
                f"Current: {curr_mb:.2f} MB, Threshold: {self._warning_threshold_mb:.2f} MB. "
                f"Peak: {peak_mb:.2f} MB. Running garbage collection..."
            )
            self.perform_cleanup()

    def perform_cleanup(self):
        """Forces garbage collection and releases Matplotlib figures to free RAM."""
        gc.collect()
        try:
            # Release matplotlib figure memory to prevent leaks in GUI dashboards
            import matplotlib.pyplot as plt
            plt.close("all")
            logger.info("Cleared all Matplotlib figure references.")
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Failed to clear matplotlib figures: {e}")
            
        logger.info("Forced garbage collection cycle completed.")

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        curr_mb, peak_mb = self.get_memory_usage_mb()
        return {
            "current_usage_mb": round(curr_mb, 2),
            "peak_usage_mb": round(peak_mb, 2),
            "warning_threshold_mb": self._warning_threshold_mb,
            "garbage_collector_enabled": gc.isenabled()
        }
