"""
analytics/ai/lifecycle/dataset_validator.py
===========================================
Validates incoming ml_data vectors for missing or anomalous entries.
"""

from typing import Dict, Any, Tuple

class DatasetValidator:
    def validate(self, ml_data: Dict[str, float]) -> Tuple[float, list]:
        """
        Evaluate real-time data quality.
        Returns:
            quality_score (0.0 to 100.0)
            issues (List[str])
        """
        if not ml_data:
            return 0.0, ["Empty dataset provided."]
            
        issues = []
        valid_count = 0
        total_count = len(ml_data)
        
        for feature, val in ml_data.items():
            if val is None:
                issues.append(f"Missing Value: '{feature}' is null.")
            elif isinstance(val, (int, float)):
                # Detect impossible physical values
                if "Temperature" in feature and (val < -50 or val > 500):
                    issues.append(f"Invalid Sensor Value: '{feature}' ({val}) is out of physical bounds.")
                elif "Pressure" in feature and (val < 0 or val > 200):
                    issues.append(f"Invalid Sensor Value: '{feature}' ({val}) is out of physical bounds.")
                else:
                    valid_count += 1
            else:
                issues.append(f"Type Error: '{feature}' has non-numeric value ({val}).")
                
        quality_score = (valid_count / total_count) * 100.0 if total_count > 0 else 0.0
        
        return quality_score, issues
