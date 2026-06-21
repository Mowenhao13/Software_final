"""供应链全景 API"""
from fastapi import APIRouter
from services.dashboard_service import get_shipment_map, get_shipment_stats

router = APIRouter(prefix="/api/supply-chain", tags=["SupplyChain"])


@router.get("/map")
def shipment_map():
    """获取物流路线地图数据"""
    return get_shipment_map()


@router.get("/stats")
def shipment_stats():
    """获取物流统计"""
    return get_shipment_stats()