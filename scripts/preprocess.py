"""
预处理脚本 — 生成 ISOMORPH 风格供应链数据
支持多数据集生成:
  standard  — 50 物品 × 156 周, 5 通用品类 (默认)
  detailed  — 40 种具体商品 × 156 周, 含真实商品名

5分量需求信号: 年季节性 + 周季节性 + AR(1)漂移 + 突发 + 宏观冲击
13 节点图拓扑 (3工厂 + 9仓储 + 1目的地 NYC)
"""
import json
import numpy as np
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
DATA_ROOT = BASE_DIR / "data"

np.random.seed(2025)

N_WEEKS = 156   # 3 年 × 52 周/年
N_DAYS = 1092


# =============================================================
# 数据集配置
# =============================================================

# 基础数据集: 50 物品 × 5 通用品类
STANDARD_CONFIG = {
    "name": "standard",
    "categories": {
        "electronics": (150, 250, 0.96),
        "apparel": (80, 180, 0.94),
        "automotive": (200, 350, 0.97),
        "food": (60, 120, 0.91),
        "pharma": (100, 200, 0.93),
    },
    "n_items": 50,
    "items": {},  # 自动生成
}

# 精细化数据集: 40 种具体商品
DETAILED_CONFIG = {
    "name": "detailed",
    "categories": {},  # 由 items 自动推导
    "n_items": 40,
    "items": {
        # 电子产品 (8)
        "P001": {"name": "智能手机", "category": "electronics", "base": 280, "ar_phi": 0.96, "burst_rate": 0.015},
        "P002": {"name": "笔记本电脑", "category": "electronics", "base": 200, "ar_phi": 0.95, "burst_rate": 0.012},
        "P003": {"name": "平板电脑", "category": "electronics", "base": 150, "ar_phi": 0.94, "burst_rate": 0.018},
        "P004": {"name": "无线耳机", "category": "electronics", "base": 120, "ar_phi": 0.93, "burst_rate": 0.025},
        "P005": {"name": "智能手表", "category": "electronics", "base": 180, "ar_phi": 0.95, "burst_rate": 0.02},
        "P006": {"name": "数码相机", "category": "electronics", "base": 100, "ar_phi": 0.92, "burst_rate": 0.01},
        "P007": {"name": "游戏主机", "category": "electronics", "base": 160, "ar_phi": 0.94, "burst_rate": 0.015},
        "P008": {"name": "蓝牙音箱", "category": "electronics", "base": 90, "ar_phi": 0.91, "burst_rate": 0.03},
        # 食品饮料 (10)
        "P009": {"name": "冷冻三文鱼", "category": "food", "base": 95, "ar_phi": 0.92, "burst_rate": 0.03},
        "P010": {"name": "有机牛奶", "category": "food", "base": 250, "ar_phi": 0.94, "burst_rate": 0.025},
        "P011": {"name": "进口牛肉", "category": "food", "base": 140, "ar_phi": 0.93, "burst_rate": 0.02},
        "P012": {"name": "休闲零食", "category": "food", "base": 200, "ar_phi": 0.95, "burst_rate": 0.035},
        "P013": {"name": "瓶装饮料", "category": "food", "base": 300, "ar_phi": 0.96, "burst_rate": 0.04},
        "P014": {"name": "速冻水饺", "category": "food", "base": 110, "ar_phi": 0.91, "burst_rate": 0.03},
        "P015": {"name": "进口红酒", "category": "food", "base": 70, "ar_phi": 0.90, "burst_rate": 0.015},
        "P016": {"name": "烘焙面包", "category": "food", "base": 180, "ar_phi": 0.93, "burst_rate": 0.04},
        "P017": {"name": "新鲜水果", "category": "food", "base": 220, "ar_phi": 0.94, "burst_rate": 0.04},
        "P018": {"name": "坚果礼盒", "category": "food", "base": 85, "ar_phi": 0.92, "burst_rate": 0.025},
        # 服装鞋帽 (8)
        "P019": {"name": "纯棉T恤", "category": "apparel", "base": 160, "ar_phi": 0.93, "burst_rate": 0.03},
        "P020": {"name": "牛仔裤", "category": "apparel", "base": 120, "ar_phi": 0.94, "burst_rate": 0.02},
        "P021": {"name": "运动鞋", "category": "apparel", "base": 100, "ar_phi": 0.92, "burst_rate": 0.025},
        "P022": {"name": "羽绒服", "category": "apparel", "base": 60, "ar_phi": 0.91, "burst_rate": 0.01},
        "P023": {"name": "休闲帽", "category": "apparel", "base": 130, "ar_phi": 0.93, "burst_rate": 0.035},
        "P024": {"name": "真皮皮带", "category": "apparel", "base": 80, "ar_phi": 0.90, "burst_rate": 0.015},
        "P025": {"name": "羊毛围巾", "category": "apparel", "base": 65, "ar_phi": 0.91, "burst_rate": 0.02},
        "P026": {"name": "太阳镜", "category": "apparel", "base": 90, "ar_phi": 0.92, "burst_rate": 0.025},
        # 汽车配件 (7)
        "P027": {"name": "汽车轮胎", "category": "automotive", "base": 200, "ar_phi": 0.97, "burst_rate": 0.01},
        "P028": {"name": "刹车片", "category": "automotive", "base": 160, "ar_phi": 0.96, "burst_rate": 0.012},
        "P029": {"name": "发动机机油", "category": "automotive", "base": 180, "ar_phi": 0.95, "burst_rate": 0.015},
        "P030": {"name": "汽车车灯", "category": "automotive", "base": 100, "ar_phi": 0.94, "burst_rate": 0.018},
        "P031": {"name": "雨刮器", "category": "automotive", "base": 140, "ar_phi": 0.93, "burst_rate": 0.02},
        "P032": {"name": "车载充电器", "category": "automotive", "base": 120, "ar_phi": 0.92, "burst_rate": 0.025},
        "P033": {"name": "空调滤芯", "category": "automotive", "base": 110, "ar_phi": 0.93, "burst_rate": 0.02},
        # 医药保健 (7)
        "P034": {"name": "处方抗生素", "category": "pharma", "base": 150, "ar_phi": 0.93, "burst_rate": 0.008},
        "P035": {"name": "复合维生素", "category": "pharma", "base": 200, "ar_phi": 0.94, "burst_rate": 0.01},
        "P036": {"name": "血压计", "category": "pharma", "base": 60, "ar_phi": 0.91, "burst_rate": 0.005},
        "P037": {"name": "医用口罩", "category": "pharma", "base": 350, "ar_phi": 0.97, "burst_rate": 0.04},
        "P038": {"name": "退烧药", "category": "pharma", "base": 130, "ar_phi": 0.92, "burst_rate": 0.015},
        "P039": {"name": "钙片", "category": "pharma", "base": 160, "ar_phi": 0.93, "burst_rate": 0.01},
        "P040": {"name": "血糖仪", "category": "pharma", "base": 70, "ar_phi": 0.90, "burst_rate": 0.008},
    },
}


def _get_config(dataset_name: str):
    """获取数据集配置"""
    if dataset_name == "detailed":
        return DETAILED_CONFIG
    return STANDARD_CONFIG


def _generate_standard_items(config):
    """为基础数据集自动生成物品参数"""
    cats = list(config["categories"].keys())
    items = {}
    for idx in range(1, config["n_items"] + 1):
        item_id = f"I{idx:03d}"
        cat = cats[idx % len(cats)]
        items[item_id] = {
            "name": None,
            "category": cat,
            "base": None,  # 由 _generate_isomorph_demand 随机生成
            "ar_phi": config["categories"][cat][2],
            "burst_rate": None,
        }
    return items


def _generate_isomorph_demand(config, data_dir):
    """生成 ISOMORPH 风格 5 分量需求信号"""
    weekly = {}
    all_items_list = []

    items_config = config.get("items", {})
    if not items_config:
        items_config = _generate_standard_items(config)

    categories_base = config.get("categories", {})

    for item_id, item_params in items_config.items():
        cat = item_params["category"]
        name = item_params.get("name")

        # 获取品类参数
        if cat in categories_base:
            base_lo, base_hi, _ = categories_base[cat]
        else:
            base_lo, base_hi = 80, 200

        if item_params.get("base") is not None:
            base = item_params["base"]
        else:
            base = np.random.uniform(base_lo, base_hi)

        ar_phi = item_params.get("ar_phi", 0.94)
        burst_rate = item_params.get("burst_rate")
        if burst_rate is None:
            burst_rate = np.random.uniform(0.005, 0.03)

        # AR(1) drift
        ar = np.zeros(N_WEEKS)
        ar[0] = np.random.randn() * 10
        for t in range(1, N_WEEKS):
            ar[t] = ar_phi * ar[t-1] + np.random.randn() * 8

        # 年季节性 (52周周期)
        season_yearly = 25 * np.sin(2 * np.pi * np.arange(N_WEEKS) / 52)
        # 月季节性 (4周周期)
        season_monthly = 10 * np.sin(2 * np.pi * np.arange(N_WEEKS) / 4.33)

        # 突发事件
        burst = np.zeros(N_WEEKS)
        burst_height = np.random.uniform(50, 150)
        for t in range(N_WEEKS):
            if np.random.random() < burst_rate:
                burst[t] = burst_height * (1 + np.random.random())
                for j in range(1, np.random.randint(2, 5)):
                    if t + j < N_WEEKS:
                        burst[t + j] = burst_height * max(0, 1 - j * 0.3)

        demand = base + ar + season_yearly + season_monthly + burst
        demand = np.maximum(demand, 10)

        entry = {
            "item_id": item_id,
            "category": cat,
            "base_demand": round(base, 1),
            "weekly_demand": [round(float(v), 2) for v in demand],
        }
        if name:
            entry["name"] = name

        weekly[item_id] = entry
        all_items_list.append(item_id)

    # 全局宏观冲击
    shock_height = np.random.uniform(100, 300)
    macro_shock_weeks = np.random.choice(N_WEEKS, size=15, replace=False)
    for week_idx in macro_shock_weeks:
        target_items = np.random.choice(all_items_list, size=min(15, len(all_items_list)), replace=False)
        for item_id in target_items:
            weekly[item_id]["weekly_demand"][week_idx] += shock_height * (1 + np.random.random())

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


def _generate_dashboard_data(weekly_data, data_dir):
    """从需求数据生成 KPI、趋势、地图 — 基于最近 30 周数据"""
    from datetime import datetime, timedelta
    now = datetime.now()

    all_demand_recent = []
    for item_id, item in weekly_data.items():
        d = np.array(item["weekly_demand"])
        if len(d) >= 30:
            all_demand_recent.extend(d[-30:])
        else:
            all_demand_recent.extend(d)

    total_demand = int(np.sum(all_demand_recent))

    weekly_totals = []
    for item_id, item in weekly_data.items():
        d = np.array(item["weekly_demand"])
        if len(weekly_totals) == 0:
            weekly_totals = d.copy()
        else:
            weekly_totals += d
    recent_weekly_totals = weekly_totals[-30:] if len(weekly_totals) >= 30 else weekly_totals
    avg_weekly_total = float(np.mean(recent_weekly_totals))

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
        "total_orders": total_demand,
        "total_amount": round(total_demand * 0.1285, 2),
        "on_time_delivery_rate": round(94.5 + np.random.uniform(-2, 2), 1),
        "inventory_turnover": round(4.2 + np.random.uniform(-0.5, 0.5), 1),
        "active_suppliers": 15,
        "risk_count": np.random.randint(3, 8),
        "cost_total": round(total_demand * 0.085, 2),
        "month_growth": month_growth,
        "total_items": len(weekly_data),
        "avg_weekly_demand": round(avg_weekly_total, 0),
        "prediction_confidence": round(0.70 + np.random.uniform(-0.05, 0.15), 2),
    }
    with open(data_dir / "kpi_snapshot.json", "w") as f:
        json.dump(kpi, f, indent=2)

    # 30 天趋势
    trends = []
    n_weeks = min(N_WEEKS, 52)
    for i in range(30):
        d = now - timedelta(days=29 - i)
        week_idx = n_weeks - 30 + i
        if week_idx < 0:
            week_idx = 0
        if week_idx >= len(weekly_totals):
            week_idx = len(weekly_totals) - 1
        weekly_total = weekly_totals[week_idx] if week_idx < len(weekly_totals) else np.mean(weekly_totals)
        daily_orders = int(weekly_total / 7 * (0.85 + np.random.random() * 0.3))
        unit_price = np.random.uniform(100, 160)
        cost_ratio = np.random.uniform(0.55, 0.72)
        trends.append({
            "date": d.strftime("%Y-%m-%d"),
            "orders": daily_orders,
            "amount": round(float(daily_orders * unit_price), 2),
            "cost": round(float(daily_orders * unit_price * cost_ratio), 2),
        })
    with open(data_dir / "trends.json", "w") as f:
        json.dump({"trends": trends}, f, indent=2)

    # 品类分布
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
    with open(data_dir / "category_distribution.json", "w") as f:
        json.dump(cat_distribution, f, indent=2)

    # 供应链地图
    carriers = ["Carrier_A", "Carrier_B", "Carrier_C", "Carrier_D", "Carrier_E"]
    statuses = ["in_transit", "delivered", "delayed", "pending"]

    graph_path = data_dir / "graph_topology.json"
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
        status = np.random.choice(statuses, p=[0.5, 0.2, 0.15, 0.15])
        travel_time = edge.get("travel_time_days", 2) * 24
        map_routes.append({
            "origin": edge["from"],
            "destination": edge["to"],
            "mode": edge.get("mode", "road"),
            "origin_coords": node_coords.get(edge["from"], [0, 0]),
            "dest_coords": node_coords.get(edge["to"], [0, 0]),
            "status": status,
            "carrier": np.random.choice(carriers),
            "eta_hours": int(travel_time if status == "in_transit" else (0 if status == "delivered" else travel_time * 0.5)),
        })

    with open(data_dir / "supply_chain_map.json", "w") as f:
        json.dump({
            "routes": map_routes,
            "total_in_transit": sum(1 for r in map_routes if r["status"] == "in_transit"),
            "total_delivered": sum(1 for r in map_routes if r["status"] == "delivered"),
            "total_delayed": sum(1 for r in map_routes if r["status"] == "delayed"),
            "total_pending": sum(1 for r in map_routes if r["status"] == "pending"),
        }, f, indent=2)

    print(f"  KPI + 趋势 + 品类分布 + 地图已写入 {data_dir}")
    print(f"  total_demand(最近30周) = {total_demand:,}")
    print(f"  avg_weekly_total(周均合计) = {avg_weekly_total:,.0f}")
    print(f"  month_growth = {month_growth}%")


def generate_dataset(dataset_name: str):
    """生成指定数据集的所有文件"""
    config = _get_config(dataset_name)
    data_dir = DATA_ROOT / dataset_name
    data_dir.mkdir(parents=True, exist_ok=True)

    # 使用不同的随机种子以获得不同数据
    seed = 2025 if dataset_name == "standard" else 2026
    np.random.seed(seed)

    item_count = config["n_items"]

    print(f"\n{'='*60}")
    print(f"生成数据集: {dataset_name}")
    if dataset_name == "detailed":
        print(f"  {item_count} 种具体商品 × {N_WEEKS} 周")
    else:
        print(f"  {item_count} 物品 × {N_WEEKS} 周")
    print(f"  目录: {data_dir}")
    print("=" * 60)

    # 1. 需求数据
    print(f"\n[1/4] 生成需求信号...")
    weekly_data, item_ids = _generate_isomorph_demand(config, data_dir)
    with open(data_dir / "demand_weekly.json", "w") as f:
        json.dump({
            "total_weeks": N_WEEKS,
            "total_items": len(weekly_data),
            "items": weekly_data,
        }, f, indent=2)
    sample = list(weekly_data.keys())[:3]
    print(f"  ✅ demand_weekly.json: {len(weekly_data)} items × {N_WEEKS} weeks")
    if dataset_name == "detailed":
        names = [weekly_data[s].get("name", s) for s in sample]
        print(f"     示例: {list(zip(sample, names))}")
    else:
        print(f"     示例: {sample}")

    # 2. 图拓扑
    print(f"\n[2/4] 生成图拓扑...")
    nodes, edges = _generate_graph()
    with open(data_dir / "graph_topology.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
    print(f"  ✅ graph_topology.json: {len(nodes)} 节点, {len(edges)} 条边")

    # 3. 品类-物品映射
    print(f"\n[3/4] 生成品类-物品映射...")
    category_items = {}
    for item_id, item in weekly_data.items():
        cat = item.get("category", "general")
        category_items.setdefault(cat, []).append(item_id)
    with open(data_dir / "item_catalog.json", "w") as f:
        json.dump(category_items, f, indent=2)
    print(f"  ✅ item_catalog.json: {dict((k, len(v)) for k, v in category_items.items())}")

    # 4. 仪表盘数据
    print(f"\n[4/4] 生成仪表盘数据...")
    _generate_dashboard_data(weekly_data, data_dir)

    # 统计
    total_size = sum(f.stat().st_size for f in data_dir.glob("*.json"))
    print(f"\n{'='*60}")
    print(f"✅ 数据集 '{dataset_name}' 完成!")
    print(f"   目录: {data_dir}")
    print(f"   总大小: {total_size / 1024:.1f} KB")
    print(f"   文件数: {len(list(data_dir.glob('*.json')))} 个")


def main():
    dataset_name = "standard"
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("--dataset", "-d"):
            if len(sys.argv) > 2:
                dataset_name = sys.argv[2]
            else:
                print("用法: python preprocess.py [--dataset standard|detailed]")
                print("       python preprocess.py --all")
                return
        elif arg == "--all":
            # 生成所有数据集
            for ds in ["standard", "detailed"]:
                generate_dataset(ds)
                print("\n")
            print("=" * 60)
            print("✅ 所有数据集已生成完成!")
            return
        else:
            dataset_name = arg

    generate_dataset(dataset_name)


if __name__ == "__main__":
    main()