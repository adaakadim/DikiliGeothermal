"""
analytics/ai/random_forest/metrics.py
=====================================
Calculates model performance metrics and generates structured reports.
"""

import os
import logging
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ai", "reports")

def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)

def evaluate_model(model_name: str, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None):
    """
    Calculates metrics and saves text reports and confusion matrix plots.
    """
    _ensure_dir()
    logger.info(f"Evaluating model: {model_name}")
    
    # Calculate metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    
    auc = None
    if y_prob is not None and len(np.unique(y_true)) == 2:
        try:
            auc = roc_auc_score(y_true, y_prob[:, 1])
        except Exception as e:
            logger.warning(f"Could not calculate ROC AUC: {e}")
            
    # Terminal Output
    print(f"\n--- Performance: {model_name} ---")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Precision: {prec*100:.2f}%")
    print(f"Recall:    {rec*100:.2f}%")
    print(f"F1 Score:  {f1*100:.2f}%")
    if auc is not None:
        print(f"ROC AUC:   {auc:.4f}")
        
    # Generate Confusion Matrix Image
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title(f"{model_name} Confusion Matrix")
    plt.colorbar()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    cm_path = os.path.join(REPORT_DIR, f"{model_name}_confusion_matrix.png")
    plt.savefig(cm_path)
    plt.close()
    
    # Save Reports
    clf_report = classification_report(y_true, y_pred, zero_division=0)
    
    report_path = os.path.join(REPORT_DIR, f"{model_name}_training_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Training Report for {model_name}\n")
        f.write("="*40 + "\n")
        f.write(f"Accuracy:  {acc*100:.2f}%\n")
        f.write(f"Precision: {prec*100:.2f}%\n")
        f.write(f"Recall:    {rec*100:.2f}%\n")
        f.write(f"F1 Score:  {f1*100:.2f}%\n")
        if auc is not None:
            f.write(f"ROC AUC:   {auc:.4f}\n")
            
    class_report_path = os.path.join(REPORT_DIR, f"{model_name}_classification_report.txt")
    with open(class_report_path, "w", encoding="utf-8") as f:
        f.write(clf_report)
        
    logger.info(f"Saved evaluation reports to {REPORT_DIR}")
