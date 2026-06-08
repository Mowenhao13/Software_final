"""物流管理 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.shipment import Shipment
from models.order import Order
from models.product import Product

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])


@router.get("/")
def list_shipments(skip: int = 0, limit: int = 20, status: str = "", db: Session = Depends(get_db)):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.status == status)
    total = query.count()
    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": shipments}


@router.get("/map")
def get_shipment_map_data(db: Session = Depends(get_db)):
    """获取物流地图数据(路线+位置)"""
    shipments = db.query(Shipment).filter(Shipment.status.in_(["in_transit", "delayed"])).all()

    routes = []
    points = []
    for s in shipments:
        if s.origin_lng and s.origin_lat and s.dest_lng and s.dest_lat:
            routes.append({
                "tracking_no": s.tracking_no,
                "origin": s.origin,
                "destination": s.destination,
                "origin_coords": [s.origin_lng, s.origin_lat],
                "dest_coords": [s.dest_lng, s.dest_lat],
                "current_coords": [s.current_lng, s.current_lat] if s.current_lng else None,
                "status": s.status,
                "carrier": s.carrier,
                "mode": s.transport_mode,
            })
            if s.current_lng and s.current_lat:
                points.append({
                    "name": s.tracking_no,
                    "value": [s.current_lng, s.current_lat],
                    "status": s.status,
                })

    return {"routes": routes, "points": points, "total_in_transit": len(shipments)}


@router.get("/stats")
def get_shipment_stats(db: Session = Depends(get_db)):
    """物流统计"""
    from sqlalchemy import func
    total = db.query(func.count(Shipment.id)).scalar() or 0
    in_transit = db.query(func.count(Shipment.id)).filter(Shipment.status == "in_transit").scalar() or 0
    delayed = db.query(func.count(Shipment.id)).filter(Shipment.status == "delayed").scalar() or 0
    delivered = db.query(func.count(Shipment.id)).filter(Shipment.status == "delivered").scalar() or 0
    avg_cost = db.query(func.avg(Shipment.cost)).scalar() or 0

    return {
        "total": total,
        "in_transit": in_transit,
        "delayed": delayed,
        "delivered": delivered,
        "on_time_rate": round((delivered - delayed) / delivered * 100, 1) if delivered > 0 else 95,
        "avg_cost": round(avg_cost, 2),
    }
