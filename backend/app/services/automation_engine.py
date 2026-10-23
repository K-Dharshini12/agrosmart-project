from sqlalchemy.orm import Session
from ..models import AutomationRule, ActuatorValve, AlertNotification, SensorReading

def evaluate_sensor_rules(db: Session, reading: SensorReading):
    """
    Evaluates active automation rules against live incoming sensor readings.
    """
    rules = db.query(AutomationRule).filter(AutomationRule.is_active == True).all()
    triggered_alerts = []

    for rule in rules:
        if rule.condition_metric == "soil_moisture":
            if rule.operator == "<" and reading.soil_moisture < rule.threshold:
                # Rule triggered! Open main valve
                valves = db.query(ActuatorValve).filter(ActuatorValve.zone_id == reading.zone_id).all()
                for v in valves:
                    v.is_open = True
                rule.trigger_count += 1
                
                alert = AlertNotification(
                    alert_type="warning",
                    message=f"Auto-Irrigation triggered: Soil moisture dropped to {reading.soil_moisture}% (Threshold: {rule.threshold}%)",
                    time_label="Just now",
                    action="Main Irrigation Valve opened automatically"
                )
                db.add(alert)
                triggered_alerts.append(alert.message)

        elif rule.condition_metric == "water_tank":
            if rule.operator == "<" and reading.water_tank_level < rule.threshold:
                alert = AlertNotification(
                    alert_type="warning",
                    message=f"Water tank level critical: {reading.water_tank_level}L remaining",
                    time_label="Just now",
                    action="Refill water storage pump immediately"
                )
                db.add(alert)
                triggered_alerts.append(alert.message)

    db.commit()
    return triggered_alerts
