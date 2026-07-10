"""
analytics/anomaly_detection/root_cause_analyzer.py
==================================================
Identifies the most likely sensor contributors to a detected anomaly
by ranking deviation magnitudes.
"""

from typing import Dict, Any, List

# Friendly names for SCADA parameters
_FRIENDLY_NAMES = {
    "Wellhead Temperature (°C)": "Wellhead Temperature",
    "Wellhead Pressure (bar)": "Wellhead Pressure",
    "GW-01 Flow Rate (t/h)": "Flow Rate",
    "P-101 Motor Current (A)": "Motor Current",
    "P-101 Motor Power (kW)": "Motor Power",
    "P-101 Discharge Pressure (bar)": "Pump Discharge Pressure",
    "HX-101 Primary Inlet Temp (°C)": "HX Primary Inlet Temp",
    "HX-101 Primary Outlet Temp (°C)": "HX Primary Outlet Temp",
    "HX-101 Secondary Inlet Temp (°C)": "HX Secondary Inlet Temp",
    "HX-101 Secondary Outlet Temp (°C)": "HX Secondary Outlet Temp",
    "Health Score": "Equipment Health Score",
}

# Engineering explanations for high deviations
_EXPLANATIONS = {
    "Motor Current": "Elevated motor current suggests increased mechanical load or bearing wear.",
    "Flow Rate": "Flow instability may indicate partial valve closure or wellhead pressure changes.",
    "Wellhead Pressure": "Pressure deviation from nominal range may signal reservoir changes or scaling.",
    "Wellhead Temperature": "Temperature anomaly may indicate changes in geothermal fluid composition.",
    "Motor Power": "Abnormal power consumption often correlates with pump cavitation or overload.",
    "Pump Discharge Pressure": "Discharge pressure deviation indicates potential pump performance degradation.",
    "HX Primary Inlet Temp": "Inlet temperature shift may signal changes in production well output.",
    "HX Primary Outlet Temp": "Outlet temperature anomaly suggests heat exchanger fouling or bypass.",
    "HX Secondary Inlet Temp": "District heating return temperature anomaly indicates load imbalance.",
    "HX Secondary Outlet Temp": "Supply temperature deviation affects district heating performance.",
    "Equipment Health Score": "Overall health degradation detected across multiple subsystems.",
}


class RootCauseAnalyzer:
    """
    Ranks anomaly contributors and generates engineering explanations.
    """

    def analyze(self, deviations: Dict[str, float], anomaly_score: float) -> Dict[str, Any]:
        """
        Analyze deviations to identify root causes.
        
        Returns:
            Dict with primary/secondary/tertiary contributors and explanation text.
        """
        if not deviations or anomaly_score < 15.0:
            return {
                "primary": "None",
                "secondary": "None",
                "tertiary": "None",
                "contributors": [],
                "explanation": "All parameters are within normal operating ranges."
            }

        # Sort by deviation magnitude, descending
        ranked = sorted(deviations.items(), key=lambda x: x[1], reverse=True)

        # Map to friendly names
        contributors = []
        for param, dev in ranked:
            friendly = _FRIENDLY_NAMES.get(param, param)
            contributors.append({
                "parameter": friendly,
                "raw_parameter": param,
                "deviation": dev,
                "contribution_pct": 0.0  # filled below
            })

        # Calculate contribution percentages
        total_dev = sum(c["deviation"] for c in contributors)
        if total_dev > 0:
            for c in contributors:
                c["contribution_pct"] = (c["deviation"] / total_dev) * 100.0

        primary = contributors[0]["parameter"] if len(contributors) > 0 else "None"
        secondary = contributors[1]["parameter"] if len(contributors) > 1 else "None"
        tertiary = contributors[2]["parameter"] if len(contributors) > 2 else "None"

        # Build explanation
        explanation_parts = []
        for c in contributors[:3]:
            expl = _EXPLANATIONS.get(c["parameter"], f"{c['parameter']} shows significant deviation.")
            if c["deviation"] > 1.5:
                explanation_parts.append(expl)

        if not explanation_parts:
            explanation_text = f"Minor deviations detected. Primary contributor: {primary}."
        else:
            explanation_text = " ".join(explanation_parts)

        return {
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "contributors": contributors[:5],
            "explanation": explanation_text
        }
