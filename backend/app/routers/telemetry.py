from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
from ..database import get_db
from ..models import SensorReading
from ..schemas import TelemetryCreate, TelemetryResponse
from ..services.automation_engine import evaluate_sensor_rules

router = APIRouter(prefix="/api/iot", tags=["IoT Telemetry"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

ws_manager = ConnectionManager()

@router.get("/latest", response_model=TelemetryResponse)
def get_latest_telemetry(db: Session = Depends(get_db)):
    reading = db.query(SensorReading).order_by(SensorReading.id.desc()).first()
    if not reading:
        reading = SensorReading(
            zone_id=1,
            soil_moisture=78.0,
            soil_temperature=24.0,
            soil_ph=6.8,
            water_tank_level=1250.0,
            connectivity_status="online",
            lora_rssi=-65
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
    return reading

@router.get("/history", response_model=List[TelemetryResponse])
def get_telemetry_history(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()

@router.post("/telemetry", response_model=TelemetryResponse)
async def post_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """
    IoT Ingestion endpoint for LoRaWAN gateways, ESP32, or MicroPython devices.
    """
    reading = SensorReading(
        zone_id=payload.zone_id,
        soil_moisture=payload.soil_moisture,
        soil_temperature=payload.soil_temperature,
        soil_ph=payload.soil_ph,
        water_tank_level=payload.water_tank_level,
        connectivity_status=payload.connectivity_status or "online",
        lora_rssi=payload.lora_rssi or -65
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Evaluate rules
    evaluate_sensor_rules(db, reading)

    # Broadcast to live WebSockets
    await ws_manager.broadcast({
        "event": "TELEMETRY_UPDATE",
        "data": {
            "soil_moisture": reading.soil_moisture,
            "soil_temperature": reading.soil_temperature,
            "soil_ph": reading.soil_ph,
            "water_tank_level": reading.water_tank_level,
            "connectivity_status": reading.connectivity_status,
            "lora_rssi": reading.lora_rssi
        }
    })

    return reading

@router.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
