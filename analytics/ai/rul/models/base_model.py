"""
analytics/ai/rul/models/base_model.py
=====================================
Abstract interfaces for Remaining Useful Life (RUL) estimation models.
Prepares the architecture for Future Compatibility with Deep Learning, LSTM, 
Transformers, and Physics-Informed Neural Networks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseRULModel(ABC):
    """
    Abstract base class for all RUL estimation models.
    """
    @abstractmethod
    def estimate_rul(self, eq_id: str, live_data: Dict[str, Any], ai_result: Dict[str, Any], health_index: float) -> float:
        """
        Estimate the Remaining Useful Life (in hours).
        
        Parameters:
            eq_id (str): Equipment identifier (e.g. "P-101")
            live_data (dict): Telemetry parameters
            ai_result (dict): Outputs from predictive models (Failure Probability)
            health_index (float): Output from Health Index Engine (0-100)
            
        Returns:
            float: Remaining Useful Life in hours.
        """
        pass

class DeepLearningRULModel(BaseRULModel):
    """
    Interface for sequence-based models like LSTM or Transformers.
    """
    @abstractmethod
    def estimate_rul(self, eq_id: str, live_data: Dict[str, Any], ai_result: Dict[str, Any], health_index: float) -> float:
        # Placeholder for future implementation where live_data is converted to a timeseries window
        raise NotImplementedError("Deep learning RUL model not yet implemented.")

class PhysicsInformedRULModel(BaseRULModel):
    """
    Interface for Physics-Informed Neural Networks (PINNs).
    Combines thermodynamic constraints with machine learning.
    """
    @abstractmethod
    def estimate_rul(self, eq_id: str, live_data: Dict[str, Any], ai_result: Dict[str, Any], health_index: float) -> float:
        raise NotImplementedError("Physics-informed RUL model not yet implemented.")
