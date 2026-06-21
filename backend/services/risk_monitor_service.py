"""风险监控服务 — 从 JSON 数据计算供给、需求、物流等风险指标"""
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORY_NAMES = {
    "apparel": "服装",
    "electronics": "电子产品",
    "food": "食品",
    "medicine": "药品",
    "raw_materials": "原材料",
}


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ──────────────────────────────────────────────
# 供给风险：基于需求数据计算需求异常变化
# ──────────────────────────────────────────────

def get_supply_risks() -> List[Dict[str, Any]]:
    """检测需求激增或骤降的物品 — 供给风险"""
    demand = _load_json("demand_weekly.json")
    items = demand.get("items", {})
    risks = []

    for item_id, item in items.items():
        d = np.array(item.get("weekly_demand", []))
        if len(d) < 12:
            continue

        # 近4周均值 vs 之前8周均值
        recent = d[-4:].mean()
        historical = d[-12:-4].mean()

        if historical == 0:
            continue

        change_pct = (recent - historical) / historical * 100
        abs_change = abs(change_pct)

        if abs_change >= 50:
            level = "high"
        elif abs_change >= 30:
            level = "medium"
        elif abs_change >= 15:
            level = "low"
        else:
            continue

        risks.append({
            "item_id": item_id,
            "category": CATEGORY_NAMES.get(item.get("category", ""), item.get("category", "")),
            "change_pct": round(change_pct, 1),
            "recent_avg": round(float(recent), 1),
            "historical_avg": round(float(historical), 1),
            "level": level,
            "direction": "surge" if change_pct > 0 else "drop",
            "description": f"近4周需求{'激增' if change_pct > 0 else '骤降'} {abs(change_pct):.1f}%",
        })

    risks.sort(key=lambda r: abs(r["change_pct"]), reverse=True)
    return risks


# ──────────────────────────────────────────────
# 需求风险：基于预测波动率 & 置信区间宽度
# ──────────────────────────────────────────────

def get_demand_risks() -> List[Dict[str, Any]]:
    """检测高波动 / 高不确定性的物品 — 需求风险"""
    demand = _load_json("demand_weekly.json")
    items = demand.get("items", {})
    risks = []

    for item_id, item in items.items():
        d = np.array(item.get("weekly_demand", []))
        if len(d) < 12:
            continue

        mean = d.mean()
        std = d.std()
        if mean == 0:
            continue

        cv = std / mean  # 波动率

        # 置信区间宽度（模拟预测区间）
        ci_width = 2 * 1.96 * (std / np.sqrt(12))
        ci_ratio = ci_width / mean if mean > 0 else 0

        if cv >= 0.8 or ci_ratio >= 0.8:
            level = "high"
        elif cv >= 0.5 or ci_ratio >= 0.6:
            level = "medium"
        elif cv >= 0.3 or ci_ratio >= 0.4:
            level = "low"
        else:
            continue

        risks.append({
            "item_id": item_id,
            "category": CATEGORY_NAMES.get(item.get("category", ""), item.get("category", "")),
            "cv": round(float(cv), 3),
            "ci_ratio": round(float(ci_ratio), 3),
            "mean": round(float(mean), 1),
            "std": round(float(std), 1),
            "level": level,
            "description": f"波动率 CV={cv:.2f}，预测区间宽度={ci_ratio:.0%}",
        })

    risks.sort(key=lambda r: r["cv"], reverse=True)
    return risks


# ──────────────────────────────────────────────
# 物流风险：基于图拓扑容量 & 运输属性
# ──────────────────────────────────────────────

def get_logistics_risks() -> List[Dict[str, Any]]:
    """检测容量瓶颈 / 高延迟的物流边 — 物流风险"""
    graph = _load_json("graph_topology.json")
    edges = graph.get("edges", [])
    risks = []

    # 模拟当前负载率 (假设使用均值的60%-95%随机)
    rng = np.random.default_rng(42)

    for edge in edges:
        cap = edge.get("capacity_per_day", 100)
        load_pct = rng.uniform(0.4, 0.95)

        if load_pct >= 0.95:
            level = "high"
        elif load_pct >= 0.80:
            level = "medium"
        elif load_pct >= 0.60:
            level = "low"
        else:
            continue

        time = edge.get("travel_time_days", 1)
        risks.append({
            "from": edge["from"],
            "to": edge["to"],
            "mode": edge.get("mode", "road"),
            "capacity": cap,
            "load_pct": round(float(load_pct * 100), 1),
            "travel_time_days": time,
            "level": level,
            "description": f"{edge['from']}→{edge['to']} 容量使用率 {load_pct*100:.0f}%",
        })

    risks.sort(key=lambda r: r["load_pct"], reverse=True)
    return risks


# ──────────────────────────────────────────────
# 告警列表
# ──────────────────────────────────────────────

def get_alerts() -> List[Dict[str, Any]]:
    """综合生成实时告警列表"""
    alerts = []

    # 从供给风险中提取高危告警
    supply_risks = get_supply_risks()
    for r in supply_risks[:3]:
        alerts.append({
            "type": "supply",
            "type_label": "供给风险",
            "item_id": r["item_id"],
            "level": r["level"],
            "message": r["description"],
            "timestamp": "实时",
        })

    # 从需求风险中提取高危告警
    demand_risks = get_demand_risks()
    for r in demand_risks[:3]:
        alerts.append({
            "type": "demand",
            "type_label": "需求风险",
            "item_id": r["item_id"],
            "level": r["level"],
            "message": r["description"],
            "timestamp": "实时",
        })

    # 从物流风险中提取高危告警
    logistics_risks = get_logistics_risks()
    for r in logistics_risks[:3]:
        alerts.append({
            "type": "logistics",
            "type_label": "物流风险",
            "item_id": f"{r['from']}→{r['to']}",
            "level": r["level"],
            "message": r["description"],
            "timestamp": "实时",
        })

    # 按风险等级排序
    level_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: level_order.get(a["level"], 99))

    return alerts


# ──────────────────────────────────────────────
# 风险总览
# ──────────────────────────────────────────────

def get_overview() -> Dict[str, Any]:
    """聚合四个维度的风险总览"""
    supply = get_supply_risks()
    demand = get_demand_risks()
    logistics = get_logistics_risks()
    all_alerts = get_alerts()

    def count_by_level(risks: List[Dict]) -> Dict[str, int]:
        return {
            "high": sum(1 for r in risks if r["level"] == "high"),
            "medium": sum(1 for r in risks if r["level"] == "medium"),
            "low": sum(1 for r in risks if r["level"] == "low"),
            "total": len(risks),
        }

    def risk_score(risks: List[Dict]) -> float:
        """风险评分 0-100"""
        if not risks:
            return 0
        score = 0
        for r in risks:
            if r["level"] == "high":
                score += 10
            elif r["level"] == "medium":
                score += 5
            elif r["level"] == "low":
                score += 2
        return min(round(score / len(risks) * 10, 1), 100)

    high_count = sum(1 for a in all_alerts if a["level"] == "high")

    return {
        "supply": count_by_level(supply),
        "demand": count_by_level(demand),
        "logistics": count_by_level(logistics),
        "total_high": high_count,
        "total_risks": len(supply) + len(demand) + len(logistics),
        "risk_score": round(
            risk_score(supply) * 0.3
            + risk_score(demand) * 0.35
            + risk_score(logistics) * 0.35,
            1,
        ),
        "level_distribution": [
            {"name": "高风险", "value": sum(
                r["level"] == "high" for r in supply + demand + logistics
            )},
            {"name": "中风险", "value": sum(
                r["level"] == "medium" for r in supply + demand + logistics
            )},
            {"name": "低风险", "value": sum(
                r["level"] == "low" for r in supply + demand + logistics
            )},
        ],
    }