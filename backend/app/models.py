import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="Ramesh Kumar")
    phone = Column(String(20), default="+91 98765 43210")
    language = Column(String(10), default="ta")  # ta (Tamil), en (English), ne (Nepali)
    location = Column(String(100), default="Field #1 - Jorethang Valley, Sikkim")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    fields = relationship("FieldZone", back_populates="farmer")
    products = relationship("MarketplaceProduct", back_populates="farmer")

class FieldZone(Base):
    __tablename__ = "field_zones"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    name = Column(String(100))  # e.g. "Tomato Field A", "Vegetable Field B"
    crop_type = Column(String(50))
    area_acres = Column(Float, default=2.5)

    farmer = relationship("Farmer", back_populates="fields")
    readings = relationship("SensorReading", back_populates="zone")
    valves = relationship("ActuatorValve", back_populates="zone")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("field_zones.id"))
    soil_moisture = Column(Float)       # e.g. 78.0 %
    soil_temperature = Column(Float)    # e.g. 24.0 °C
    soil_ph = Column(Float)             # e.g. 6.8 pH
    water_tank_level = Column(Float)    # e.g. 1250 L
    connectivity_status = Column(String(20), default="online")
    lora_rssi = Column(Integer, default=-65) # dBm
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    zone = relationship("FieldZone", back_populates="readings")

class ActuatorValve(Base):
    __tablename__ = "actuator_valves"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("field_zones.id"))
    name = Column(String(100))          # e.g. "Main Irrigation Valve"
    zone_name = Column(String(100))     # e.g. "Tomato Field A"
    is_open = Column(Boolean, default=True)
    flow_rate = Column(String(20), default="15 L/min")
    color = Column(String(30), default="text-blue-500")
    last_toggled = Column(DateTime, default=datetime.datetime.utcnow)

    zone = relationship("FieldZone", back_populates="valves")

class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))          # e.g. "Soil Moisture Auto-Irrigation"
    description = Column(String(255))   # e.g. "Start irrigation when soil moisture < 60%"
    condition_metric = Column(String(50)) # "soil_moisture", "weather_rain", "time_schedule"
    threshold = Column(Float, nullable=True)
    operator = Column(String(10), default="<")
    action_type = Column(String(50))    # "OPEN_VALVE", "CLOSE_VALVE", "REDUCE_FLOW"
    is_active = Column(Boolean, default=True)
    trigger_count = Column(Integer, default=0)

class MarketplaceProduct(Base):
    __tablename__ = "marketplace_products"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    name = Column(String(100))          # e.g. "Organic Tomatoes"
    category = Column(String(50), default="vegetables")
    price = Column(Float)               # e.g. 85.0
    unit = Column(String(20), default="per kg")
    stock = Column(Float)               # e.g. 250.0 kg
    image = Column(String(20), default="🍅")
    status = Column(String(20), default="active") # "active", "out_of_stock"
    views = Column(Integer, default=124)
    rating = Column(Float, default=4.8)
    orders = Column(Integer, default=23)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    farmer = relationship("Farmer", back_populates="products")

class MandiPrice(Base):
    __tablename__ = "mandi_prices"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(100))       # e.g. "Tomatoes"
    current_price = Column(Float)       # e.g. 85.0
    change = Column(Float)              # e.g. 12.0
    trend = Column(String(20), default="up") # "up", "down", "stable"
    demand = Column(String(20), default="high") # "high", "medium", "low"
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class NearbyBuyer(Base):
    __tablename__ = "nearby_buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))          # e.g. "Fresh Valley Store"
    location = Column(String(100))      # e.g. "Gangtok - 12 km"
    order_value = Column(String(50))    # e.g. "₹15,000"
    rating = Column(Float, default=4.7)
    buyer_type = Column(String(30), default="retail") # "retail", "wholesale", "restaurant"
    phone = Column(String(20), default="+91 98111 22233")

class AlertNotification(Base):
    __tablename__ = "alert_notifications"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(20))     # "warning", "success", "info"
    message = Column(String(255))
    time_label = Column(String(50))     # "2 hours ago"
    action = Column(String(150))        # "Refill recommended"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

class CctvMonitoring(Base):
    __tablename__ = "cctv_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("field_zones.id"))
    camera_name = Column(String(100), default="CCTV Feed #1 - Field A")
    stream_url = Column(String(255), default="/static/cctv_feed.jpg")
    is_live = Column(Boolean, default=True)
    growth_analysis = Column(String(50), default="95% Healthy")
    pest_detection = Column(String(50), default="None Detected")
    harvest_ready = Column(String(50), default="5-7 days")
    last_analyzed = Column(DateTime, default=datetime.datetime.utcnow)
