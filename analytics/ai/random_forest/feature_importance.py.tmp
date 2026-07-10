"""
analytics/ai/random_forest/feature_importance.py
================================================
Extracts and visualizes the most important signals the Random Forest model
is using to make predictions.
"""

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Any

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ai", "reports")

def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)

def extract_and_plot_importance(model: Any, model_name: str, feature_names: List[str]):
    """
    Extracts feature_importances_ from a trained RandomForest model, saves
    it to a CSV, and generates a horizontal bar chart.
    """
    _ensure_dir()
    logger.info(f"Extracting feature importance for {model_name}")
    
    if not hasattr(model, "feature_importances_"):
        logger.error(f"Model {model_name} does not expose feature_importances_")
        return
        
    importances = model.feature_importances_
    
    # Create a DataFrame for easy sorting and saving
    df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    })
    df = df.sort_values(by="Importance", ascending=False)
    
    # Save to CSV
    csv_path = os.path.join(REPORT_DIR, f"{model_name}_feature_importance.csv")
    df.to_csv(csv_path, index=False)
    
    import textwrap
    
    # Generate Chart
    # Take top 15 features for readability
    top_df = df.head(15).sort_values(by="Importance", ascending=True)
    
    # Wrap long feature names to avoid overlapping on the Y-axis
    wrapped_labels = [textwrap.fill(str(label), width=20) for label in top_df["Feature"]]
    
    plt.figure(figsize=(12, 8))
    plt.barh(wrapped_labels, top_df["Importance"], color="steelblue")
    plt.xlabel("Importance Score", fontsize=12)
    plt.title(f"Top 15 Feature Importances: {model_name}", fontsize=14)
    
    # Decrease Y-axis font size so words don't crash into each other vertically
    plt.yticks(fontsize=9)
    
    # Ensure layout fits everything perfectly
    plt.tight_layout()
    plt.subplots_adjust(left=0.3) # Extra padding just in case
    
    png_path = os.path.join(REPORT_DIR, f"{model_name}_feature_importance.png")
    plt.savefig(png_path, bbox_inches="tight", dpi=150)
    plt.close()
    
    logger.info(f"Saved feature importance outputs to {REPORT_DIR}")
