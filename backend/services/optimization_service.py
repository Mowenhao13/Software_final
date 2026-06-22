"""物流路径优化服务 — DFS + 贪心 + 去重 + 需求联动（支持多数据集切换）"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from services.dataset_manager import get_data_dir
from services.forecast_service import predict_demand


def _load_graph() -> Dict[str, Any]:
    """加载图拓扑 JSON"""
    path = get_data_dir() / "graph_topology.json"
    if not path.exists():
        return {"nodes": [], "edges": []}
    with open(path) as f:
        return json.load(f)


def _load_item_catalog() -> Dict[str, List[str]]:
    """加载物品-品类映射"""
    path = get_data_dir() / "item_catalog.json"
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


def get_graph() -> Dict[str, Any]:
    """返回图拓扑（含节点坐标、边属性）"""
    return _load_graph()


def _dfs_all_paths(
    graph: Dict[str, Any],
    start: str,
    end: str,
    max_depth: int = 6,
) -> List[List[str]]:
    """DFS 枚举所有简单路径（不超过 max_depth 跳）"""
    adj: Dict[str, List[Tuple[str, dict]]] = {}
    for e in graph.get("edges", []):
        adj.setdefault(e["from"], []).append((e["to"], e))
        # 无向图：双向可达
        adj.setdefault(e["to"], []).append((e["from"], e))

    all_paths: List[List[str]] = []
    visited = set()

    def dfs(current: str, path: List[str]):
        if len(path) > max_depth:
            return
        if current == end:
            all_paths.append(path.copy())
            return
        for neighbor, _ in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path)
                path.pop()
                visited.remove(neighbor)

    visited.add(start)
    dfs(start, [start])
    return all_paths


def _score_path(
    path: List[str],
    graph: Dict[str, Any],
    demand_volume: float,
    forecast_weight: float = 1.0,
    mode_filter: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """评估一条路径的综合得分（考虑成本、时间、容量、运输方式）"""
    total_cost = 0.0
    total_time = 0
    min_capacity = float("inf")
    edges_used = []
    valid = True

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        found = False
        for e in graph.get("edges", []):
            # 支持双向匹配（DFS 将图视为无向图搜索）
            if (e["from"] == u and e["to"] == v) or (e["from"] == v and e["to"] == u):
                found = True
                if mode_filter and e.get("mode") != mode_filter:
                    valid = False
                    break
                total_cost += e.get("cost", 0) * (demand_volume / max(e.get("capacity_per_day", 1), 1))
                total_time += e.get("travel_time_days", 1)
                min_capacity = min(min_capacity, e.get("capacity_per_day", float("inf")))
                edges_used.append(e)
                break

        if not found or not valid:
            return None

    # 容量检查：需求超过容量 < 3 倍即可（模拟场景中容量可弹性扩展）
    if demand_volume > min_capacity * 3:
        return None

    score = total_cost + forecast_weight * total_time
    return {
        "path": path,
        "total_cost": round(total_cost, 2),
        "total_days": total_time,
        "min_capacity": min_capacity,
        "score": round(score, 2),
        "edges": edges_used,
        "hops": len(path) - 1,
    }


def _deduplicate_paths(results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """基于路径节点集合去重：如果两条路径共享超过 60% 节点则视为重复"""
    if not results:
        return []
    deduped = [results[0]]
    for r in results[1:]:
        nodes = set(r["path"])
        is_dup = False
        for d in deduped:
            d_nodes = set(d["path"])
            if len(nodes & d_nodes) / max(len(nodes | d_nodes), 1) > 0.6:
                is_dup = True
                break
        if not is_dup:
            deduped.append(r)
        if len(deduped) >= top_k:
            break
    return deduped


def find_routes(
    start: str,
    end: str,
    demand_volume: float = 100,
    top_k: int = 5,
    forecast_weight: float = 1.0,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """入口：DFS + 贪心评分 + 去重
    当 mode 过滤下无有效路径时，自动放宽过滤并标记 mode_relaxed=True
    """
    graph = _load_graph()
    paths = _dfs_all_paths(graph, start, end)
    if not paths:
        return {"error": f"无法找到从 {start} 到 {end} 的路径", "routes": []}

    def _search(mode_filter):
        scored = []
        for p in paths:
            s = _score_path(p, graph, demand_volume, forecast_weight, mode_filter)
            if s:
                scored.append(s)
        scored.sort(key=lambda x: x["score"])
        return scored

    scored = _search(mode)
    mode_relaxed = False

    # 如果严格过滤无结果且指定了 mode，自动放宽
    if not scored and mode is not None:
        scored = _search(None)
        mode_relaxed = True

    deduped = _deduplicate_paths(scored, top_k)

    # 添加前端兼容字段
    for r in deduped:
        r["total_time_days"] = r["total_days"]
        r["demand_fitness"] = round(
            min(100, (r["min_capacity"] / demand_volume) * 100 if demand_volume > 0 else 100), 1
        )
        # 标记每条边上实际使用的运输方式
        r["segments"] = []
        for i in range(len(r["path"]) - 1):
            u, v = r["path"][i], r["path"][i + 1]
            for e in graph.get("edges", []):
                if e["from"] == u and e["to"] == v:
                    r["segments"].append({
                        "from": u, "to": v,
                        "mode": e.get("mode", "road"),
                        "cost": e.get("cost", 0),
                        "days": e.get("travel_time_days", 1),
                    })
                    break

    return {
        "start": start,
        "end": end,
        "demand_volume": demand_volume,
        "total_paths_found": len(paths),
        "valid_paths": len(scored),
        "routes": deduped,
        "paths": deduped,
        "mode_filter": mode,
        "mode_relaxed": mode_relaxed,
        "nodes": graph.get("nodes", []),
    }


def find_route_with_forecast(
    start: str,
    end: str,
    item_id: str,
    top_k: int = 5,
    horizon: int = 12,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """结合需求预测做联动路径规划：先查品类匹配，再调 find_routes"""
    category = _get_item_category(item_id)
    if not category:
        return {"error": f"物品 {item_id} 未找到品类映射", "routes": []}

    forecast = predict_demand(item_id, horizon)
    forecast_series = forecast.get("forecast", [])
    avg_forecast = sum(f.get("mean", 0) for f in forecast_series) / max(len(forecast_series), 1)

    if avg_forecast == 0:
        avg_forecast = 100  # fallback

    result = find_routes(
        start=start,
        end=end,
        demand_volume=avg_forecast,
        top_k=top_k,
        forecast_weight=1.2,
        mode=mode,
    )

    # 添加 forecast 信息（前端兼容）
    first_forecast = forecast_series[0] if forecast_series else {}
    result["forecast"] = {
        "item_id": item_id,
        "trend": first_forecast.get("trend", "stable"),
        "growth_rate": first_forecast.get("growth_rate", 0.0),
        "confidence": forecast.get("confidence", first_forecast.get("confidence", 0.5)),
        "forecast_weight": 1.2,
    }

    return result