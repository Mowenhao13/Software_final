"""产品管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.product import Product
from schemas import ProductCreate

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/")
def list_products(skip: int = 0, limit: int = 50, category: str = "", db: Session = Depends(get_db)):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return {"total": total, "items": products}


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """产品类别列表"""
    from sqlalchemy import func
    cats = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    return [{"category": c, "count": n} for c, n in cats if c]
