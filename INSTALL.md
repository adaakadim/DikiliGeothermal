# Installation Guide

## Requirements
- Python 3.11 or higher
- Windows 10/11
- At least 4GB of RAM (8GB recommended for historical playback)
- Local SQLite installation

## Setup Instructions

### 1. Extract the Project
Clone the repository or extract the Release Candidate package to your desired directory.

### 2. Create a Virtual Environment
We strongly recommend running the SCADA platform in an isolated Python environment.
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Database Initialization
The Historian uses SQLite and will automatically generate `data/historian.db` upon the first launch. If you wish to flush the database, delete the `.db` file before launching.

### 5. Running the Application
To launch the SCADA main window:
```powershell
python -m gui.app
```

## Troubleshooting
- **No data displayed?** Ensure the `scada.scan_interval_sec` in `config/user_state.yaml` is set to an appropriate positive value.
- **Charts not rendering?** Ensure `matplotlib` is properly installed in the active venv.
- **Missing AI Predictions?** The models are generated dynamically during the first boot. Allow up to 30 seconds for the initial decision boundary generation.
