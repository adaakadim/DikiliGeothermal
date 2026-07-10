@echo off
title AI Model Trainer (Random Forest)
echo ================================================================
echo   DIKILI GEOTHERMAL SCADA - AI Model Trainer
echo   Starting Random Forest training pipeline...
echo ================================================================
echo.
echo NOTE: This script requires 'scikit-learn', 'pandas', and 'matplotlib'.
echo If this fails in MSYS2, please run this script in a standard 
echo Windows Python environment (like Anaconda).
echo.
python -m analytics.ai.random_forest.trainer
echo.
pause
