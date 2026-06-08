"""AI 预测 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.forecast_service import generate_forecast

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("/demand")
def get_demand_forecast(product_id: int = Query(None), db: Session = Depends(get_db)):
    """获取需求预测(未来30天)"""
    return generate_forecast(db, product_id)


@router.get("/sales")
def get_sales_forecast(db: Session = Depends(get_db)):
    """获取销售额预测"""
    return generate_forecast(db)
