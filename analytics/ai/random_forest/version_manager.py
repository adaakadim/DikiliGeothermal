"""
analytics/ai/random_forest/version_manager.py
=============================================
Manages versioning, saving, and loading of trained Random Forest models.
Ensures previous versions are never overwritten.
"""

import os
import glob
import pickle
import logging
from typing import Any, Tuple

logger = logging.getLogger(__name__)

# Output directory for models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ai", "models")

def _ensure_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)

def save_model(model: Any, model_name: str) -> str:
    """
    Saves a model as a new version (e.g., random_forest_v1.pkl) and updates
    the 'latest' pointer file.
    
    Returns the path to the saved version.
    """
    _ensure_dir()
    
    # Find next version number
    existing_files = glob.glob(os.path.join(MODEL_DIR, f"{model_name}_v*.pkl"))
    versions = []
    for f in existing_files:
        try:
            # Extract number from filename
            base = os.path.basename(f)
            v_str = base.replace(f"{model_name}_v", "").replace(".pkl", "")
            versions.append(int(v_str))
        except ValueError:
            continue
            
    next_v = max(versions) + 1 if versions else 1
    
    versioned_filename = f"{model_name}_v{next_v}.pkl"
    latest_filename = f"{model_name}_latest.pkl"
    
    versioned_path = os.path.join(MODEL_DIR, versioned_filename)
    latest_path = os.path.join(MODEL_DIR, latest_filename)
    
    # Save the actual versioned file
    with open(versioned_path, "wb") as f:
        pickle.dump(model, f)
        
    # Save a copy as latest
    with open(latest_path, "wb") as f:
        pickle.dump(model, f)
        
    logger.info(f"Model saved successfully: {versioned_path}")
    logger.info(f"Latest pointer updated: {latest_path}")
    
    return versioned_path

def load_latest_model(model_name: str) -> Any:
    """
    Loads the '_latest.pkl' version of the specified model.
    """
    latest_path = os.path.join(MODEL_DIR, f"{model_name}_latest.pkl")
    if not os.path.exists(latest_path):
        logger.warning(f"No latest model found for {model_name} at {latest_path}")
        return None
        
    from analytics.ai.random_forest.model_metadata import ModelMetadataManager
    from security.audit import AuditLogger
    
    # 1. Verify model integrity (SHA-256 Checksum)
    if not ModelMetadataManager.validate_model_integrity(model_name, latest_path):
        logger.error(f"Integrity Failure: Model '{model_name}' failed hash validation. Model will not be loaded.")
        AuditLogger.log_event("Model Loading", "analytics.ai", "FAIL", "CRIT", details=f"Model failed checksum validation: {model_name}")
        return None
        
    try:
        with open(latest_path, "rb") as f:
            model = pickle.load(f)
            
        # 2. Verify model version and feature details
        ModelMetadataManager.validate_model_integrity(model_name, latest_path, loaded_model=model)
        logger.info(f"Model Loaded: '{model_name}' successfully loaded and verified.")
        AuditLogger.log_event("Model Loading", "analytics.ai", "SUCCESS", "INFO", details=f"Loaded latest model: {model_name}")
        return model
    except Exception as e:
        logger.error(f"Failed to load latest model for {model_name}: {e}")
        AuditLogger.log_event("Model Loading", "analytics.ai", "FAIL", "CRIT", details=f"Failed to load model {model_name}: {e}")
        return None
