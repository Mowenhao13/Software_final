"""
预处理脚本 — 生成 ISOMORPH 风格供应链数据
- 50 个物品 (C=50)
- 260 周需求 (5 年, 按月/周尺度)
- 5分量需求信号: 年季节性 + 周季节性 + AR(1)漂移 + 突发 + 宏观冲击
- 13 节点图拓扑 (3工厂 + 9仓储 + 1目的地 NYC)
"""
import json
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
DATA_DIR = BASE_DIR / "data"

np.random.seed(2025)

N_ITEMS = 50
N_WEEKS = 156   # 3 年 × 52 周/年 (合理的企业历史数据尺度)
N_DAYS = 1092


def _generate_isomorph_demand():
    """生成 ISOMORPH 风格 5 分量需求信号"""
    # 物品基础参数
    item_params = {
        "I001": {"base": 180, "category": "electronics", "ar_phi": 0.96, "burst_rate": 0.02},
        "I002": {"base": 220, "category": "electronics", "ar_phi": 0.97, "burst_rate": 0.015},
        "I003": {"base": 95, "category": "apparel", "ar_phi": 0.93, "burst_rate": 0.03},
        "I004": {"base": 150, "category": "apparel", "ar_phi": 0.94, "burst_rate": 0.025},
        "I005": {"base": 280, "category": "automotive", "ar_phi": 0.98, "burst_rate": 0.01},
        "I006": {"base": 65, "category": "food", "ar_phi": 0.92, "burst_rate": 0.04},
        "I007": {"base": 310, "category": "automotive", "ar_phi": 0.97, "burst_rate": 0.012},
        "I008": {"base": 120, "category": "pharma", "ar_phi": 0.91, "burst_rate": 0.008},
        "I009": {"base": 200, "category": "electronics", "ar_phi": 0.95, "burst_rate": 0.018},
        "I010": {"base": 85, "category": "food", "ar_phi": 0.90, "burst_rate": 0.035},
    }
    categories_base = {
        "electronics": (150, 250, 0.96),
        "apparel": (80, 180, 0.94),
        "automotive": (200, 350, 0.97),
        "food": (60, 120, 0.91),
        "pharma": (100, 200, 0.93),
    }
    cats = list(categories_base.keys())

    weekly = {}
    all_items_list = []

    for idx in range(1, N_ITEMS + 1):
        item_id = f"I{idx:03d}"
        cat = cats[idx % len(cats)]
        base_lo, base_hi, ar_phi = categories_base[cat]

        base = np.random.uniform(base_lo, base_hi)
        # AR(1) drift
        ar = np.zeros(N_WEEKS)
        ar[0] = np.random.randn() * 10
        for t in range(1, N_WEEKS):
            ar[t] = ar_phi * ar[t-1] + np.random.randn() * 8

        # 年季节性 (52周周期)
        season_yearly = 25 * np.sin(2 * np.pi * np.arange(N_WEEKS) / 52)
        # 月季节性 (4周周期, 叠加)
        season_monthly = 10 * np.sin(2 * np.pi * np.arange(N_WEEKS) / 4.33)

        # 突发事件
        burst = np.zeros(N_WEEKS)
        burst_rate = np.random.uniform(0.005, 0.03)
        burst_height = np.random.uniform(50, 150)
        for t in range(N_WEEKS):
            if np.random.random() < burst_rate:
                burst[t] = burst_height * (1 + np.random.random())
                # 突发持续 2-4 周
                for j in range(1, np.random.randint(2, 5)):
                    if t + j < N_WEEKS:
                        burst[t + j] = burst_height * max(0, 1 - j * 0.3)

        # 宏观冲击 (所有物品同一天受影响)
        macro_shock = np.zeros(N_WEEKS)
        if idx == 1:  # 只为第一个物品生成，全局共享
            pass

        demand = base + ar + season_yearly + season_monthly + burst
        # 确保非负
        demand = np.maximum(demand, 10)

        weekly[item_id] = {
            "item_id": item_id,
            "category": cat,
            "base_demand": round(base, 1),
            "weekly_demand": [round(float(v), 2) for v in demand],
        }
        all_items_list.append(item_id)

    # 全局宏观冲击 (对所有物品通用)
    macro_shock_weeks = np.random.choice(N_WEEKS, size=15, replace=False)  # 约 3 次/年 宏观冲击
    shock_height = np.random.uniform(100, 300)
    for week_idx in macro_shock_weeks:
        for item_id in np.random.choice(all_items_list, size=15, replace=False):
            item = weekly[item_id]
            item["weekly_demand"][week_idx] += shock_height * (1 + np.random.random())

    return weekly, all_items_list


def _generate_graph():
    """生成 13 节点 ISOMORPH 风格图拓扑"""
    nodes = [
        {"id": "Factory_NY", "name": "New York Factory", "type": "factory", "region": "Northeast",
         "coords": [-73.94, 40.81], "capacity": 500},
        {"id": "Factory_CHI", "name": "Chicago Factory", "type": "factory", "region": "Midwest",
         "coords": [-87.63, 41.88], "capacity": 800},
        {"id": "Factory_LA", "name": "LA Factory", "type": "factory", "region": "West",
         "coords": [-118.24, 34.05], "capacity": 600},
        {"id": "Warehouse_1", "name": "NY Metro DC", "type": "warehouse", "region": "Northeast",
         "coords": [-74.01, 40.71], "capacity": 400},
        {"id": "Warehouse_2", "name": "NJ Distribution", "type": "warehouse", "region": "Northeast",
         "coords": [-74.42, 40.72], "capacity": 350},
        {"id": "Warehouse_3", "name": "Chicago Hub", "type": "warehouse", "region": "Midwest",
         "coords": [-87.62, 41.87], "capacity": 450},
        {"id": "Warehouse_4", "name": "Atlanta Hub", "type": "warehouse", "region": "Southeast",
         "coords": [-84.39, 33.75], "capacity": 300},
        {"id": "Warehouse_5", "name": "Dallas Hub", "type": "warehouse", "region": "South",
         "coords": [-96.80, 32.78], "capacity": 320},
        {"id": "Warehouse_6", "name": "LA Distribution", "type": "warehouse", "region": "West",
         "coords": [-118.24, 34.05], "capacity": 380},
        {"id": "Warehouse_7", "name": "Denver Hub", "type": "warehouse", "region": "Mountain",
         "coords": [-104.99, 39.74], "capacity": 250},
        {"id": "Warehouse_8", "name": "Seattle Hub", "type": "warehouse", "region": "West",
         "coords": [-122.33, 47.61], "capacity": 280},
        {"id": "Warehouse_9", "name": "DC Distribution", "type": "warehouse", "region": "Northeast",
         "coords": [-77.04, 38.91], "capacity": 360},
        {"id": "NYC_Destination", "name": "NYC Customer Center", "type": "destination", "region": "Northeast",
         "coords": [-73.99, 40.76], "capacity": 9999},
    ]

    edges = [
        {"from": "Factory_NY", "to": "Warehouse_1", "travel_time_days": 2, "capacity_per_day": 100, "cost": 200, "mode": "road"},
        {"from": "Factory_NY", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 80, "cost": 300, "mode": "road"},
        {"from": "Factory_CHI", "to": "Warehouse_3", "travel_time_days": 1, "capacity_per_day": 150, "cost": 100, "mode": "road"},
        {"from": "Factory_CHI", "to": "Warehouse_5", "travel_time_days": 3, "capacity_per_day": 120, "cost": 250, "mode": "rail"},
        {"from": "Factory_CHI", "to": "Warehouse_7", "travel_time_days": 4, "capacity_per_day": 90, "cost": 350, "mode": "rail"},
        {"from": "Factory_LA", "to": "Warehouse_6", "travel_time_days": 1, "capacity_per_day": 140, "cost": 150, "mode": "road"},
        {"from": "Factory_LA", "to": "Warehouse_8", "travel_time_days": 3, "capacity_per_day": 100, "cost": 280, "mode": "rail"},
        {"from": "Warehouse_1", "to": "Warehouse_2", "travel_time_days": 1, "capacity_per_day": 120, "cost": 80, "mode": "road"},
        {"from": "Warehouse_1", "to": "Warehouse_9", "travel_time_days": 2, "capacity_per_day": 100, "cost": 180, "mode": "road"},
        {"from": "Warehouse_2", "to": "NYC_Destination", "travel_time_days": 1, "capacity_per_day": 130, "cost": 60, "mode": "road"},
        {"from": "Warehouse_3", "to": "Warehouse_5", "travel_time_days": 3, "capacity_per_day": 110, "cost": 220, "mode": "rail"},
        {"from": "Warehouse_3", "to": "Warehouse_4", "travel_time_days": 2, "capacity_per_day": 100, "cost": 170, "mode": "road"},
        {"from": "Warehouse_4", "to": "Warehouse_9", "travel_time_days": 2, "capacity_per_day": 90, "cost": 200, "mode": "road"},
        {"from": "Warehouse_5", "to": "Warehouse_7", "travel_time_days": 2, "capacity_per_day": 80, "cost": 190, "mode": "road"},
        {"from": "Warehouse_5", "to": "Warehouse_4", "travel_time_days": 2, "capacity_per_day": 95, "cost": 160, "mode": "road"},
        {"from": "Warehouse_6", "to": "Warehouse_7", "travel_time_days": 3, "capacity_per_day": 85, "cost": 260, "mode": "rail"},
        {"from": "Warehouse_6", "to": "Warehouse_8", "travel_time_days": 2, "capacity_per_day": 90, "cost": 200, "mode": "road"},
        {"from": "Warehouse_7", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 75, "cost": 280, "mode": "rail"},
        {"from": "Warehouse_8", "to": "Warehouse_7", "travel_time_days": 2, "capacity_per_day": 80, "cost": 210, "mode": "road"},
        {"from": "Warehouse_8", "to": "Warehouse_9", "travel_time_days": 4, "capacity_per_day": 70, "cost": 350, "mode": "rail"},
        {"from": "Warehouse_9", "to": "NYC_Destination", "travel_time_days": 1, "capacity_per_day": 120, "cost": 80, "mode": "road"},
        {"from": "Warehouse_2", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 70, "cost": 250, "mode": "road"},
        {"from": "Warehouse_4", "to": "NYC_Destination", "travel_time_days": 2, "capacity_per_day": 85, "cost": 180, "mode": "road"},
    ]

    return nodes, edges


def _generate_dashboard_data(weekly_data):
    """从需求数据生成 KPI、趋势、地图 — 基于最近 30 周数据"""
    from datetime import datetime, timedelta
    now = datetime.now()

    # === KPI — 使用最近 30 周数据 ===
    all_demand_recent = [] # 最近 30 周

    for item_id, item in weekly_data.items():
        d = np.array(item["weekly_demand"])
        if len(d) >= 30:
            all_demand_recent.extend(d[-30:])
        else:
            all_demand_recent.extend(d)

    total_demand = int(np.sum(all_demand_recent))

    # 周均总需求 = 最近30周内每周所有物品需求之和的平均
    weekly_totals = []
    for item_id, item in weekly_data.items():
        d = np.array(item["weekly_demand"])
        if len(weekly_totals) == 0:
            weekly_totals = d.copy()
        else:
            weekly_totals += d
    recent_weekly_totals = weekly_totals[-30:] if len(weekly_totals) >= 30 else weekly_totals
    avg_weekly_total = float(np.mean(recent_weekly_totals))

    # 月环比增长：比较近 4 周 vs 前 4 周（基于最近30周）
    if len(recent_weekly_totals) >= 8:
        recent4 = np.mean(recent_weekly_totals[-4:])
        prev4 = np.mean(recent_weekly_totals[-8:-4])
        if prev4 > 0:
            month_growth = round((recent4 - prev4) / prev4 * 100, 1)
        else:
            month_growth = round(np.random.uniform(3.0, 10.0), 1)
    else:
        month_growth = round(np.random.uniform(3.0, 10.0), 1)

    kpi = {
        "total_orders": total_demand,                          # 最近30周总需求（单位量）
        "total_amount": round(total_demand * 0.1285, 2),       # 总金额（万元）：需求×单价换算
        "on_time_delivery_rate": round(94.5 + np.random.uniform(-2, 2), 1),
        "inventory_turnover": round(4.2 + np.random.uniform(-0.5, 0.5), 1),
        "active_suppliers": 15,
        "risk_count": np.random.randint(3, 8),
        "cost_total": round(total_demand * 0.085, 2),          # 总成本（万元）
        "month_growth": month_growth,
        "total_items": len(weekly_data),
        "avg_weekly_demand": round(avg_weekly_total, 0),       # 最近30周所有物品合计周均需求
        "prediction_confidence": round(0.70 + np.random.uniform(-0.05, 0.15), 2),
    }
    with open(DATA_DIR / "kpi_snapshot.json", "w") as f:
        json.dump(kpi, f, indent=2)

    # === 30 天趋势 — 基于真实需求数据抽取 ===
    # 将 156 周映射到 30 天（每周聚合为日并插值）
    trends = []
    n_weeks = min(N_WEEKS, 52)  # 用最近 1 年
    for i in range(30):
        d = now - timedelta(days=29 - i)
        # 映射到周索引
        week_idx = n_weeks - 30 + i
        if week_idx < 0:
            week_idx = 0
        if week_idx >= len(weekly_totals):
            week_idx = len(weekly_totals) - 1
        weekly_total = weekly_totals[week_idx] if week_idx < len(weekly_totals) else np.mean(weekly_totals)

        # 用周总需求估算日订单数
        daily_orders = int(weekly_total / 7 * (0.85 + np.random.random() * 0.3))
        unit_price = np.random.uniform(100, 160)
        cost_ratio = np.random.uniform(0.55, 0.72)

        trends.append({
            "date": d.strftime("%Y-%m-%d"),
            "orders": daily_orders,
            "amount": round(float(daily_orders * unit_price), 2),
            "cost": round(float(daily_orders * unit_price * cost_ratio), 2),
        })
    with open(DATA_DIR / "trends.json", "w") as f:
        json.dump({"trends": trends}, f, indent=2)

    # === 品类分布（保持不变） ===
    cat_stats = {}
    for item_id, item in weekly_data.items():
        cat = item.get("category", "general")
        cat_stats.setdefault(cat, {"count": 0, "total_demand": 0})
        cat_stats[cat]["count"] += 1
        cat_stats[cat]["total_demand"] += sum(item["weekly_demand"][-52:])
    cat_distribution = [
        {"category": k, "count": v["count"], "total_demand": round(v["total_demand"], 0)}
        for k, v in cat_stats.items()
    ]
    with open(DATA_DIR / "category_distribution.json", "w") as f:
        json.dump(cat_distribution, f, indent=2)

    # === 供应链地图 — 从图拓扑动态生成（保持不变） ===
    carriers = ["Carrier_A", "Carrier_B", "Carrier_C", "Carrier_D", "Carrier_E"]
    statuses = ["in_transit", "delivered", "delayed", "pending"]

    graph_path = DATA_DIR / "graph_topology.json"
    if graph_path.exists():
        with open(graph_path) as gf:
            graph_data = json.load(gf)
    else:
        graph_data = {"nodes": [], "edges": []}

    node_coords = {}
    for n in graph_data.get("nodes", []):
        coords = n.get("coords", [0, 0])
        node_coords[n["id"]] = coords

    edges = graph_data.get("edges", [])
    active_edges = np.random.choice(
        len(edges),
        size=max(1, int(len(edges) * 0.7)),
        replace=False,
    )

    map_routes = []
    for idx in active_edges:
        edge = edges[idx]
        origin = edge["from"]
        dest = edge["to"]
        origin_coords = node_coords.get(origin, [0, 0])
        dest_coords = node_coords.get(dest, [0, 0])
        status = np.random.choice(statuses, p=[0.5, 0.2, 0.15, 0.15])
        carrier = np.random.choice(carriers)
        travel_time = edge.get("travel_time_days", 2) * 24
        eta = travel_time if status == "in_transit" else (0 if status == "delivered" else travel_time * 0.5)

        map_routes.append({
            "origin": origin,
            "destination": dest,
            "mode": edge.get("mode", "road"),
            "origin_coords": origin_coords,
            "dest_coords": dest_coords,
            "status": status,
            "carrier": carrier,
            "eta_hours": int(eta),
        })

    routes_in_transit = sum(1 for r in map_routes if r["status"] == "in_transit")
    routes_delivered = sum(1 for r in map_routes if r["status"] == "delivered")
    routes_delayed = sum(1 for r in map_routes if r["status"] == "delayed")
    routes_pending = sum(1 for r in map_routes if r["status"] == "pending")
    with open(DATA_DIR / "supply_chain_map.json", "w") as f:
        json.dump({
            "routes": map_routes,
            "total_in_transit": routes_in_transit,
            "total_delivered": routes_delivered,
            "total_delayed": routes_delayed,
            "total_pending": routes_pending,
        }, f, indent=2)

    print(f"KPI + 趋势 + 品类分布 + 地图已写入 {DATA_DIR}")
    print(f"  total_demand(全量156周) = {total_demand:,}")
    print(f"  avg_weekly_total(周均合计) = {avg_weekly_total:,.0f}")
    print(f"  month_growth = {month_growth}%")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("生成 ISOMORPH 风格供应链数据...")
    print(f"  物品数: {N_ITEMS}")
    print(f"  周数: {N_WEEKS} 周 (等价 {N_DAYS:,} 天)")
    print("=" * 60)

    # 1. 需求数据
    print("\n[1/4] 生成需求信号...")
    weekly_data, item_ids = _generate_isomorph_demand()
    with open(DATA_DIR / "demand_weekly.json", "w") as f:
        json.dump({
            "total_weeks": N_WEEKS,
            "total_items": len(weekly_data),
            "items": weekly_data,
        }, f, indent=2)
    sample = list(weekly_data.keys())[:3]
    print(f"  ✅ demand_weekly.json: {len(weekly_data)} items × {N_WEEKS} weeks")
    print(f"     示例: {sample}")

    # 2. 图拓扑
    print("\n[2/4] 生成图拓扑...")
    nodes, edges = _generate_graph()
    with open(DATA_DIR / "graph_topology.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
    print(f"  ✅ graph_topology.json: {len(nodes)} 节点, {len(edges)} 条边")

    # 3. 品类-物品映射
    print("\n[3/4] 生成品类-物品映射...")
    category_items = {}
    for item_id, item in weekly_data.items():
        cat = item.get("category", "general")
        category_items.setdefault(cat, []).append(item_id)
    with open(DATA_DIR / "item_catalog.json", "w") as f:
        json.dump(category_items, f, indent=2)
    print(f"  ✅ item_catalog.json: {dict((k, len(v)) for k, v in category_items.items())}")

    # 4. 仪表盘数据
    print("\n[4/4] 生成仪表盘数据...")
    _generate_dashboard_data(weekly_data)

    # 统计
    total_size = sum(
        f.stat().st_size for f in DATA_DIR.glob("*.json")
    )
    print(f"\n{'=' * 60}")
    print(f"✅ 全部完成! 数据目录: {DATA_DIR}")
    print(f"   总大小: {total_size / 1024:.1f} KB")
    print(f"   文件数: {len(list(DATA_DIR.glob('*.json')))} 个")


if __name__ == "__main__":
    main()