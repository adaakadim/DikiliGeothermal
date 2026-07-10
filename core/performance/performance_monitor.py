"""
core/performance/performance_monitor.py
======================================
Performance Monitoring & Profiling Framework for industrial Digital Twin operation.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("core.performance")

class PerformanceMonitor:
    _instance = None
    _lock = threading_lock = None # placeholder

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._inference_latencies: List[float] = []
        self._alarm_processing_latencies: List[float] = []
        self._snapshots: List[Dict[str, Any]] = []
        
        # Load configs
        from core.configuration import config
        self._max_history = config.get("performance.performance_monitor.history_size", 100)
        self._ai_threshold = config.get("performance.performance_monitor.ai_warning_s", 1.0)
        
        self._initialized = True

    def record_ai_inference(self, duration_s: float):
        """Records an AI inference timing."""
        self._inference_latencies.append(duration_s)
        if len(self._inference_latencies) > self._max_history:
            self._inference_latencies.pop(0)
            
        if duration_s > self._ai_threshold:
            logger.warning(
                f"[PERFORMANCE WARNING] AI Inference duration {duration_s:.3f}s "
                f"exceeded threshold of {self._ai_threshold:.2f}s."
            )

    def record_alarm_processing(self, duration_s: float):
        """Records alarm scan duration."""
        self._alarm_processing_latencies.append(duration_s)
        if len(self._alarm_processing_latencies) > self._max_history:
            self._alarm_processing_latencies.pop(0)

    def collect_snapshot(self) -> Dict[str, Any]:
        """Gathers system metrics across subsystems and stores a history snapshot."""
        metrics = self.get_current_metrics()
        self._snapshots.append({
            "timestamp": time.time(),
            "metrics": metrics
        })
        if len(self._snapshots) > self._max_history:
            self._snapshots.pop(0)
        return metrics

    def get_current_metrics(self) -> Dict[str, Any]:
        """Queries and aggregates statistics from all performance components."""
        # 1. Memory metrics
        from core.performance.memory_monitor import MemoryMonitor
        mem_stats = MemoryMonitor().get_stats()
        
        # 2. Scheduler metrics
        from core.scheduler.enterprise_scheduler import EnterpriseScheduler
        try:
            sched_stats = EnterpriseScheduler().get_diagnostics()
        except Exception:
            sched_stats = []
            
        # 3. Historian metrics
        historian_stats = {}
        try:
            # We look up the global historian instance if it exists, or fetch mock stats
            from core.historian.historian import DataHistorian
            # Create a temp instance to query if path is default
            hist = DataHistorian()
            historian_stats = hist.get_health_status()
            hist.close()
        except Exception as e:
            logger.debug(f"Could not fetch historian health: {e}")
            
        # 4. Rendering metrics (if GUI registered)
        render_stats = {}
        
        avg_ai = sum(self._inference_latencies) / len(self._inference_latencies) if self._inference_latencies else 0.0
        max_ai = max(self._inference_latencies) if self._inference_latencies else 0.0
        avg_alarm = sum(self._alarm_processing_latencies) / len(self._alarm_processing_latencies) if self._alarm_processing_latencies else 0.0
        
        return {
            "memory": mem_stats,
            "scheduler": sched_stats,
            "historian": historian_stats,
            "ai_inference": {
                "avg_latency_ms": round(avg_ai * 1000, 2),
                "max_latency_ms": round(max_ai * 1000, 2),
                "total_runs": len(self._inference_latencies)
            },
            "alarm_manager": {
                "avg_scan_latency_ms": round(avg_alarm * 1000, 2)
            }
        }

    def reset_statistics(self):
        """Clears accumulated profiling buffers."""
        self._inference_latencies.clear()
        self._alarm_processing_latencies.clear()
        self._snapshots.clear()
        logger.info("Performance statistics buffers cleared.")

    def export_statistics(self, filepath: str) -> bool:
        """Saves current metrics snapshot history to an external JSON report."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "exported_at": time.time(),
                    "snapshots": self._snapshots,
                    "summary": self.get_current_metrics()
                }, f, indent=2)
            logger.info(f"Performance statistics exported successfully to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export performance stats to {filepath}: {e}")
            return False
