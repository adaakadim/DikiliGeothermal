import re

file_path = r'c:\Users\kadim\.gemini\antigravity-ide\scratch\DikiliGeothermal\digital_twin\plant_model\facility.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace import line to include Valve
content = content.replace(
    'from digital_twin.equipment.models import GeothermalWell, Pump, HeatExchanger, Pipeline, Separator, ReinjectionWell',
    'from digital_twin.equipment.models import GeothermalWell, Pump, HeatExchanger, Pipeline, Separator, ReinjectionWell, Valve'
)

# Add valves after PROD-PIPE
valve_1 = """        
        # 3.5 Production Valve
        self.equipment["V-101"] = Valve(id="V-101", name="Production Control Valve", type="VALVE")"""
        
content = content.replace(
    '        self.equipment["PROD-PIPE"] = Pipeline(id="PROD-PIPE", name="Main Production Line", type="PIPELINE")',
    '        self.equipment["PROD-PIPE"] = Pipeline(id="PROD-PIPE", name="Main Production Line", type="PIPELINE")\n' + valve_1
)

valve_2 = """        
        # 7.5 District Heating Valve
        self.equipment["V-201"] = Valve(id="V-201", name="DH Return Valve", type="VALVE")"""
        
content = content.replace(
    '        self.equipment["DH-NET"] = Pipeline(id="DH-NET", name="Distribution Network", type="NETWORK")',
    '        self.equipment["DH-NET"] = Pipeline(id="DH-NET", name="Distribution Network", type="NETWORK")\n' + valve_2
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added Valves to facility.py")
