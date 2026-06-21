"""风险监控 API"""
from fastapi import APIRouter
from services.risk_monitor_service import (
    get_overview,
    get_supply_risks,
    get_demand_risks,
    get_logistics_risks,
    get_alerts,
)

router = APIRouter(prefix="/api/risk-monitor", tags=["Risk Monitor"])


@router.get("/overview")
def overview():
    """风险总览：各类风险数量 & 等级分布"""
    return get_overview()


@router.get("/supply-risks")
def supply_risks():
    """供给风险列表：需求激增/骤降的物品"""
    return {"risks": get_supply_risks()}


@router.get("/demand-risks")
def demand_risks():
    """需求风险列表：高波动/高不确定性的物品"""
    return {"risks": get_demand_risks()}


@router.get("/logistics-risks")
def logistics_risks():
    """物流风险列表：容量瓶颈边"""
    return {"risks": get_logistics_risks()}


@router.get("/alerts")
def alerts():
    """实时告警列表"""
    return {"alerts": get_alerts()}