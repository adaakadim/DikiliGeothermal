"""
tests/test_model_integrity.py
==============================
Automated unit tests for the AI Model Integrity & Version Verification framework.
"""

import sys
from unittest.mock import MagicMock

# Mock optional packages to run tests without HMI plotting requirements
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['matplotlib.animation'] = MagicMock()
sys.modules['matplotlib.gridspec'] = MagicMock()
sys.modules['matplotlib.lines'] = MagicMock()
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import os
import json
import shutil
import pytest
from analytics.ai.random_forest.model_metadata import ModelMetadataManager
from analytics.ai.random_forest.version_manager import load_latest_model, MODEL_DIR

@pytest.fixture
def backup_manifest():
    manifest_path = ModelMetadataManager.get_manifest_path()
    backup_path = manifest_path + ".bak"
    if os.path.exists(manifest_path):
        shutil.copyfile(manifest_path, backup_path)
    yield manifest_path
    # Restore
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, manifest_path)
        os.remove(backup_path)

def test_calculate_checksum():
    test_file = os.path.join(MODEL_DIR, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("hello world")
        
    checksum = ModelMetadataManager.calculate_checksum(test_file)
    # Expected SHA-256 for "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert checksum == expected
    os.remove(test_file)

def test_successful_integrity_validation(backup_manifest):
    # Verify both models match the manifest checksums
    assert ModelMetadataManager.validate_model_integrity(
        "PumpFailure_RF", 
        os.path.join(MODEL_DIR, "PumpFailure_RF_latest.pkl")
    ) is True

    assert ModelMetadataManager.validate_model_integrity(
        "Maintenance_RF", 
        os.path.join(MODEL_DIR, "Maintenance_RF_latest.pkl")
    ) is True

def test_corrupted_model_validation(backup_manifest):
    # Create a corrupted temporary model file
    corrupt_path = os.path.join(MODEL_DIR, "Corrupt_RF_latest.pkl")
    with open(corrupt_path, "wb") as f:
        f.write(b"invalid_pickle_data_corrupt")

    # Update manifest to expect a different hash
    manifest = ModelMetadataManager.load_manifest()
    manifest["Corrupt_RF"] = {
        "model_name": "Corrupt_RF",
        "sha256": "wrong_expected_hash",
        "feature_count": 21
    }
    with open(backup_manifest, "w") as f:
        json.dump(manifest, f)

    # Validation should reject the file
    assert ModelMetadataManager.validate_model_integrity("Corrupt_RF", corrupt_path) is False
    os.remove(corrupt_path)

def test_missing_manifest(backup_manifest):
    # Remove manifest
    if os.path.exists(backup_manifest):
        os.remove(backup_manifest)
        
    # Validation should fail
    model_path = os.path.join(MODEL_DIR, "PumpFailure_RF_latest.pkl")
    assert ModelMetadataManager.validate_model_integrity("PumpFailure_RF", model_path) is False

def test_feature_count_warning(backup_manifest):
    class DummyModel:
        n_features_in_ = 10 # Model actually has 10 features
        feature_names_in_ = ["col1", "col2"]

    # Manifest expects 21 features
    manifest = ModelMetadataManager.load_manifest()
    assert manifest["PumpFailure_RF"]["feature_count"] == 21

    # Should print a warning but return True (warnings do not block fallback load)
    model_path = os.path.join(MODEL_DIR, "PumpFailure_RF_latest.pkl")
    result = ModelMetadataManager.validate_model_integrity(
        "PumpFailure_RF", 
        model_path, 
        loaded_model=DummyModel()
    )
    assert result is True
