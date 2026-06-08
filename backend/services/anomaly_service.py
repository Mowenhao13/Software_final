"""异常检测服务 — 基于统计方法(Z-Score/IQR)检测异常"""
import numpy as np
from sqlalchemy.orm import Session
from models.order import Order
from models.inventory import Inventory
from models.shipment import Shipment
from models.product import Product
from datetime import datetime, timedelta


def detect_order_anomalies(db: Session):
    """检测订单量的异常"""
    # 获取每日订单量
    thirty_days_ago = datetime.now() - timedelta(days=30)
    orders = db.query(Order).filter(Order.order_date >= thirty_days_ago).all()

    daily_counts = {}
    for o in orders:
        day = o.order_date.strftime("%Y-%m-%d") if o.order_date else ""
        daily_counts[day] = daily_counts.get(day, 0) + 1

    if len(daily_counts) < 7:
        return []

    values = list(daily_counts.values())
    mean_val = np.mean(values)
    std_val = np.std(values)

    anomalies = []
    for day, count in daily_counts.items():
        if std_val > 0:
            z_score = (count - mean_val) / std_val
            if abs(z_score) > 2:
                anomalies.append({
                    "date": day,
                    "value": count,
                    "type": "订单量异常",
                    "severity": "high" if abs(z_score) > 2.5 else "medium",
                    "detail": f"{'偏高' if z_score > 0 else '偏低'}, Z-Score={z_score:.2f}"
                })

    return sorted(anomalies, key=lambda x: x["date"], reverse=True)


def detect_inventory_anomalies(db: Session):
    """检测库存异常 — 使用IQR方法"""
    inventories = db.query(Inventory).all()
    if len(inventories) < 5:
        return []

    quantities = [inv.quantity for inv in inventories]
    q1 = np.percentile(quantities, 25)
    q3 = np.percentile(quantities, 75)
    iqr = q3 - q1

    anomalies = []
    for inv in inventories:
        product = db.query(Product).filter(Product.id == inv.product_id).first()
        if inv.quantity < q1 - 1.5 * iqr:
            anomalies.append({
                "entity": product.name if product else f"产品{inv.product_id}",
                "warehouse": inv.warehouse,
                "quantity": inv.quantity,
                "type": "库存异常低",
                "severity": "high",
                "detail": f"库存{inv.quantity}远低于正常范围下限{q1 - 1.5 * iqr:.0f}"
            })
        elif inv.quantity > q3 + 1.5 * iqr:
            anomalies.append({
                "entity": product.name if product else f"产品{inv.product_id}",
                "warehouse": inv.warehouse,
                "quantity": inv.quantity,
                "type": "库存异常高",
                "severity": "low",
                "detail": f"库存{inv.quantity}远高于正常范围上限{q3 + 1.5 * iqr:.0f}，可能积压"
            })

    return anomalies


def detect_cost_anomalies(db: Session):
    """检测成本异常 — Z-Score方法"""
    from models.cost_record import CostRecord

    thirty_days_ago = datetime.now() - timedelta(days=30)
    records = db.query(CostRecord).filter(CostRecord.date >= thirty_days_ago).all()

    if not records:
        return []

    amounts = [r.amount for r in records]
    mean_val = np.mean(amounts)
    std_val = np.std(amounts)

    anomalies = []
    for r in records:
        if std_val > 0:
            z_score = (r.amount - mean_val) / std_val
            if z_score > 2:
                anomalies.append({
                    "date": r.date.strftime("%Y-%m-%d") if r.date else "",
                    "category": r.category,
                    "amount": r.amount,
                    "type": "成本异常偏高",
                    "severity": "high" if z_score > 2.5 else "medium",
                    "detail": f"成本{r.amount:.2f}, Z-Score={z_score:.2f}, {r.description or ''}"
                })

    return sorted(anomalies, key=lambda x: x["amount"], reverse=True)
