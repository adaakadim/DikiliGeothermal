"""
analytics/ai/random_forest/trainer.py
=====================================
Orchestrates the training pipeline for the Random Forest predictive models.
Loads data, splits into Train/Test, trains models, evaluates them, and
saves the versioned artifacts.
"""

import os
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from analytics.ai.random_forest.metrics import evaluate_model
from analytics.ai.random_forest.feature_importance import extract_and_plot_importance
from analytics.ai.random_forest.version_manager import save_model

logger = logging.getLogger(__name__)

# Data file path (generated in Phase 3.1)
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ai", "historical_dataset.csv")

def train_all_models():
    """
    Main entry point for retraining the AI engine.
    """
    logger.info("Training Started")
    
    if not os.path.exists(DATA_PATH):
        logger.error(f"Dataset not found at {DATA_PATH}. Please run Phase 3.1 dataset generation first.")
        print(f"[!] WARNING: Dataset not found: {DATA_PATH}")
        return
        
    logger.info("Loading Dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # We ignore non-numeric features like Timestamp and String IDs for RF
    ignore_cols = ["Timestamp", "Well ID"]
    
    # Identify target columns vs feature columns
    target_cols = [c for c in df.columns if c.startswith("Target_")]
    feature_cols = [c for c in df.columns if c not in target_cols and c not in ignore_cols]
    
    X = df[feature_cols].fillna(0)
    
    # Target 1: Pump Failure
    target_pump = "Target_Pump_Failure"
    if target_pump in df.columns:
        logger.info(f"Training Model: {target_pump}")
        y = df[target_pump]
        _train_evaluate_save("PumpFailure_RF", X, y, feature_cols)
        
    # Target 2: Maintenance Required
    target_maint = "Target_Maintenance_Required"
    if target_maint in df.columns:
        logger.info(f"Training Model: {target_maint}")
        y = df[target_maint]
        _train_evaluate_save("Maintenance_RF", X, y, feature_cols)

    logger.info("Training Completed")
    print("\n[+] All Random Forest models successfully trained, evaluated, and versioned!")

def _train_evaluate_save(model_name: str, X: pd.DataFrame, y: pd.Series, feature_names: list):
    """
    Sub-routine to train a single RF model target.
    """
    logger.info(f"Splitting dataset (80/20) for {model_name}...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    logger.info(f"Initializing RandomForestClassifier for {model_name}...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    
    logger.info(f"Fitting model {model_name}...")
    rf.fit(X_train, y_train)
    
    logger.info(f"Evaluating model {model_name}...")
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test) if hasattr(rf, "predict_proba") else None
    
    # 1. Metrics & Reports
    evaluate_model(model_name, y_test, y_pred, y_prob)
    
    # 2. Feature Importance
    extract_and_plot_importance(rf, model_name, feature_names)
    
    # 3. Versioning
    logger.info(f"Saving Model {model_name}...")
    save_model(rf, model_name)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    train_all_models()
