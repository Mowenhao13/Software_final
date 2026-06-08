"""订单管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.order import Order
from models.product import Product
from models.supplier import Supplier
from schemas import OrderCreate
from datetime import datetime

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("/")
def list_orders(skip: int = 0, limit: int = 20, status: str = "", search: str = "",
                db: Session = Depends(get_db)):
    """订单列表(含关联信息)"""
    query = db.query(Order, Product.name.label("product_name"), Supplier.name.label("supplier_name")).join(
        Product, Order.product_id == Product.id
    ).join(Supplier, Order.supplier_id == Supplier.id)

    if status:
        query = query.filter(Order.status == status)
    if search:
        query = query.filter(Order.order_no.contains(search))

    total = query.count()
    results = query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()

    items = []
    for order, prod_name, sup_name in results:
        items.append({
            "id": order.id,
            "order_no": order.order_no,
            "product_id": order.product_id,
            "product_name": prod_name,
            "supplier_id": order.supplier_id,
            "supplier_name": sup_name,
            "quantity": order.quantity,
            "amount": order.amount,
            "status": order.status,
            "order_date": order.order_date.strftime("%Y-%m-%d") if order.order_date else None,
            "expected_delivery": order.expected_delivery.strftime("%Y-%m-%d") if order.expected_delivery else None,
            "actual_delivery": order.actual_delivery.strftime("%Y-%m-%d") if order.actual_delivery else None,
        })
    return {"total": total, "items": items}


@router.post("/")
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    order_count = db.query(func.count(Order.id)).scalar()
    order = Order(
        order_no=f"PO-{datetime.now().year}-{order_count + 1001:04d}",
        product_id=data.product_id,
        supplier_id=data.supplier_id,
        quantity=data.quantity,
        amount=data.amount,
        status=data.status,
        order_date=datetime.now(),
        expected_delivery=datetime.now().replace(hour=0) if data.status != "pending" else None,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/status")
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    order.status = status
    if status == "delivered":
        order.actual_delivery = datetime.now()
    db.commit()
    return {"message": "状态已更新"}
