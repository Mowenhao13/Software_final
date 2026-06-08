"""风险管理 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.risk_alert import RiskAlert
from services.risk_service import get_risk_summary, get_risk_heatmap_data, detect_new_risks
from services.anomaly_service import detect_order_anomalies, detect_inventory_anomalies, detect_cost_anomalies

router = APIRouter(prefix="/api/risks", tags=["Risks"])


@router.get("/")
def list_risks(skip: int = 0, limit: int = 20, severity: str = "", status: str = "",
               db: Session = Depends(get_db)):
    """风险预警列表"""
    query = db.query(RiskAlert)
    if severity:
        query = query.filter(RiskAlert.severity == severity)
    if status:
        query = query.filter(RiskAlert.status == status)
    total = query.count()
    items = query.order_by(RiskAlert.risk_score.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """风险统计摘要"""
    return get_risk_summary(db)


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    """风险热力图数据"""
    return get_risk_heatmap_data(db)


@router.post("/detect")
def run_risk_detection(db: Session = Depends(get_db)):
    """运行风险检测"""
    new_count = detect_new_risks(db)
    return {"new_alerts": new_count, "message": f"检测完成，发现{new_count}条新预警"}


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    """获取全部异常"""
    order_anomalies = detect_order_anomalies(db)
    inventory_anomalies = detect_inventory_anomalies(db)
    cost_anomalies = detect_cost_anomalies(db)
    return {
        "order_anomalies": order_anomalies,
        "inventory_anomalies": inventory_anomalies,
        "cost_anomalies": cost_anomalies,
        "total": len(order_anomalies) + len(inventory_anomalies) + len(cost_anomalies),
    }


@router.put("/{alert_id}/status")
def update_alert_status(alert_id: int, status: str, db: Session = Depends(get_db)):
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(404, "预警不存在")
    alert.status = status
    if status == "resolved":
        from datetime import datetime
        alert.resolved_at = datetime.now()
    db.commit()
    return {"message": "状态已更新"}
