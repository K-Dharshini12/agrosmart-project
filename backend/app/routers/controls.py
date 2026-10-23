from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import ActuatorValve, AutomationRule
from ..schemas import ValveResponse, ValveToggleRequest, AutomationRuleResponse, RuleToggleRequest

router = APIRouter(prefix="/api/controls", tags=["Smart Controls"])

@router.get("/valves", response_model=List[ValveResponse])
def get_valves(db: Session = Depends(get_db)):
    return db.query(ActuatorValve).all()

@router.post("/valves/{valve_id}/toggle", response_model=ValveResponse)
def toggle_valve(valve_id: int, payload: ValveToggleRequest, db: Session = Depends(get_db)):
    valve = db.query(ActuatorValve).filter(ActuatorValve.id == valve_id).first()
    if not valve:
        raise HTTPException(status_code=404, detail="Valve not found")
    valve.is_open = payload.is_open
    db.commit()
    db.refresh(valve)
    return valve

@router.get("/rules", response_model=List[AutomationRuleResponse])
def get_rules(db: Session = Depends(get_db)):
    return db.query(AutomationRule).all()

@router.post("/rules/{rule_id}/toggle", response_model=AutomationRuleResponse)
def toggle_rule(rule_id: int, payload: RuleToggleRequest, db: Session = Depends(get_db)):
    rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = payload.is_active
    db.commit()
    db.refresh(rule)
    return rule
