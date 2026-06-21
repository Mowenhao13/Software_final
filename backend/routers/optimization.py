"""物流路径优化 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.optimization_service import get_graph, find_routes, find_route_with_forecast

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])


class RouteRequest(BaseModel):
    start: str
    end: str
    demand_volume: float = 100
    top_k: int = 5
    forecast_weight: float = 1.0
    mode: Optional[str] = None  # road/rail/air, None=全部


class RouteWithForecastRequest(BaseModel):
    start: str
    end: str
    item_id: str
    top_k: int = 5
    horizon: int = 12
    mode: Optional[str] = None  # road/rail/air, None=全部


@router.get("/graph")
def graph():
    """返回图拓扑数据"""
    return get_graph()


@router.post("/route")
def route(req: RouteRequest):
    """给定起点/终点/需求量，返回 Top-K 最优路径"""
    result = find_routes(req.start, req.end, req.demand_volume, req.top_k, req.forecast_weight, req.mode)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/route/with-forecast")
def route_with_forecast(req: RouteWithForecastRequest):
    """结合 Chronos-2 需求预测做联动路径规划"""
    result = find_route_with_forecast(req.start, req.end, req.item_id, req.top_k, req.horizon, req.mode)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result