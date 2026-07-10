import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\equipment\models.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add Valve class at the end
valve_class = """
@dataclass
class Valve(Equipment):
    def evaluate_status(self):
        # A valve might have Position sensor (0-100%)
        pos = self.sensors.get("Position", 0)
        if pos >= 95:
            self.status = "FULLY OPEN"
        elif pos <= 5:
            self.status = "CLOSED"
        else:
            self.status = "PARTIALLY OPEN"
        
        # Override if alarms or high risk exist
        if self.alarms:
            self.status = "CRITICAL"
        elif self.failure_risk > 60:
            self.status = "CRITICAL"
        elif self.failure_risk > 35:
            self.status = "WARNING"
"""
content += valve_class

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added Valve class to models.py")
