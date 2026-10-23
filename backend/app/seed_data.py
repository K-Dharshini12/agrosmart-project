from .database import engine, Base, SessionLocal
from .models import (
    Farmer, FieldZone, SensorReading, ActuatorValve,
    AutomationRule, MarketplaceProduct, MandiPrice,
    NearbyBuyer, AlertNotification, CctvMonitoring
)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(Farmer).first():
        db.close()
        return

    print("Seeding initial AgroSmart farm data...")

    # 1. Farmer Profile
    farmer = Farmer(
        name="Ramesh Kumar",
        phone="+91 98765 43210",
        language="ta",
        location="Field #1 - Jorethang Valley, Sikkim"
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    # 2. Field Zones
    zone1 = FieldZone(farmer_id=farmer.id, name="Tomato Field A", crop_type="Tomatoes", area_acres=1.5)
    zone2 = FieldZone(farmer_id=farmer.id, name="Vegetable Field B", crop_type="Mixed Vegetables", area_acres=2.0)
    db.add_all([zone1, zone2])
    db.commit()
    db.refresh(zone1)
    db.refresh(zone2)

    # 3. Initial Sensor Readings
    reading = SensorReading(
        zone_id=zone1.id,
        soil_moisture=78.0,
        soil_temperature=24.0,
        soil_ph=6.8,
        water_tank_level=1250.0,
        connectivity_status="online",
        lora_rssi=-65
    )
    db.add(reading)

    # 4. Actuator Valves
    valve1 = ActuatorValve(
        zone_id=zone1.id,
        name="Main Irrigation Valve",
        zone_name="Tomato Field A",
        is_open=True,
        flow_rate="15 L/min",
        color="text-blue-500"
    )
    valve2 = ActuatorValve(
        zone_id=zone2.id,
        name="Secondary Valve",
        zone_name="Vegetable Field B",
        is_open=False,
        flow_rate="8 L/min",
        color="text-green-500"
    )
    db.add_all([valve1, valve2])

    # 5. Automation Rules
    rule1 = AutomationRule(
        name="Soil Moisture Auto-Irrigation",
        description="Start irrigation when soil moisture < 60%",
        condition_metric="soil_moisture",
        threshold=60.0,
        operator="<",
        action_type="OPEN_VALVE",
        is_active=True,
        trigger_count=3
    )
    rule2 = AutomationRule(
        name="Weather-Based Control",
        description="Reduce irrigation before rain",
        condition_metric="weather_rain",
        operator="==",
        action_type="REDUCE_FLOW",
        is_active=True,
        trigger_count=1
    )
    rule3 = AutomationRule(
        name="Timer-Based Schedule",
        description="Daily irrigation at 6 AM and 6 PM",
        condition_metric="time_schedule",
        operator="==",
        action_type="SCHEDULED_CYCLE",
        is_active=False,
        trigger_count=12
    )
    db.add_all([rule1, rule2, rule3])

    # 6. Marketplace Products
    prod1 = MarketplaceProduct(
        farmer_id=farmer.id,
        name="Organic Tomatoes",
        category="vegetables",
        price=85.0,
        unit="per kg",
        stock=250.0,
        image="🍅",
        status="active",
        views=124,
        rating=4.8,
        orders=23
    )
    prod2 = MarketplaceProduct(
        farmer_id=farmer.id,
        name="Fresh Potatoes",
        category="vegetables",
        price=35.0,
        unit="per kg",
        stock=500.0,
        image="🥔",
        status="active",
        views=89,
        rating=4.6,
        orders=15
    )
    prod3 = MarketplaceProduct(
        farmer_id=farmer.id,
        name="Green Beans",
        category="vegetables",
        price=120.0,
        unit="per kg",
        stock=0.0,
        image="🫘",
        status="out_of_stock",
        views=45,
        rating=4.9,
        orders=8
    )
    db.add_all([prod1, prod2, prod3])

    # 7. Mandi Prices
    mandi_data = [
        MandiPrice(product="Tomatoes", current_price=85.0, change=12.0, trend="up", demand="high"),
        MandiPrice(product="Potatoes", current_price=35.0, change=-5.0, trend="down", demand="medium"),
        MandiPrice(product="Onions", current_price=45.0, change=8.0, trend="up", demand="high"),
        MandiPrice(product="Carrots", current_price=65.0, change=0.0, trend="stable", demand="medium"),
    ]
    db.add_all(mandi_data)

    # 8. Nearby Buyers
    buyers = [
        NearbyBuyer(name="Fresh Valley Store", location="Gangtok - 12 km", order_value="₹15,000", rating=4.7, buyer_type="retail"),
        NearbyBuyer(name="Organic Food Co.", location="Siliguri - 35 km", order_value="₹28,000", rating=4.9, buyer_type="wholesale"),
        NearbyBuyer(name="Local Restaurant Chain", location="Kalimpong - 25 km", order_value="₹8,500", rating=4.5, buyer_type="restaurant"),
    ]
    db.add_all(buyers)

    # 9. Alerts
    alerts = [
        AlertNotification(alert_type="warning", message="Water tank level below 30%", time_label="2 hours ago", action="Refill recommended"),
        AlertNotification(alert_type="success", message="Soil moisture optimal for tomatoes", time_label="4 hours ago", action="Continue current schedule"),
        AlertNotification(alert_type="info", message="Weather forecast: Rain expected tomorrow", time_label="6 hours ago", action="Reduce irrigation"),
    ]
    db.add_all(alerts)

    # 10. CCTV Monitoring
    cctv = CctvMonitoring(
        zone_id=zone1.id,
        camera_name="Tomato Field Section A",
        stream_url="/static/farm-cctv.jpg",
        is_live=True,
        growth_analysis="95% Healthy",
        pest_detection="None Detected",
        harvest_ready="5-7 days"
    )
    db.add(cctv)

    db.commit()
    db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    init_db()
