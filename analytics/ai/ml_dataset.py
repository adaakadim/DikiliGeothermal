"""
analytics/ai/ml_dataset.py
==========================
Orchestrator for the AI machine learning dataset generation process.
Coordinates the simulator, applies feature engineering, and exports the data
to disk for downstream ML algorithms (Random Forest, XGBoost, etc.).
"""

import os
import csv
import logging
from datetime import datetime

from analytics.ai.dataset_generator import generate_raw_dataset
from analytics.ai.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)

def generate_and_save_dataset(records_needed: int = 10000):
    """
    Generates the historical ML dataset and saves it to data/ai/.
    """
    print("=========================================================")
    print("  PHASE 3.1: AI DATASET GENERATION")
    print("=========================================================")
    print(f"[*] Simulating {records_needed} historical operating records...")
    
    # 1. Generate Raw Data
    raw_data = generate_raw_dataset(records_needed=records_needed)
    print("[*] Raw data generation complete.")
    
    # 2. Feature Engineering
    print("[*] Applying feature engineering (rolling windows, indices)...")
    engineer = FeatureEngineer(window_size=5)
    final_data = engineer.process_dataset(raw_data)
    
    # 3. Export
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ai")
    os.makedirs(out_dir, exist_ok=True)
    
    csv_path = os.path.join(out_dir, "historical_dataset.csv")
    
    if not final_data:
        print("[!] No data generated.")
        return
        
    headers = list(final_data[0].keys())
    
    print(f"[*] Saving dataset to {csv_path} ...")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(final_data)
        
    # Metrics calculation
    feature_count = sum(1 for h in headers if h.startswith("Feature_"))
    target_count = sum(1 for h in headers if h.startswith("Target_"))
    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    
    print("=========================================================")
    print("  DATASET SUCCESSFULLY GENERATED")
    print("=========================================================")
    print(f"Number of records: {len(final_data)}")
    print(f"Total columns:     {len(headers)}")
    print(f"Feature count:     {feature_count}")
    print(f"Target count:      {target_count}")
    print(f"Dataset size:      {file_size_mb:.2f} MB")
    print(f"Output Path:       {csv_path}")
    print("=========================================================")
    print("Note: Excel (.xlsx) format export was skipped due to missing 'openpyxl'")
    print("      dependency in the MSYS2 environment. The CSV file is fully compatible")
    print("      with Excel, Pandas, and XGBoost.")
    print("=========================================================")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_and_save_dataset(records_needed=10000)
