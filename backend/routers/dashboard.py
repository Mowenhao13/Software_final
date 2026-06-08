"""仪表盘 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Supplier, Product, Inventory, Order, Shipment, RiskAlert, CostRecord
from schemas import KPIData, TrendItem
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KPIData)
def get_kpis(db: Session = Depends(get_db)):
    """获取仪表盘核心KPI"""
    now = datetime.now()
    month_ago = now - timedelta(days=30)
    prev_month_ago = month_ago - timedelta(days=30)

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_amount = db.query(func.sum(Order.amount)).filter(Order.status != "cancelled").scalar() or 0
    active_suppliers = db.query(func.count(Supplier.id)).filter(Supplier.status == "active").scalar() or 0
    risk_count = db.query(func.count(RiskAlert.id)).filter(RiskAlert.status == "active").scalar() or 0

    # 准时交付率
    delivered = db.query(func.count(Order.id)).filter(Order.status == "delivered").scalar() or 0
    on_time = db.query(func.count(Order.id)).filter(
        Order.status == "delivered",
        Order.actual_delivery <= Order.expected_delivery
    ).scalar() or 0
    on_time_rate = round(on_time / delivered * 100, 1) if delivered > 0 else 95.0

    # 库存周转率 (平均)
    avg_turnover = db.query(func.avg(Inventory.turnover_rate)).scalar() or 3.5
    inventory_turnover = round(avg_turnover, 1)

    # 总成本
    cost_total = db.query(func.sum(CostRecord.amount)).scalar() or 0

    # 本月订单金额 vs 上月
    this_month_amount = db.query(func.sum(Order.amount)).filter(
        Order.order_date >= month_ago, Order.status != "cancelled"
    ).scalar() or 0
    prev_month_amount = db.query(func.sum(Order.amount)).filter(
        Order.order_date >= prev_month_ago, Order.order_date < month_ago,
        Order.status != "cancelled"
    ).scalar() or 1
    month_growth = round((this_month_amount - prev_month_amount) / prev_month_amount * 100, 1)

    return {
        "total_orders": total_orders,
        "total_amount": round(total_amount, 2),
        "on_time_delivery_rate": on_time_rate,
        "inventory_turnover": inventory_turnover,
        "active_suppliers": active_suppliers,
        "risk_count": risk_count,
        "cost_total": round(cost_total, 2),
        "month_growth": month_growth,
    }


@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    """获取近30天趋势数据"""
    days = []
    today = datetime.now()
    for i in range(30):
        d = today - timedelta(days=29 - i)
        day_start = d.replace(hour=0, minute=0, second=0)
        day_end = d.replace(hour=23, minute=59, second=59)

        orders_count = db.query(func.count(Order.id)).filter(
            Order.order_date >= day_start, Order.order_date <= day_end
        ).scalar() or 0

        amount = db.query(func.sum(Order.amount)).filter(
            Order.order_date >= day_start, Order.order_date <= day_end,
            Order.status != "cancelled"
        ).scalar() or 0

        cost = db.query(func.sum(CostRecord.amount)).filter(
            CostRecord.date >= day_start, CostRecord.date <= day_end
        ).scalar() or 0

        days.append({
            "date": d.strftime("%Y-%m-%d"),
            "orders": orders_count,
            "amount": round(amount, 2),
            "cost": round(cost, 2),
        })

    return {"trends": days}


@router.get("/supplier-distribution")
def get_supplier_distribution(db: Session = Depends(get_db)):
    """供应商地区分布"""
    regions = db.query(Supplier.region, func.count(Supplier.id)).group_by(Supplier.region).all()
    return [{"region": r, "count": c} for r, c in regions]


@router.get("/order-status")
def get_order_status_distribution(db: Session = Depends(get_db)):
    """订单状态分布"""
    statuses = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    return [{"status": s, "count": c} for s, c in statuses]
