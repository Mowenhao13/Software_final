"""供应商评分服务 — 多维度加权评估"""
from sqlalchemy.orm import Session
from models.supplier import Supplier
from models.order import Order
from sqlalchemy import func


# 评分维度权重
WEIGHTS = {
    "delivery_rate": 0.30,   # 准时交付率
    "quality_rate": 0.30,    # 质量合格率
    "cost_score": 0.25,      # 成本竞争力
    "response_time": 0.15,   # 响应速度
}


def calculate_supplier_score(db: Session, supplier_id: int):
    """计算供应商综合评分"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return None

    # 响应速度评分转换 (小时 → 0-100, 响应越快分越高)
    # 最佳响应时间4小时 → 100分, 最差48小时 → 0分
    rt = supplier.response_time or 24
    response_score = max(0, min(100, 100 - (rt - 4) * 100 / 44))

    dimensions = {
        "准时交付率": round(supplier.delivery_rate * 100, 1),
        "质量合格率": round(supplier.quality_rate * 100, 1),
        "成本竞争力": round(supplier.cost_score, 1),
        "响应速度": round(response_score, 1),
    }

    # 加权总分
    overall = (
        supplier.delivery_rate * 100 * WEIGHTS["delivery_rate"] +
        supplier.quality_rate * 100 * WEIGHTS["quality_rate"] +
        supplier.cost_score * WEIGHTS["cost_score"] +
        response_score * WEIGHTS["response_time"]
    )

    # 更新数据库中的评分
    supplier.score = round(overall, 1)
    db.commit()

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.name,
        "overall_score": round(overall, 1),
        "dimensions": dimensions
    }


def update_all_scores(db: Session):
    """更新全部供应商评分"""
    suppliers = db.query(Supplier).all()
    results = []
    for s in suppliers:
        score = calculate_supplier_score(db, s.id)
        if score:
            results.append(score)
    return results


def get_supplier_performance_ranking(db: Session):
    """供应商绩效排名"""
    suppliers = db.query(Supplier).filter(Supplier.status == "active").order_by(
        Supplier.score.desc()
    ).all()

    ranking = []
    for rank, s in enumerate(suppliers, 1):
        # 统计该供应商的订单
        total_orders = db.query(func.count(Order.id)).filter(Order.supplier_id == s.id).scalar() or 0
        delivered = db.query(func.count(Order.id)).filter(
            Order.supplier_id == s.id, Order.status == "delivered"
        ).scalar() or 0

        ranking.append({
            "rank": rank,
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "region": s.region,
            "score": s.score,
            "delivery_rate": round(s.delivery_rate * 100, 1),
            "quality_rate": round(s.quality_rate * 100, 1),
            "total_orders": total_orders,
            "delivered_orders": delivered,
            "status": s.status,
        })

    return ranking
