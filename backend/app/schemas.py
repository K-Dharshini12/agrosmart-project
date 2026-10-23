from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Telemetry Schemas
class TelemetryCreate(BaseModel):
    zone_id: int = 1
    soil_moisture: float
    soil_temperature: float
    soil_ph: float
    water_tank_level: float
    connectivity_status: Optional[str] = "online"
    lora_rssi: Optional[int] = -65

class TelemetryResponse(BaseModel):
    id: int
    zone_id: int
    soil_moisture: float
    soil_temperature: float
    soil_ph: float
    water_tank_level: float
    connectivity_status: str
    lora_rssi: int
    recorded_at: datetime

    class Config:
        from_attributes = True

# Valve Actuation Schemas
class ValveToggleRequest(BaseModel):
    is_open: bool

class ValveResponse(BaseModel):
    id: int
    name: str
    zone_name: str
    is_open: bool
    flow_rate: str
    color: str

    class Config:
        from_attributes = True

# Automation Rule Schemas
class RuleToggleRequest(BaseModel):
    is_active: bool

class AutomationRuleResponse(BaseModel):
    id: int
    name: str
    description: str
    condition_metric: str
    threshold: Optional[float]
    operator: str
    action_type: str
    is_active: bool
    trigger_count: int

    class Config:
        from_attributes = True

# AI Assistant Schemas (Tamil, Thanglish, English)
class AIChatRequest(BaseModel):
    message: str
    language: str = "ta" # "ta" (Tamil/Thanglish) or "en" (English)
    api_key: Optional[str] = None
    provider: Optional[str] = None # "groq" or "gemini"
    context: Optional[dict] = None

class AIChatResponse(BaseModel):
    reply: str
    speech_text: Optional[str] = None
    language: str
    intent: str
    engine: Optional[str] = None
    audio_url: Optional[str] = None
    suggested_actions: Optional[List[str]] = None

class AIKeyConfigRequest(BaseModel):
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    ai_provider: Optional[str] = None

class AIKeyConfigResponse(BaseModel):
    has_groq: bool
    has_gemini: bool
    active_provider: str
    message: str

# Marketplace Schemas
class ProductCreate(BaseModel):
    name: str
    category: str = "vegetables"
    price: float
    unit: str = "per kg"
    stock: float
    image: str = "🌱"
    status: str = "active"

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    unit: str
    stock: float
    image: str
    status: str
    views: int
    rating: float
    orders: int

    class Config:
        from_attributes = True

class MandiPriceResponse(BaseModel):
    id: int
    product: str
    current_price: float
    change: float
    trend: str
    demand: str

    class Config:
        from_attributes = True

class NearbyBuyerResponse(BaseModel):
    id: int
    name: str
    location: str
    order_value: str
    rating: float
    buyer_type: str

    class Config:
        from_attributes = True

# Alerts
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    message: str
    time_label: str
    action: str

    class Config:
        from_attributes = True

# CCTV
class CctvConnectRequest(BaseModel):
    camera_name: Optional[str] = "Live CCTV #1"
    stream_url: Optional[str] = None
    source_type: Optional[str] = "webcam" # "webcam" or "ip_stream"

class CctvResponse(BaseModel):
    id: int
    camera_name: str
    stream_url: str
    is_live: bool
    growth_analysis: str
    pest_detection: str
    harvest_ready: str

    class Config:
        from_attributes = True
