from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import AlertNotification
from ..schemas import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(AlertNotification).order_by(AlertNotification.id.desc()).all()

@router.post("/send-sms-simulation")
def trigger_sms_alert(phone: str = "+919876543210", message: str = "AgroSmart Alert: Soil moisture low in Field A"):
    return {
        "status": "sent",
        "provider": "Twilio / Gov SMS Gateway",
        "phone": phone,
        "message": message,
        "timestamp": "Now"
    }
