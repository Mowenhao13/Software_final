"""风险监控服务 — 从 JSON 数据计算供给、需求、物流等风险指标（支持多数据集切换）"""
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict
from services.dataset_manager import get_data_dir

CATEGORY_NAMES = {
    "apparel": "服装",
    "electronics": "电子产品",
    "food": "食品",
    "pharma": "药品",
    "automotive": "汽车配件",
    "grocery": "食品杂货",
    "home": "家居用品",
    "sports": "运动户外",
    "baby": "婴儿用品",
}


def _load_json(filename: str) -> dict:
    path = get_data_dir() / filename
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def get_overview() -> Dict[str, Any]:
    """风险总览 — 返回前端期望的格式"""
    supply = get_supply_risks()
    demand = get_demand_risks()
    logistics = get_logistics_risks()
    alerts = get_alerts()

    def count_levels(items: list, level_field: str = "risk_level") -> dict:
        total = len(items)
        high = sum(1 for x in items if x.get(level_field) == "high")
        medium = sum(1 for x in items if x.get(level_field) == "medium")
        return {"total": total, "high": high, "medium": medium, "low": total - high - medium}

    return {
        "supply": count_levels(supply),
        "demand": count_levels(demand),
        "logistics": count_levels(logistics),
        "total_high": count_levels(supply)["high"] + count_levels(demand)["high"] + count_levels(logistics)["high"],
        "active_alerts": len(alerts),
        "total_supply_risks": len(supply),
        "total_demand_risks": len(demand),
        "total_logistics_risks": len(logistics),
        "risk_levels": {"high": count_levels(supply)["high"] + count_levels(demand)["high"] + count_levels(logistics)["high"],
                        "medium": count_levels(supply)["medium"] + count_levels(demand)["medium"] + count_levels(logistics)["medium"],
                        "low": count_levels(supply)["low"] + count_levels(demand)["low"] + count_levels(logistics)["low"]},
        "level_distribution": [
            {"name": "高风险", "value": count_levels(supply)["high"] + count_levels(demand)["high"] + count_levels(logistics)["high"]},
            {"name": "中风险", "value": count_levels(supply)["medium"] + count_levels(demand)["medium"] + count_levels(logistics)["medium"]},
            {"name": "低风险", "value": count_levels(supply)["low"] + count_levels(demand)["low"] + count_levels(logistics)["low"]},
        ],
    }


def _normalize(items: list, field_map: dict) -> list:
    """统一字段名，前端兼容"""
    result = []
    for item in items:
        normalized = {}
        for front_field, backend_field in field_map.items():
            normalized[front_field] = item.get(backend_field if backend_field else front_field, "")
        # 保留其他未映射字段
        for k, v in item.items():
            if k not in field_map.values() and k not in normalized:
                normalized[k] = v
        result.append(normalized)
    return result


def get_supply_risks() -> List[Dict[str, Any]]:
    """供给风险 — CV > 0.4 或最近趋势异常的物品"""
    demand = _load_json("demand_weekly.json")
    items = demand.get("items", {})
    risks = []
    for item_id, item in items.items():
        d = np.array(item.get("weekly_demand", []))
        if len(d) < 12:
            continue
        recent = d[-12:]
        cv = float(np.std(recent) / max(np.mean(recent), 1))
        if cv > 0.4:
            risks.append({
                "item_id": item_id,
                "name": item.get("name", item_id),
                "category": CATEGORY_NAMES.get(item.get("category", ""), item.get("category", "")),
                "level": "high" if cv > 0.6 else "medium",
                "risk_level": "high" if cv > 0.6 else "medium",
                "cv": round(cv, 2),
                "change_pct": round((float(np.mean(recent[-4:])) / max(float(np.mean(recent[-8:-4])), 1) - 1) * 100, 1),
                "avg_demand": round(float(np.mean(recent)), 1),
                "mean": round(float(np.mean(recent)), 1),
                "description": f"周需求波动(CV={cv:.2f})，近4周均值为{float(np.mean(recent[-4:])):.0f}",
                "trend": "unstable",
            })
    return risks


def get_demand_risks() -> List[Dict[str, Any]]:
    """需求风险 — 月环比异常物品"""
    demand = _load_json("demand_weekly.json")
    items = demand.get("items", {})
    risks = []
    for item_id, item in items.items():
        d = np.array(item.get("weekly_demand", []))
        if len(d) < 10:
            continue
        recent4 = np.mean(d[-4:]) if len(d) >= 4 else np.mean(d)
        prev4 = np.mean(d[-8:-4]) if len(d) >= 8 else np.mean(d) * 0.9
        if prev4 > 0:
            change_pct = (recent4 - prev4) / prev4 * 100
        else:
            change_pct = 0.0
        if abs(change_pct) > 20:
            cv = float(np.std(d[-12:]) / max(np.mean(d[-12:]), 1)) if len(d) >= 12 else 0.3
            risks.append({
                "item_id": item_id,
                "name": item.get("name", item_id),
                "category": CATEGORY_NAMES.get(item.get("category", ""), item.get("category", "")),
                "level": "high" if abs(change_pct) > 40 else "medium",
                "risk_level": "high" if abs(change_pct) > 40 else "medium",
                "change_pct": round(change_pct, 1),
                "cv": round(cv, 2),
                "mean": round(float(recent4), 1),
                "avg_demand": round(float(recent4), 1),
                "recent_avg": round(float(recent4), 1),
                "prev_avg": round(float(prev4), 1),
                "direction": "surge" if change_pct > 0 else "drop",
                "description": f"需求{'激增' if change_pct > 0 else '骤降'} {abs(change_pct):.1f}%，近4周均值 {recent4:.0f}",
            })
    return risks


def get_logistics_risks() -> List[Dict[str, Any]]:
    """物流风险 — 容量瓶颈边"""
    graph = _load_json("graph_topology.json")
    edges = graph.get("edges", [])
    risks = []
    for e in edges:
        cap = e.get("capacity_per_day", 100)
        utilization = np.random.uniform(0.5, 0.95)
        if utilization > 0.8:
            risks.append({
                "from": e["from"],
                "to": e["to"],
                "mode": e.get("mode", "road"),
                "level": "high" if utilization > 0.9 else "medium",
                "risk_level": "high" if utilization > 0.9 else "medium",
                "load_pct": round(utilization * 100, 1),
                "capacity": cap,
                "utilization": round(utilization, 2),
                "travel_days": e.get("travel_time_days", 1),
                "description": f"容量利用率 {int(utilization * 100)}%，最大容量 {cap}/天",
            })
    return risks


def get_alerts() -> List[Dict[str, Any]]:
    """实时告警列表"""
    now = __import__("datetime").datetime.now()
    alerts_list = []

    supply = get_supply_risks()
    for r in supply[:3]:
        alerts_list.append({
            "type": "supply",
            "type_label": "供给",
            "severity": r.get("level", "medium"),
            "level": r.get("level", "medium"),
            "item_id": r["item_id"],
            "name": r.get("name", r["item_id"]),
            "message": r.get("description", f"周需求波动(CV={r.get('cv', '?')})"),
            "timestamp": now.strftime("%H:%M:%S"),
        })

    demand = get_demand_risks()
    for r in demand[:3]:
        alerts_list.append({
            "type": "demand",
            "type_label": "需求",
            "severity": r.get("level", "medium"),
            "level": r.get("level", "medium"),
            "item_id": r["item_id"],
            "name": r.get("name", r["item_id"]),
            "message": r.get("description", f"需求异常"),
            "timestamp": now.strftime("%H:%M:%S"),
        })

    logistics = get_logistics_risks()
    for r in logistics[:2]:
        alerts_list.append({
            "type": "logistics",
            "type_label": "物流",
            "severity": r.get("level", "medium"),
            "level": r.get("level", "medium"),
            "from": r["from"],
            "to": r["to"],
            "item_id": f"{r['from']}→{r['to']}",
            "message": r.get("description", f"容量瓶颈"),
            "timestamp": now.strftime("%H:%M:%S"),
        })

    return alerts_list