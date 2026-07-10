"""
analytics/ai/rul/health_decay.py
================================
Physics-informed heuristic health decay model.
Estimates the continuous degradation of equipment health based on operational stress.
"""

class HealthDecayModel:
    def __init__(self, nominal_life_hours: float = 10000.0):
        self.nominal_life_hours = nominal_life_hours
        
    def calculate_decay_rate(self, failure_probability: float, current_health: float) -> float:
        """
        Calculate the current degradation rate (health lost per hour).
        
        Parameters:
            failure_probability (float): 0-100% from AI model.
            current_health (float): 0-100% from Health Index model.
            
        Returns:
            float: degradation rate multiplier (1.0 = nominal, >1.0 = accelerated).
        """
        # Nominal decay rate
        base_rate = 1.0
        
        # Accelerated decay due to high failure probability (stress)
        if failure_probability > 80.0:
            stress_multiplier = 5.0
        elif failure_probability > 50.0:
            stress_multiplier = 2.5
        elif failure_probability > 30.0:
            stress_multiplier = 1.5
        else:
            stress_multiplier = 1.0
            
        # As health gets lower, degradation accelerates slightly (wear and tear effect)
        wear_multiplier = 1.0
        if current_health < 40.0:
            wear_multiplier = 1.5
        elif current_health < 70.0:
            wear_multiplier = 1.2
            
        return base_rate * stress_multiplier * wear_multiplier
