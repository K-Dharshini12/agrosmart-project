from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import MarketplaceProduct, MandiPrice, NearbyBuyer
from ..schemas import ProductResponse, ProductCreate, MandiPriceResponse, NearbyBuyerResponse

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(MarketplaceProduct).all()

@router.post("/products", response_model=ProductResponse)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = MarketplaceProduct(
        farmer_id=1,
        name=payload.name,
        category=payload.category,
        price=payload.price,
        unit=payload.unit,
        stock=payload.stock,
        image=payload.image,
        status=payload.status,
        views=1,
        rating=5.0,
        orders=0
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/mandi-prices", response_model=List[MandiPriceResponse])
def get_mandi_prices(db: Session = Depends(get_db)):
    return db.query(MandiPrice).all()

@router.get("/buyers", response_model=List[NearbyBuyerResponse])
def get_nearby_buyers(db: Session = Depends(get_db)):
    return db.query(NearbyBuyer).all()

@router.get("/insights")
def get_market_insights():
    return {
        "tip": "Tomato prices are expected to rise 15% next week due to increased demand from restaurants. Consider harvesting early for better profits.",
        "top_demand": "Tomatoes & Onions",
        "predicted_trend": "Bullish for vegetables in next 10 days"
    }
