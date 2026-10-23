from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CctvMonitoring
from ..schemas import CctvResponse, CctvConnectRequest

router = APIRouter(prefix="/api/cctv", tags=["CCTV Computer Vision"])

@router.get("/status", response_model=CctvResponse)
def get_cctv_status(db: Session = Depends(get_db)):
    cctv = db.query(CctvMonitoring).first()
    if not cctv:
        cctv = CctvMonitoring(
            zone_id=1,
            camera_name="No CCTV Connected",
            stream_url="",
            is_live=False,
            growth_analysis="No Signal",
            pest_detection="Disconnected",
            harvest_ready="Offline"
        )
        db.add(cctv)
        db.commit()
        db.refresh(cctv)
    return cctv

@router.post("/connect", response_model=CctvResponse)
def connect_cctv(payload: CctvConnectRequest, db: Session = Depends(get_db)):
    cctv = db.query(CctvMonitoring).first()
    if not cctv:
        cctv = CctvMonitoring(zone_id=1)
        db.add(cctv)
    
    cctv.camera_name = payload.camera_name or "Real Farm CCTV #1"
    cctv.stream_url = payload.stream_url or "device_camera_stream"
    cctv.is_live = True
    cctv.growth_analysis = "96% Healthy"
    cctv.pest_detection = "None Detected"
    cctv.harvest_ready = "5-7 days"
    db.commit()
    db.refresh(cctv)
    return cctv

@router.post("/disconnect", response_model=CctvResponse)
def disconnect_cctv(db: Session = Depends(get_db)):
    cctv = db.query(CctvMonitoring).first()
    if cctv:
        cctv.is_live = False
        cctv.camera_name = "No CCTV Connected"
        cctv.stream_url = ""
        cctv.growth_analysis = "No Signal"
        cctv.pest_detection = "Disconnected"
        cctv.harvest_ready = "Offline"
        db.commit()
        db.refresh(cctv)
    return cctv

@router.post("/analyze")
def trigger_cctv_analysis(camera_id: int = 1):
    """
    Simulates / triggers YOLOv8 or ResNet model inference on camera stream frame.
    """
    return {
        "status": "success",
        "camera_id": camera_id,
        "inference": {
            "crop": "Tomato (Solanum lycopersicum)",
            "health_score": 0.96,
            "detected_pests": [],
            "leaf_chlorosis": "Normal",
            "fruiting_stage": "Early ripening (color break)",
            "estimated_harvest_window_days": "5-7 days"
        }
    }
