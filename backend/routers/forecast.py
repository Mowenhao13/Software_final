"""需求预测 API"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from services.forecast_service import get_available_items, predict_demand, batch_predict, get_available_models

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


class BatchRequest(BaseModel):
    item_ids: List[str]
    horizon: int = 12
    model: str = "auto"  # auto / chronos-2 / lag-llama / moirai


@router.get("/models")
def available_models():
    """返回可用模型列表"""
    return get_available_models()


@router.get("/items")
def available_items():
    """返回可预测的物品列表"""
    return get_available_items()


@router.get("/demand/{item_id}")
def demand_forecast(
    item_id: str,
    horizon: int = 12,
    model: str = Query("auto", description="auto/chronos-2/lag-llama/moirai"),
):
    """对指定物品做需求预测"""
    result = predict_demand(item_id, horizon, model)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/history/{item_id}")
def demand_history(item_id: str, weeks: int = 52):
    """返回物品的历史需求数据"""
    from services.forecast_service import _load_demand_data
    import numpy as np
    data = _load_demand_data()
    items = data.get("items", {})
    item = items.get(item_id)
    if not item:
        raise HTTPException(404, f"物品 {item_id} 未找到")
    d = np.array(item["weekly_demand"], dtype=np.float32)
    n = min(weeks, len(d))
    return {
        "item_id": item_id,
        "category": item.get("category", ""),
        "total_weeks": len(d),
        "history": [round(float(v), 2) for v in d[-n:]],
        "labels": [f"W{-n+i+1}" for i in range(n)],
    }


@router.post("/batch")
def batch_forecast(req: BatchRequest):
    """批量预测多个物品"""
    return batch_predict(req.item_ids, req.horizon, req.model)