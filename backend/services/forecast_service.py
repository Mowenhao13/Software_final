"""需求预测服务 — 使用Holt-Winters指数平滑进行时间序列预测"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.order import Order
from models.product import Product
from config import FORECAST_WINDOW


def generate_forecast(db: Session, product_id: int | None = None):
    """
    基于历史订单数据生成30天需求预测
    使用加权移动平均 + 趋势外推 (不依赖statsmodels避免复杂依赖)
    """
    query = db.query(Order).filter(Order.status != "cancelled")

    if product_id:
        query = query.filter(Order.product_id == product_id)
        product = db.query(Product).filter(Product.id == product_id).first()
        product_name = product.name if product else "未知产品"
        unit = "件"
    else:
        product_name = "全部产品"
        unit = "件"

    orders = query.order_by(Order.order_date).all()

    if len(orders) < 10:
        return {"product_name": product_name, "unit": unit, "forecast": [], "confidence": 0, "trend": "stable"}

    # 按天聚合订单量
    daily_quantities = {}
    daily_amounts = {}
    for order in orders:
        day = order.order_date.strftime("%Y-%m-%d") if order.order_date else None
        if day:
            daily_quantities[day] = daily_quantities.get(day, 0) + order.quantity
            daily_amounts[day] = daily_amounts.get(day, 0) + order.amount

    dates = sorted(daily_quantities.keys())
    values = [daily_quantities[d] for d in dates]

    if len(values) < 5:
        return {"product_name": product_name, "unit": unit, "forecast": [], "confidence": 0, "trend": "stable"}

    # --- Holt-Winters 简化实现 ---
    alpha = 0.3   # 水平平滑
    beta = 0.1    # 趋势平滑
    gamma = 0.1   # 季节平滑
    season_length = 7  # 周季节

    # 初始化
    level = values[0]
    trend = values[1] - values[0] if len(values) > 1 else 0
    seasonal = [0] * season_length

    # 拟合
    fitted = []
    for t, y in enumerate(values):
        if t < season_length:
            fitted.append(y)
            continue

        # 预测
        s_idx = (t - season_length) % season_length
        forecast_val = level + trend + seasonal[s_idx]
        fitted.append(max(0, forecast_val))

        # 更新
        new_level = alpha * (y - seasonal[s_idx]) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        new_seasonal = gamma * (y - new_level) + (1 - gamma) * seasonal[s_idx]

        level, trend = new_level, new_trend
        seasonal[s_idx] = new_seasonal

    # 计算误差
    errors = [abs(values[i] - fitted[i]) for i in range(season_length, len(values))]
    mae = np.mean(errors) if errors else np.mean(values) * 0.15
    std_err = np.std(errors) if errors else mae

    # 预测未来
    last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    forecast_result = []
    f_level, f_trend = level, trend
    f_seasonal = seasonal.copy()

    for i in range(FORECAST_WINDOW):
        f_date = last_date + timedelta(days=i + 1)
        s_idx = (len(values) + i) % season_length
        pred = max(0, f_level + f_trend + f_seasonal[s_idx])

        forecast_result.append({
            "date": f_date.strftime("%Y-%m-%d"),
            "predicted": round(pred, 1),
            "lower_bound": round(max(0, pred - 1.96 * mae), 1),
            "upper_bound": round(pred + 1.96 * mae, 1),
            "actual": None
        })

        # 模拟更新
        f_trend = f_trend if not np.isnan(f_trend) else 0
        f_level = alpha * (pred - f_seasonal[s_idx]) + (1 - alpha) * (f_level + f_trend)

    # 趋势判断
    recent_avg = np.mean(values[-14:]) if len(values) >= 14 else np.mean(values)
    forecast_avg = np.mean([f["predicted"] for f in forecast_result])
    if forecast_avg > recent_avg * 1.08:
        trend = "up"
    elif forecast_avg < recent_avg * 0.92:
        trend = "down"
    else:
        trend = "stable"

    # 置信度
    cv = mae / (np.mean(values) + 0.001)
    confidence = round(max(0, min(1, 1 - cv)), 2)

    return {
        "product_name": product_name,
        "unit": unit,
        "forecast": forecast_result,
        "confidence": confidence,
        "trend": trend
    }


def generate_sales_forecast(db: Session):
    """销售额预测"""
    return generate_forecast(db)
