"""
digital_twin/plant_model/facility.py
====================================
The central Digital Twin facility model. Aggregates all equipment and synchronizes state.
"""

from typing import Dict, Any
from digital_twin.equipment.models import GeothermalWell, Pump, HeatExchanger, Pipeline, Equipment

class DikiliFacility:
    def __init__(self):
        self.equipment: Dict[str, Equipment] = {}
        self._initialize_plant()

    def _initialize_plant(self):
        from digital_twin.equipment.models import GeothermalWell, Pump, HeatExchanger, Pipeline, Separator, ReinjectionWell, Valve
        
        # 1. Production Well
        self.equipment["GW-01"] = GeothermalWell(id="GW-01", name="Production Well 1", type="WELL")
        
        # 2. Production Pump
        self.equipment["P-101"] = Pump(id="P-101", name="Production Pump", type="PUMP")
        
        # 3. Production Pipeline
        self.equipment["PROD-PIPE"] = Pipeline(id="PROD-PIPE", name="Main Production Line", type="PIPELINE")
        
        # 3.5 Production Valve
        self.equipment["V-101"] = Valve(id="V-101", name="Production Control Valve", type="VALVE")
        
        # 4. Separator
        self.equipment["SEP-01"] = Separator(id="SEP-01", name="Brine Separator", type="SEPARATOR")
        
        # 5. Heat Exchanger
        self.equipment["HX-101"] = HeatExchanger(id="HX-101", name="Primary Heat Exchanger", type="HX")
        
        # 6. District Heating Pump
        self.equipment["P-201"] = Pump(id="P-201", name="DH Circulation Pump", type="PUMP")
        
        # 7. Distribution Network
        self.equipment["DH-NET"] = Pipeline(id="DH-NET", name="Distribution Network", type="NETWORK")
        
        # 7.5 District Heating Valve
        self.equipment["V-201"] = Valve(id="V-201", name="DH Return Valve", type="VALVE")
        
        # 8. Return Line
        self.equipment["RET-PIPE"] = Pipeline(id="RET-PIPE", name="Return Pipeline", type="PIPELINE")
        
        # 9. Reinjection Pump
        self.equipment["P-301"] = Pump(id="P-301", name="Reinjection Pump", type="PUMP")
        
        # 10. Reinjection Well
        self.equipment["RW-01"] = ReinjectionWell(id="RW-01", name="Reinjection Well 1", type="WELL")

    def update_from_scada(self, scada_data: Dict[str, Any]):
        """Update sensor values from live SCADA arrays."""
        for eq_id, eq_obj in self.equipment.items():
            if eq_id in scada_data:
                for k, v in scada_data[eq_id].items():
                    eq_obj.update_sensor(k, v)

    def update_from_ai(self, ai_data: Dict[str, Any]):
        """Update AI metrics for equipment."""
        for eq_id, eq_obj in self.equipment.items():
            if eq_id in ai_data:
                data = ai_data[eq_id]
                eq_obj.update_ai(
                    health=data.get("health", 100.0),
                    risk=data.get("risk", 0.0),
                    conf=data.get("conf", 0.0),
                    rec=data.get("recommendation", "Continue Monitoring"),
                    pos=data.get("pos_factors", []),
                    neg=data.get("neg_factors", []),
                    expl=data.get("explanation_text", "")
                )
                if "rul_hours" in data:
                    eq_obj.update_rul(
                        hours=data["rul_hours"],
                        days=data.get("estimated_days", 0.0),
                        conf=data.get("rul_conf", 0.0),
                        deg_rate=data.get("degradation_rate", 0.0),
                        trend=data.get("rul_trend", "Unknown"),
                        priority=data.get("maintenance_priority", "Unknown")
                    )
                
    def update_from_optimization(self, opt_data: Dict[str, Any]):
        """Update optimization recommendations for equipment."""
        for eq_id, eq_obj in self.equipment.items():
            if eq_id in opt_data:
                data = opt_data[eq_id]
                eq_obj.update_optimization(
                    eff=data.get("efficiency", 0.0),
                    target=data.get("target_efficiency", 0.0),
                    sugg=data.get("suggestion", ""),
                    est_imp=data.get("estimated_improvement", "")
                )

    def update_from_anomaly(self, anomaly_data: Dict[str, Any]):
        """Update anomaly detection data for affected equipment."""
        affected_str = anomaly_data.get("Affected Equipment", "")
        score = anomaly_data.get("Anomaly Score", 0.0)
        status = anomaly_data.get("Status", "Normal")
        root_cause = anomaly_data.get("Root Cause", {}).get("primary", "None")
        recommendation = anomaly_data.get("Recommendation", "")
        
        # Apply to specifically affected equipment
        if affected_str and affected_str != "None":
            affected_ids = [eid.strip() for eid in affected_str.split(",")]
            for eq_id in affected_ids:
                if eq_id in self.equipment:
                    self.equipment[eq_id].update_anomaly(score, status, root_cause, recommendation)
        
        # Apply a reduced score to all equipment for general awareness
        for eq_id, eq_obj in self.equipment.items():
            if eq_obj.anomaly_score == 0.0:
                eq_obj.update_anomaly(score * 0.3, "Normal" if score < 25 else status, root_cause, "")
                
    def update_from_kpi(self, kpi_data: Dict[str, Any]):
        """Update facility-level operational intelligence KPIs."""
        # For Phase 5.5.4, we store global KPI data in the facility object itself
        # so it can be queried by other modules or summary views.
        self.kpi_data = kpi_data

    def update_from_decision(self, decision_data: Dict[str, Any]):
        """Update unified decision support assessments for equipment."""
        for eq_id, eq_obj in self.equipment.items():
            if eq_id in decision_data:
                eq_obj.update_decision_support(decision_data[eq_id])

    def evaluate_all(self):
        """Trigger evaluate_status on all equipment to compute colors/alarms."""
        for eq_obj in self.equipment.values():
            eq_obj.evaluate_status()

    def get_equipment(self, eq_id: str) -> Equipment | None:
        return self.equipment.get(eq_id)
