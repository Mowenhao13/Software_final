"""库存管理 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.inventory import Inventory
from models.product import Product

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/")
def list_inventory(warehouse: str = "", low_stock_only: bool = False, db: Session = Depends(get_db)):
    """库存列表(含产品信息)"""
    query = db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id)
    if warehouse:
        query = query.filter(Inventory.warehouse == warehouse)
    if low_stock_only:
        query = query.filter(Inventory.quantity < Inventory.safety_stock)

    results = query.all()
    items = []
    for inv, prod in results:
        items.append({
            "id": inv.id,
            "product_id": prod.id,
            "product_name": prod.name,
            "product_code": prod.code,
            "category": prod.category,
            "warehouse": inv.warehouse,
            "quantity": inv.quantity,
            "safety_stock": inv.safety_stock,
            "max_stock": inv.max_stock,
            "turnover_rate": inv.turnover_rate,
            "last_restock": inv.last_restock.strftime("%Y-%m-%d") if inv.last_restock else None,
            "status": "low" if inv.quantity < inv.safety_stock else (
                "excess" if inv.quantity > inv.max_stock else "normal"),
            "updated_at": inv.updated_at.strftime("%Y-%m-%d %H:%M") if inv.updated_at else None,
        })
    return {"total": len(items), "items": items}


@router.get("/summary")
def get_inventory_summary(db: Session = Depends(get_db)):
    """库存概览统计"""
    total_products = db.query(func.count(Inventory.id)).scalar() or 0
    low_stock = db.query(func.count(Inventory.id)).filter(
        Inventory.quantity < Inventory.safety_stock
    ).scalar() or 0
    excess_stock = db.query(func.count(Inventory.id)).filter(
        Inventory.quantity > Inventory.max_stock
    ).scalar() or 0
    total_value = db.query(func.sum(Inventory.quantity * Product.unit_price)).join(
        Product, Inventory.product_id == Product.id
    ).scalar() or 0

    avg_turnover = db.query(func.avg(Inventory.turnover_rate)).scalar() or 0

    return {
        "total_skus": total_products,
        "low_stock_count": low_stock,
        "excess_stock_count": excess_stock,
        "total_inventory_value": round(total_value, 2),
        "avg_turnover_rate": round(avg_turnover, 1),
        "low_stock_rate": round(low_stock / total_products * 100, 1) if total_products > 0 else 0,
    }


@router.get("/warehouses")
def get_warehouses(db: Session = Depends(get_db)):
    """仓库列表"""
    whs = db.query(Inventory.warehouse, func.count(Inventory.id)).group_by(Inventory.warehouse).all()
    return [{"warehouse": w, "sku_count": c} for w, c in whs if w]
