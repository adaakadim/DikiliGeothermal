"""
tests/fault_scenarios.py
========================
Phase 3.4 AI Validation Framework.
Runs predefined industrial fault scenarios through the AI engine to validate predictive capabilities.
"""

import os
import json
import logging
from datetime import datetime
from copy import deepcopy

from analytics.ai.feature_engineering import FeatureEngineer
from analytics.ai.random_forest.predictor import predict_plant_state

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ai", "reports")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "validation_results.log")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Base Normal State
BASE_DATA = {
    "Temperature (°C)": 96.5,
    "Pressure (bar)": 5.2,
    "Flow Rate (m3/h)": 118.0,
    "Pump Speed (%)": 100.0,
    "Pump Running (0/1)": 1,
    "Motor Current (A)": 55.2,
    "Motor Voltage (V)": 400.0,
    "Motor Power (kW)": 32.0,
    "Pump Operating Hours": 2500.0,
    "Heat Exchanger Inlet Temperature": 96.5,
    "Heat Exchanger Outlet Temperature": 79.1,
    "Heat Exchanger Efficiency": 90.0,
    "District Heating Supply Temperature": 91.5,
    "District Heating Return Temperature": 71.5,
    "Thermal Power (MW)": 8.5,
    "Pressure Drop": 0.52,
    "Daily Energy": 204.0,
    "Outside Air Temperature": 15.0,
    "Plant Load": 70.0,
    "Alarm Count": 0,
    "Health Score": 100.0,
}

SCENARIOS = [
    {
        "name": "SCENARIO 1: NORMAL OPERATION",
        "overrides": {}
    },
    {
        "name": "SCENARIO 2: PUMP OVERLOAD",
        "overrides": {
            "Motor Current (A)": 85.0,
            "Motor Power (kW)": 55.0,
            "Flow Rate (m3/h)": 75.0,
            "Pump Operating Hours": 9000.0
        }
    },
    {
        "name": "SCENARIO 3: HEAT EXCHANGER PERFORMANCE LOSS",
        "overrides": {
            "Heat Exchanger Efficiency": 55.0,
            "Heat Exchanger Outlet Temperature": 86.0, # Hotter return because less heat extracted
            "District Heating Return Temperature": 83.5 # (dT=8) 91.5 - 8
        }
    },
    {
        "name": "SCENARIO 4: PRESSURE INSTABILITY",
        "overrides": {
            "Pressure (bar)": 2.8,
            "Flow Rate (m3/h)": 60.0,
            "Pressure Drop": 0.28
        }
    },
    {
        "name": "SCENARIO 5: SENSOR ANOMALY",
        "overrides": {
            "Temperature (°C)": 150.0,
            "Heat Exchanger Inlet Temperature": 150.0
        }
    }
]


def run_validation():
    from analytics.ai.prediction_history import PredictionHistoryLogger
    engineer = FeatureEngineer()
    history_logger = PredictionHistoryLogger()
    
    logger.info("================================================================")
    logger.info("  PHASE 3.4 - AI VALIDATION AND FAULT SCENARIO TESTING")
    logger.info("================================================================")
    
    results = []
    
    for scenario in SCENARIOS:
        logger.info(f"\nRunning {scenario['name']}...")
        
        # Prepare data
        live_data = deepcopy(BASE_DATA)
        live_data.update(scenario["overrides"])
        
        # Log Inputs
        input_str = ", ".join([f"{k}: {v}" for k, v in scenario["overrides"].items()]) if scenario["overrides"] else "Base conditions"
        logger.info(f"Input Overrides: {input_str}")
        
        # Pipeline execution
        engineered_data = engineer.process_row(live_data)
        prediction = predict_plant_state(engineered_data)
        
        # Log to history database
        history_logger.log_prediction(prediction)
        
        # Save results
        res_summary = {
            "Scenario": scenario["name"],
            "Failure Risk (%)": prediction["Pump Failure Probability (%)"],
            "Health (%)": prediction["Equipment Health (%)"],
            "Maintenance": prediction["Maintenance Required"],
            "Status": prediction["Plant Status"]
        }
        results.append(res_summary)
        
        # Output formatting
        logger.info(f"Failure Risk: {res_summary['Failure Risk (%)']}%")
        logger.info(f"Health:       {res_summary['Health (%)']}%")
        logger.info(f"Maintenance:  {res_summary['Maintenance']}")
        logger.info(f"Status:       {res_summary['Status']}")
        logger.info(f"Confidence:   {prediction['Prediction Confidence (%)']}%")
        logger.info("-" * 40)
        
    logger.info("\nVALIDATION SUMMARY TABLE:")
    logger.info(f"{'SCENARIO':<40} | {'RISK':<5} | {'HEALTH':<6} | {'MAINT':<6} | {'STATUS'}")
    logger.info("-" * 80)
    for res in results:
        name = res['Scenario'].replace('SCENARIO ', '').split(': ')[1]
        logger.info(f"{name:<40} | {res['Failure Risk (%)']:>4.0f}% | {res['Health (%)']:>5.0f}% | {str(res['Maintenance']):<6} | {res['Status']}")

    # Display GUI window for professional presentation
    show_results_gui(results)


def show_results_gui(results):
    import tkinter as tk
    from tkinter import ttk
    from gui.theme import BG_PRIMARY, BG_SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY
    
    root = tk.Tk()
    root.title("DikiliGeothermal - AI Validation Report")
    root.geometry("850x250")
    root.configure(bg=BG_PRIMARY)
    
    # Configure style to match SCADA theme
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview", font=('Consolas', 11), rowheight=30, 
                    background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY)
    style.configure("Treeview.Heading", font=('Consolas', 12, 'bold'), 
                    background="#1f2937", foreground=TEXT_SECONDARY)
    
    # Create title
    lbl = tk.Label(root, text="AI FAULT SCENARIO VALIDATION RESULTS", 
                   bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=('Consolas', 14, 'bold'))
    lbl.pack(pady=10)
    
    # Create Treeview
    columns = ("Scenario", "Risk", "Health", "Maintenance", "Plant Status")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=5)
    
    tree.heading("Scenario", text="SCENARIO")
    tree.heading("Risk", text="RISK (%)")
    tree.heading("Health", text="HEALTH (%)")
    tree.heading("Maintenance", text="MAINTENANCE")
    tree.heading("Plant Status", text="STATUS")
    
    tree.column("Scenario", anchor="w", width=320)
    tree.column("Risk", anchor="center", width=100)
    tree.column("Health", anchor="center", width=100)
    tree.column("Maintenance", anchor="center", width=120)
    tree.column("Plant Status", anchor="center", width=150)
    
    tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Insert Data
    for res in results:
        name = res['Scenario'].replace('SCENARIO ', '').split(': ')[1]
        tree.insert("", "end", values=(
            name,
            f"{res['Failure Risk (%)']:.0f}%",
            f"{res['Health (%)']:.0f}%",
            str(res['Maintenance']).upper(),
            res['Status']
        ))
        
    # Bring window to front
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    
    root.mainloop()

if __name__ == "__main__":
    run_validation()
