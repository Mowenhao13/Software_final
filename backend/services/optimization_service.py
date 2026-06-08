"""物流路径和成本优化服务"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.shipment import Shipment
from models.order import Order
from models.cost_record import CostRecord
from datetime import datetime, timedelta


def get_logistics_analysis(db: Session):
    """物流分析 — 时效、成本对比"""
    shipments = db.query(Shipment).all()

    if not shipments:
        return {"routes": [], "summary": {}}

    # 按运输方式统计
    mode_stats = {}
    for s in shipments:
        mode = s.transport_mode
        if mode not in mode_stats:
            mode_stats[mode] = {"count": 0, "total_cost": 0, "total_delay": 0, "on_time": 0}
        mode_stats[mode]["count"] += 1
        mode_stats[mode]["total_cost"] += s.cost or 0
        if s.arrival_time and s.actual_arrival:
            delay = (s.actual_arrival - s.arrival_time).total_seconds() / 3600
            mode_stats[mode]["total_delay"] += max(0, delay)
            if delay <= 0:
                mode_stats[mode]["on_time"] += 1

    mode_summary = {}
    for mode, stats in mode_stats.items():
        mode_summary[mode] = {
            "count": stats["count"],
            "avg_cost": round(stats["total_cost"] / stats["count"], 2),
            "on_time_rate": round(stats["on_time"] / stats["count"] * 100, 1) if stats["count"] > 0 else 0,
            "avg_delay_hours": round(stats["total_delay"] / stats["count"], 1),
        }

    # 路线分析
    routes = db.query(
        Shipment.origin, Shipment.destination, Shipment.transport_mode,
        func.count(Shipment.id).label("count"),
        func.avg(Shipment.cost).label("avg_cost")
    ).group_by(Shipment.origin, Shipment.destination, Shipment.transport_mode).limit(20).all()

    route_data = [
        {"origin": r.origin, "destination": r.destination, "mode": r.transport_mode,
         "count": r.count, "avg_cost": round(r.avg_cost or 0, 2)}
        for r in routes
    ]

    return {
        "routes": route_data,
        "summary": mode_summary
    }


def get_cost_analysis(db: Session):
    """成本分析 — 按类别和时间维度"""
    # 按类别汇总
    by_category = db.query(
        CostRecord.category, func.sum(CostRecord.amount).label("total")
    ).group_by(CostRecord.category).all()

    # 按月汇总趋势
    six_months_ago = datetime.now() - timedelta(days=180)
    by_month = db.query(
        func.strftime("%Y-%m", CostRecord.date).label("month"),
        func.sum(CostRecord.amount).label("total")
    ).filter(CostRecord.date >= six_months_ago).group_by("month").order_by("month").all()

    # 按部门汇总
    by_dept = db.query(
        CostRecord.department, func.sum(CostRecord.amount).label("total")
    ).group_by(CostRecord.department).all()

    total_cost = sum(item.total for item in by_category)

    return {
        "total_cost": round(total_cost, 2),
        "by_category": [{"category": c, "amount": round(a, 2),
                          "percentage": round(a / total_cost * 100, 1) if total_cost > 0 else 0}
                         for c, a in by_category],
        "by_month": [{"month": m, "amount": round(a, 2)} for m, a in by_month],
        "by_department": [{"department": d, "amount": round(a, 2)} for d, a in by_dept],
    }
