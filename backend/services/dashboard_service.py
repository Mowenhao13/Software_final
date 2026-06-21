"""仪表盘服务 — 从 JSON 文件读取数据"""
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def get_kpis() -> Dict[str, Any]:
    """从 KPI 快照读取"""
    return _load_json("kpi_snapshot.json")


def get_trends() -> List[Dict[str, Any]]:
    """从趋势 JSON 读取"""
    data = _load_json("trends.json")
    return data.get("trends", [])


def get_supplier_distribution() -> List[Dict[str, Any]]:
    """供应商分布"""
    return [
        {"region": "华东", "count": 4},
        {"region": "华南", "count": 2},
        {"region": "华北", "count": 2},
        {"region": "西南", "count": 1},
        {"region": "西北", "count": 1},
    ]


def get_order_status() -> List[Dict[str, Any]]:
    """订单状态分布"""
    return [
        {"status": "pending", "count": 12},
        {"status": "confirmed", "count": 25},
        {"status": "shipping", "count": 18},
        {"status": "delivered", "count": 45},
        {"status": "cancelled", "count": 5},
    ]


def get_shipment_map() -> Dict[str, Any]:
    """读取供应链地图数据"""
    return _load_json("supply_chain_map.json")


def get_shipment_stats() -> Dict[str, Any]:
    """物流统计"""
    map_data = get_shipment_map()
    routes = map_data.get("routes", [])
    total = len(routes)
    in_transit = sum(1 for r in routes if r.get("status") == "in_transit")
    delayed = sum(1 for r in routes if r.get("status") == "delayed")
    delivered = sum(1 for r in routes if r.get("status") == "delivered")
    return {
        "total": total,
        "in_transit": in_transit,
        "delayed": delayed,
        "delivered": delivered,
        "on_time_rate": round((delivered - delayed) / delivered * 100, 1) if delivered > 0 else 95,
        "avg_cost": round(sum(r.get("cost", 0) or 0 for r in routes) / total, 2) if total > 0 else 0,
    }


def get_item_catalog() -> Dict[str, List[str]]:
    """读取物品-品类映射"""
    return _load_json("item_catalog.json")


def get_category_distribution() -> List[Dict[str, Any]]:
    """读取品类分布"""
    return _load_json("category_distribution.json")


def get_all_items_summary() -> List[Dict[str, Any]]:
    """所有物品的简要统计"""
    demand = _load_json("demand_weekly.json")
    items = demand.get("items", {})
    result = []
    for item_id, item in items.items():
        d = np.array(item.get("weekly_demand", []))
        total = float(np.sum(d))
        avg = float(np.mean(d))
        std = float(np.std(d))
        latest = float(d[-1]) if len(d) > 0 else 0
        result.append({
            "item_id": item_id,
            "category": item.get("category", "general"),
            "total_demand": round(total, 0),
            "avg_weekly": round(avg, 1),
            "std_weekly": round(std, 1),
            "latest_week": round(latest, 1),
        })
    return result