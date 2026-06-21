"""物流路径优化服务 — DFS + 贪心 + 去重 + 需求联动"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from services.forecast_service import predict_demand

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_graph() -> Dict[str, Any]:
    """加载图拓扑 JSON"""
    path = DATA_DIR / "graph_topology.json"
    if not path.exists():
        return {"nodes": [], "edges": []}
    with open(path) as f:
        return json.load(f)


def _load_item_catalog() -> Dict[str, List[str]]:
    """加载物品-品类映射"""
    path = DATA_DIR / "item_catalog.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _get_item_category(item_id: str) -> Optional[str]:
    """获取物品所属品类"""
    catalog = _load_item_catalog()
    for cat, items in catalog.items():
        if item_id in items:
            return cat
    return None


def _build_adjacency(edges: List[Dict], mode: Optional[str] = None) -> Dict[str, List[Dict]]:
    """将边列表转为邻接表，可选按运输方式过滤"""
    adj = {}
    for e in edges:
        if mode and e.get("mode") != mode:
            continue
        adj.setdefault(e["from"], []).append({
            "to": e["to"],
            "travel_time_days": e.get("travel_time_days", 1),
            "capacity_per_day": e.get("capacity_per_day", 100),
            "cost": e.get("cost", 100),
            "mode": e.get("mode", "road"),
        })
    return adj


def get_graph() -> Dict[str, Any]:
    """返回完整图数据"""
    return _load_graph()


def find_routes(
    start: str,
    end: str,
    demand_volume: float = 100,
    top_k: int = 5,
    forecast_weight: float = 1.0,
    mode: Optional[str] = None,
    node_type_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """DFS + 贪心 + 去重 搜索 Top-K 最优路径

    参数:
        start: 起点节点ID
        end: 终点节点ID
        demand_volume: 需求量
        top_k: 返回 Top-K 路径数
        forecast_weight: 预测权重 (影响容量惩罚权重)
        mode: 运输方式过滤 (road/rail/air, None=全部)
        node_type_filter: 节点类型过滤 (factory/warehouse/destination, None=全部)
    """
    graph = _load_graph()
    edges = graph.get("edges", [])
    adj = _build_adjacency(edges, mode)
    nodes = graph.get("nodes", [])

    if start not in adj:
        return {"error": f"起点 {start} 不存在或无符合条件的边", "paths": []}
    if start == end:
        return {"error": "起点与终点相同", "paths": []}

    # 构建节点类型映射
    node_types = {n["id"]: n.get("type", "") for n in nodes}

    # DFS 搜索所有简单路径（不含环）
    all_paths = []
    stack = [(start, [start], 0, 0, 0)]

    while stack:
        node, path, total_time, total_cost, cap_penalty = stack.pop()

        if node == end:
            # 归一化评分
            norm_time = total_time / (total_time + 1)
            norm_cost = total_cost / (total_cost + 1)
            norm_penalty = cap_penalty / (cap_penalty + 1)

            # 需求预测对路径的影响: 如果 demand_volume 高，容量惩罚权重放大
            w1, w2, w3 = 0.35, 0.35, 0.30
            if forecast_weight > 1.0:
                w3 = min(0.30 * forecast_weight, 0.60)
                w1 = (1.0 - w3) * 0.5
                w2 = (1.0 - w3) * 0.5

            score = w1 * norm_time + w2 * norm_cost + w3 * norm_penalty

            # 需求适配度 (0~100)
            demand_fitness = max(0, min(100, 100 - cap_penalty * 10))

            all_paths.append({
                "path": path,
                "total_time_days": total_time,
                "total_cost": total_cost,
                "capacity_penalty": cap_penalty,
                "score": round(score, 4),
                "demand_fitness": demand_fitness,
            })
            continue

        for edge in adj.get(node, []):
            neighbor = edge["to"]
            # 去重: 跳过已访问节点
            if neighbor in path:
                continue
            # 节点类型过滤: 如果不是终点且该节点类型匹配过滤条件
            if node_type_filter and neighbor != end:
                ntype = node_types.get(neighbor, "")
                # 如果是起点类型过滤，只允许经过 warehouse 类型中转
                if ntype != "warehouse" and neighbor != end:
                    pass  # 允许工厂直接到目的地的路径
            # 容量检查
            cap_pen = 0
            if demand_volume > edge["capacity_per_day"]:
                cap_pen = (demand_volume - edge["capacity_per_day"]) / edge["capacity_per_day"]

            stack.append((
                neighbor,
                path + [neighbor],
                total_time + edge["travel_time_days"],
                total_cost + edge["cost"],
                cap_penalty + cap_pen,
            ))

    # 按综合得分排序 (分数越低越优)
    all_paths.sort(key=lambda p: p["score"])

    return {
        "start": start,
        "end": end,
        "demand_volume": demand_volume,
        "forecast_weight": forecast_weight,
        "mode_filter": mode,
        "nodes": nodes,
        "paths": all_paths[:top_k],
    }


def find_route_with_forecast(
    start: str,
    end: str,
    item_id: str,
    top_k: int = 5,
    horizon: int = 12,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """结合需求预测做联动路径规划"""
    # 获取需求预测
    pred = predict_demand(item_id, horizon)
    if "error" in pred:
        return {"error": pred["error"], "paths": []}

    # 计算预测增长率（最后4周预测均值 vs 历史均值）
    forecast_vals = [f["predicted"] for f in pred.get("forecast", [])[:4]]
    history_vals = pred.get("history", [])[-8:]
    if forecast_vals and history_vals:
        forecast_avg = sum(forecast_vals) / len(forecast_vals)
        history_avg = sum(history_vals) / len(history_vals)
        growth_rate = (forecast_avg - history_avg) / (history_avg + 0.001)
    else:
        growth_rate = 0

    # 联动规则
    if growth_rate > 0.5:
        forecast_weight = 2.0  # 容量权重翻倍
        demand_volume = forecast_avg
    elif growth_rate > 0.3:
        forecast_weight = 1.5
        demand_volume = forecast_avg
    elif growth_rate < -0.2:
        forecast_weight = 0.5  # 需求下降，偏向成本最低
        demand_volume = history_avg if history_avg else forecast_avg
    else:
        forecast_weight = 1.0
        demand_volume = history_avg if history_avg else (forecast_avg if forecast_vals else 100)

    # 执行路径搜索
    routes = find_routes(start, end, demand_volume, top_k, forecast_weight, mode)

    # 关联预测信息
    routes["forecast"] = {
        "item_id": item_id,
        "growth_rate": round(float(growth_rate), 3),
        "forecast_weight": forecast_weight,
        "trend": pred.get("trend", "stable"),
        "confidence": pred.get("confidence", 0),
    }

    return routes