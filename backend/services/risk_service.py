"""风险分析服务 — 基于统计规则的风险识别"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.risk_alert import RiskAlert
from models.inventory import Inventory
from models.order import Order
from models.shipment import Shipment
from models.product import Product
from datetime import datetime, timedelta


def get_risk_summary(db: Session):
    """风险汇总统计"""
    total = db.query(RiskAlert).count()
    active = db.query(RiskAlert).filter(RiskAlert.status == "active").count()
    high_risk = db.query(RiskAlert).filter(RiskAlert.status == "active", RiskAlert.severity == "high").count()

    severity_dist = db.query(RiskAlert.severity, func.count(RiskAlert.id)).filter(
        RiskAlert.status == "active"
    ).group_by(RiskAlert.severity).all()

    alert_type_dist = db.query(RiskAlert.alert_type, func.count(RiskAlert.id)).filter(
        RiskAlert.status == "active"
    ).group_by(RiskAlert.alert_type).all()

    return {
        "total": total,
        "active": active,
        "high_risk": high_risk,
        "severity_distribution": {s: c for s, c in severity_dist},
        "type_distribution": {t: c for t, c in alert_type_dist},
    }


def get_risk_heatmap_data(db: Session):
    """风险热力图数据 — 按区域/类别统计风险"""
    data = []
    # 库存短缺风险
    low_stock = db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id).filter(
        Inventory.quantity < Inventory.safety_stock
    ).all()
    for inv, prod in low_stock:
        data.append({
            "entity": prod.name,
            "type": "inventory_shortage",
            "risk_level": "high" if inv.quantity < inv.safety_stock * 0.5 else "medium",
            "value": round((1 - inv.quantity / inv.safety_stock) * 100, 1) if inv.safety_stock > 0 else 100,
            "description": f"{prod.name}: 库存{inv.quantity}/{inv.safety_stock}"
        })

    # 延迟订单
    overdue = db.query(Order).filter(
        Order.status.in_(["shipping", "confirmed"]),
        Order.expected_delivery < datetime.now()
    ).all()
    for order in overdue:
        days_late = (datetime.now() - order.expected_delivery).days if order.expected_delivery else 0
        data.append({
            "entity": order.order_no,
            "type": "delivery_delay",
            "risk_level": "high" if days_late > 5 else "medium",
            "value": days_late,
            "description": f"订单{order.order_no}: 延迟{days_late}天"
        })

    # 延迟物流
    delayed_shipments = db.query(Shipment).filter(
        Shipment.status == "delayed"
    ).all()
    for ship in delayed_shipments:
        data.append({
            "entity": ship.tracking_no,
            "type": "logistics_delay",
            "risk_level": "medium",
            "value": 5,
            "description": f"运单{ship.tracking_no}: {ship.origin}→{ship.destination}延迟"
        })

    return data


def detect_new_risks(db: Session):
    """自动检测新风险并保存到数据库"""
    new_alerts = []

    # 检查库存不足
    low_stock = db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id).filter(
        Inventory.quantity < Inventory.safety_stock
    ).all()
    for inv, prod in low_stock:
        existing = db.query(RiskAlert).filter(
            RiskAlert.alert_type == "inventory_shortage",
            RiskAlert.related_entity_id == prod.id,
            RiskAlert.status == "active"
        ).first()
        if not existing:
            alert = RiskAlert(
                alert_type="inventory_shortage",
                severity="high" if inv.quantity < inv.safety_stock * 0.5 else "medium",
                title=f"{prod.name}库存不足",
                description=f"当前库存{inv.quantity}，安全库存{inv.safety_stock}",
                risk_score=round(1 - inv.quantity / (inv.safety_stock + 0.01), 2) if inv.safety_stock > 0 else 0.9,
                related_entity_type="product",
                related_entity_id=prod.id,
                suggested_action=f"建议立即采购{inv.safety_stock - inv.quantity + 100}件"
            )
            db.add(alert)
            new_alerts.append(alert)

    db.commit()
    return len(new_alerts)
