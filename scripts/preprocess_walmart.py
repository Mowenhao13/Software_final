"""
Walmart 数据集预处理器
从 moviebrain01/walmart-demand-forecast 下载的真实 Walmart 销售数据
生成 12 个商品部门 × 156 周的需求时序

数据来源: https://huggingface.co/datasets/moviebrain01/walmart-demand-forecast
格式: Date,Weekly_Sales,ARIMA_Forecast,Prophet_Forecast,LSTM_Forecast

流程:
  1. 读取 Walmart 真实销售额曲线 (15 周)
  2. 周期循环 + 插值 → 156 周总需求基线
  3. 按部门分配比例 + ISOMORPH 噪声 → 各部门时序
  4. 各部门内细分商品生成
"""
import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
DATA_DIR = BASE_DIR / "data" / "walmart"
CSV_PATH = DATA_DIR / "forecast_results.csv"

N_WEEKS = 156
np.random.seed(2027)  # 不同种子区别于其他数据集

# Walmart 6 大部门配置
DEPARTMENTS = {
    "grocery": {
        "name": "食品杂货",
        "items": [
            ("WM001", "有机牛奶", "乳制品"),
            ("WM002", "进口牛肉", "肉类"),
            ("WM003", "冷冻披萨", "冷冻食品"),
            ("WM004", "休闲零食", "零食"),
            ("WM005", "瓶装饮料", "饮料"),
            ("WM006", "进口红酒", "酒类"),
        ],
        "sales_share": 0.30,   # 占总销售额 30%
        "ar_phi": 0.94,
        "burst_rate": 0.025,
    },
    "electronics": {
        "name": "电子用品",
        "items": [
            ("WM007", "液晶电视", "影音"),
            ("WM008", "蓝牙音箱", "影音"),
            ("WM009", "笔记本电脑", "电脑"),
            ("WM010", "无线耳机", "手机配件"),
            ("WM011", "充电宝", "手机配件"),
        ],
        "sales_share": 0.18,
        "ar_phi": 0.96,
        "burst_rate": 0.015,
    },
    "home": {
        "name": "家居用品",
        "items": [
            ("WM012", "记忆棉枕头", "床上用品"),
            ("WM013", "不锈钢锅具", "厨房用品"),
            ("WM014", "台灯", "灯具"),
            ("WM015", "收纳箱", "收纳"),
            ("WM016", "毛毯", "床上用品"),
        ],
        "sales_share": 0.16,
        "ar_phi": 0.93,
        "burst_rate": 0.02,
    },
    "apparel": {
        "name": "服装鞋帽",
        "items": [
            ("WM017", "纯棉T恤", "男装"),
            ("WM018", "牛仔裤", "男装"),
            ("WM019", "运动鞋", "鞋类"),
            ("WM020", "羽绒服", "女装"),
            ("WM021", "休闲帽", "配饰"),
            ("WM022", "真皮皮带", "配饰"),
        ],
        "sales_share": 0.18,
        "ar_phi": 0.92,
        "burst_rate": 0.03,
    },
    "sports": {
        "name": "运动户外",
        "items": [
            ("WM023", "瑜伽垫", "健身"),
            ("WM024", "哑铃套装", "健身"),
            ("WM025", "露营帐篷", "户外"),
            ("WM026", "保温杯", "户外"),
        ],
        "sales_share": 0.10,
        "ar_phi": 0.91,
        "burst_rate": 0.025,
    },
    "baby": {
        "name": "婴儿用品",
        "items": [
            ("WM027", "婴儿奶粉", "奶粉"),
            ("WM028", "纸尿裤", "尿布"),
            ("WM029", "婴儿湿巾", "护理"),
            ("WM030", "婴儿服饰", "童装"),
        ],
        "sales_share": 0.08,
        "ar_phi": 0.95,
        "burst_rate": 0.02,
    },
}


def _load_walmart_csv() -> np.ndarray:
    """读取 Walmart CSV，返回周销售额数组 (单位: 美元)"""
    if not CSV_PATH.exists():
        # 从下载的临时位置复制
        tmp = Path("/tmp/walmart_forecast.csv")
        if tmp.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(str(tmp), str(CSV_PATH))
        else:
            raise FileNotFoundError(f"Walmart CSV 不存在: {CSV_PATH}")

    sales = []
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sales.append(float(row["Weekly_Sales"]))
    return np.array(sales)


def _extend_to_156_weeks(sales_15: np.ndarray) -> np.ndarray:
    """将 15 周销售额扩展为 156 周"""
    # 周期循环 (15周*10=150周，再补6周)
    repeats = N_WEEKS // len(sales_15) + 1
    extended = np.tile(sales_15, repeats)[:N_WEEKS]

    # 添加年增长趋势 (~3% YoY)
    trend = 1.0 + 0.03 * np.arange(N_WEEKS) / 52
    extended = extended * trend

    # 添加小幅度随机波动
    noise = np.random.normal(0, extended * 0.02)
    return np.maximum(extended + noise, extended * 0.5)


def _department_sales(total_sales: np.ndarray, share: float) -> np.ndarray:
    """根据销售占比分配各部门周销售额 (美元)"""
    return total_sales * share


def _item_sales(dept_sales: np.ndarray, n_items: int, base_var: float = 0.15) -> np.ndarray:
    """将部门销售额按比例分配到各商品 (返回 n_items × N_WEEKS 矩阵)"""
    # 随机分配比例 (和为1)
    weights = np.random.dirichlet(np.ones(n_items) * 2)
    item_sales_mat = np.outer(weights, dept_sales)  # n_items × N_WEEKS

    # 各商品添加独立波动
    for i in range(n_items):
        noise = np.random.normal(0, item_sales_mat[i] * base_var)
        item_sales_mat[i] = np.maximum(item_sales_mat[i] + noise, item_sales_mat[i] * 0.3)

    return item_sales_mat


def _add_isomorph_components(
    base_signal: np.ndarray,
    ar_phi: float,
    burst_rate: float,
    item_id: str,
) -> np.ndarray:
    """在基础信号上叠加 ISOMORPH 5 分量噪声"""
    n = len(base_signal)

    # AR(1) 漂移 (百分比扰动)
    ar = np.zeros(n)
    ar[0] = np.random.randn() * 0.01
    for t in range(1, n):
        ar[t] = ar_phi * ar[t-1] + np.random.randn() * 0.008
    ar_component = base_signal * ar

    # 年季节性
    season = 0.08 * np.sin(2 * np.pi * np.arange(n) / 52)
    season_component = base_signal * season

    # 月季节性
    season_m = 0.04 * np.sin(2 * np.pi * np.arange(n) / 4.33)
    season_m_component = base_signal * season_m

    # 突发事件
    burst = np.zeros(n)
    burst_height = np.random.uniform(0.10, 0.25)  # 10-25% 暴增
    for t in range(n):
        if np.random.random() < burst_rate:
            burst[t] = burst_height * base_signal[t]
            for j in range(1, np.random.randint(2, 4)):
                if t + j < n:
                    burst[t + j] = burst[t] * max(0, 1 - j * 0.3)

    final = base_signal + ar_component + season_component + season_m_component + burst
    return np.maximum(final, base_signal * 0.2)  # 不低于基线的 20%


def _add_macro_shocks(weekly_data: dict):
    """添加全局宏观冲击"""
    all_ids = list(weekly_data.keys())
    shock_height = np.random.uniform(0.12, 0.30)
    shock_weeks = np.random.choice(N_WEEKS, size=8, replace=False)

    for week_idx in shock_weeks:
        target = np.random.choice(all_ids, size=max(1, int(len(all_ids) * 0.3)), replace=False)
        for item_id in target:
            item = weekly_data[item_id]
            d = np.array(item["weekly_demand"])
            d[week_idx] *= (1 + shock_height * (1 + np.random.random()))
            item["weekly_demand"] = d.tolist()


def generate_graph_topology():
    """生成 Walmart 供应链图拓扑"""
    # 基于 Walmart 实际配送网络
    nodes = [
        {"id": "Bentonville_HQ", "name": "Walmart HQ (AR)", "type": "warehouse", "region": "South",
         "coords": [-94.22, 36.37], "capacity": 2000},
        {"id": "DC_Midwest", "name": "Midwest DC (IN)", "type": "warehouse", "region": "Midwest",
         "coords": [-86.53, 39.77], "capacity": 1500},
        {"id": "DC_West", "name": "West Coast DC (CA)", "type": "warehouse", "region": "West",
         "coords": [-117.16, 32.72], "capacity": 1200},
        {"id": "DC_Southeast", "name": "Southeast DC (GA)", "type": "warehouse", "region": "Southeast",
         "coords": [-84.39, 33.75], "capacity": 1000},
        {"id": "DC_Northeast", "name": "Northeast DC (PA)", "type": "warehouse", "region": "Northeast",
         "coords": [-75.37, 40.91], "capacity": 1100},
        {"id": "DC_Texas", "name": "Texas DC (TX)", "type": "warehouse", "region": "South",
         "coords": [-96.80, 32.78], "capacity": 900},
        {"id": "Store_NY", "name": "NY Supercenter", "type": "store", "region": "Northeast",
         "coords": [-73.99, 40.76], "capacity": 500},
        {"id": "Store_LA", "name": "LA Supercenter", "type": "store", "region": "West",
         "coords": [-118.24, 34.05], "capacity": 600},
        {"id": "Store_CHI", "name": "Chicago Supercenter", "type": "store", "region": "Midwest",
         "coords": [-87.63, 41.88], "capacity": 550},
        {"id": "Store_ATL", "name": "Atlanta Supercenter", "type": "store", "region": "Southeast",
         "coords": [-84.39, 33.76], "capacity": 450},
        {"id": "Store_HOU", "name": "Houston Supercenter", "type": "store", "region": "South",
         "coords": [-95.37, 29.76], "capacity": 400},
        {"id": "Store_SEA", "name": "Seattle Supercenter", "type": "store", "region": "West",
         "coords": [-122.33, 47.61], "capacity": 350},
    ]

    edges = [
        {"from": "Bentonville_HQ", "to": "DC_Midwest", "travel_time_days": 2, "capacity_per_day": 500, "cost": 300, "mode": "road"},
        {"from": "Bentonville_HQ", "to": "DC_Texas", "travel_time_days": 2, "capacity_per_day": 400, "cost": 280, "mode": "road"},
        {"from": "DC_Midwest", "to": "Store_CHI", "travel_time_days": 1, "capacity_per_day": 300, "cost": 120, "mode": "road"},
        {"from": "DC_Midwest", "to": "DC_Northeast", "travel_time_days": 2, "capacity_per_day": 350, "cost": 200, "mode": "road"},
        {"from": "DC_Northeast", "to": "Store_NY", "travel_time_days": 1, "capacity_per_day": 280, "cost": 100, "mode": "road"},
        {"from": "DC_West", "to": "Store_LA", "travel_time_days": 1, "capacity_per_day": 350, "cost": 90, "mode": "road"},
        {"from": "DC_West", "to": "Store_SEA", "travel_time_days": 3, "capacity_per_day": 200, "cost": 350, "mode": "rail"},
        {"from": "DC_Southeast", "to": "Store_ATL", "travel_time_days": 1, "capacity_per_day": 250, "cost": 80, "mode": "road"},
        {"from": "DC_Southeast", "to": "DC_Northeast", "travel_time_days": 3, "capacity_per_day": 300, "cost": 280, "mode": "rail"},
        {"from": "DC_Texas", "to": "Store_HOU", "travel_time_days": 1, "capacity_per_day": 220, "cost": 90, "mode": "road"},
        {"from": "DC_Texas", "to": "DC_West", "travel_time_days": 4, "capacity_per_day": 250, "cost": 400, "mode": "rail"},
        {"from": "DC_Midwest", "to": "DC_West", "travel_time_days": 4, "capacity_per_day": 280, "cost": 380, "mode": "rail"},
        {"from": "DC_Midwest", "to": "DC_Southeast", "travel_time_days": 3, "capacity_per_day": 300, "cost": 250, "mode": "road"},
        {"from": "DC_Northeast", "to": "DC_Midwest", "travel_time_days": 2, "capacity_per_day": 320, "cost": 200, "mode": "road"},
        {"from": "Store_CHI", "to": "Store_NY", "travel_time_days": 4, "capacity_per_day": 100, "cost": 500, "mode": "rail"},
    ]

    return nodes, edges


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Walmart 数据集生成")
    print(f"  12 商品部门 × 30 种商品 × {N_WEEKS} 周")
    print(f"  数据源: moviebrain01/walmart-demand-forecast")
    print("=" * 60)

    # 1. 读取 Walmart 真实销售数据
    print("\n[1/5] 读取 Walmart 销售数据...")
    sales_15 = _load_walmart_csv()
    print(f"  原始数据: {len(sales_15)} 周, 均值 ${sales_15.mean():,.0f}")

    # 2. 扩展为 156 周
    print("\n[2/5] 扩展为 156 周周期...")
    total_sales = _extend_to_156_weeks(sales_15)
    print(f"  扩展后均值: ${total_sales.mean():,.0f}")

    # 3. 生成各部门商品需求
    print("\n[3/5] 生成各商品需求时序...")
    weekly_data = {}
    all_item_ids = []

    for dept_key, dept in DEPARTMENTS.items():
        dept_sales = _department_sales(total_sales, dept["sales_share"])
        n_items = len(dept["items"])
        item_sales_mat = _item_sales(dept_sales, n_items)

        for idx, (item_id, item_name, sub_cat) in enumerate(dept["items"]):
            base = item_sales_mat[idx]

            # 销售额 → 需求数量 (假设均价 $50)
            demand_qty = base / np.random.uniform(40, 80)

            # 叠加 ISOMORPH 噪声
            demand_signal = _add_isomorph_components(
                demand_qty, dept["ar_phi"], dept["burst_rate"], item_id
            )
            demand_signal = np.maximum(demand_signal, 10).tolist()

            weekly_data[item_id] = {
                "item_id": item_id,
                "name": item_name,
                "category": dept_key,
                "sub_category": sub_cat,
                "department": dept["name"],
                "base_demand": round(float(np.mean(demand_signal)), 1),
                "weekly_demand": [round(float(v), 2) for v in demand_signal],
            }
            all_item_ids.append(item_id)

        print(f"  {dept['name']}: {n_items} 种商品, 周均占比 {dept['sales_share']*100:.0f}%")

    # 4. 全局宏观冲击
    print("\n[4/5] 添加宏观冲击...")
    _add_macro_shocks(weekly_data)

    # 5. 写入 JSON
    print("\n[5/5] 写入数据文件...")

    with open(DATA_DIR / "demand_weekly.json", "w") as f:
        json.dump({"total_weeks": N_WEEKS, "total_items": len(weekly_data), "items": weekly_data}, f, indent=2)
    print(f"  ✅ demand_weekly.json: {len(weekly_data)} items × {N_WEEKS} weeks")

    # 品类映射
    category_items = {}
    dept_list = []
    for item_id, item in weekly_data.items():
        dept = item.get("category", "general")
        category_items.setdefault(dept, []).append(item_id)
        dept_list.append({
            "department": item.get("department", ""),
            "category": dept,
            "sub_category": item.get("sub_category", ""),
            "item_id": item_id,
            "name": item.get("name", ""),
        })
    with open(DATA_DIR / "item_catalog.json", "w") as f:
        json.dump(category_items, f, indent=2)
    print(f"  ✅ item_catalog.json: {len(category_items)} departments")

    with open(DATA_DIR / "department_catalog.json", "w") as f:
        json.dump(dept_list, f, indent=2)

    # 图拓扑
    nodes, edges = generate_graph_topology()
    with open(DATA_DIR / "graph_topology.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
    print(f"  ✅ graph_topology.json: {len(nodes)} nodes, {len(edges)} edges")

    # 品类分布
    cat_stats = {}
    for item_id, item in weekly_data.items():
        dept = item.get("category", "general")
        cat_stats.setdefault(dept, {"count": 0, "total_demand": 0, "name": item.get("department", "")})
        cat_stats[dept]["count"] += 1
        cat_stats[dept]["total_demand"] += sum(item["weekly_demand"][-52:])
    cat_dist = [
        {"category": k, "name": v["name"], "count": v["count"], "total_demand": round(v["total_demand"], 0)}
        for k, v in cat_stats.items()
    ]
    with open(DATA_DIR / "category_distribution.json", "w") as f:
        json.dump(cat_dist, f, indent=2)

    # 仪表盘数据
    from datetime import datetime, timedelta
    now = datetime.now()

    all_demand_recent = []
    for item_id, item in weekly_data.items():
        d = np.array(item["weekly_demand"])
        all_demand_recent.extend(d[-30:] if len(d) >= 30 else d)

    total_demand = int(np.sum(all_demand_recent))

    weekly_totals = np.zeros(N_WEEKS)
    for item_id, item in weekly_data.items():
        weekly_totals += np.array(item["weekly_demand"])
    recent_weekly_totals = weekly_totals[-30:] if N_WEEKS >= 30 else weekly_totals
    avg_weekly_total = float(np.mean(recent_weekly_totals))

    if len(recent_weekly_totals) >= 8:
        recent4 = np.mean(recent_weekly_totals[-4:])
        prev4 = np.mean(recent_weekly_totals[-8:-4])
        month_growth = round((recent4 - prev4) / prev4 * 100, 1) if prev4 > 0 else round(np.random.uniform(3.0, 10.0), 1)
    else:
        month_growth = round(np.random.uniform(3.0, 10.0), 1)

    kpi = {
        "total_orders": total_demand,
        "total_amount": round(total_demand * 0.1285, 2),
        "on_time_delivery_rate": round(93.0 + np.random.uniform(-2, 2), 1),
        "inventory_turnover": round(5.8 + np.random.uniform(-0.5, 0.5), 1),
        "active_suppliers": 22,
        "risk_count": np.random.randint(3, 8),
        "cost_total": round(total_demand * 0.085, 2),
        "month_growth": month_growth,
        "total_items": len(weekly_data),
        "avg_weekly_demand": round(avg_weekly_total, 0),
        "prediction_confidence": round(0.72 + np.random.uniform(-0.05, 0.10), 2),
    }
    with open(DATA_DIR / "kpi_snapshot.json", "w") as f:
        json.dump(kpi, f, indent=2)
    print(f"  ✅ kpi_snapshot.json")

    # 趋势
    trends = []
    for i in range(30):
        d = now - timedelta(days=29 - i)
        week_idx = max(0, min(51, 52 - 30 + i))
        wt = weekly_totals[week_idx] if week_idx < len(weekly_totals) else np.mean(weekly_totals)
        daily_orders = int(wt / 7 * (0.85 + np.random.random() * 0.3))
        unit_price = np.random.uniform(100, 160)
        trends.append({
            "date": d.strftime("%Y-%m-%d"),
            "orders": daily_orders,
            "amount": round(float(daily_orders * unit_price), 2),
            "cost": round(float(daily_orders * unit_price * np.random.uniform(0.55, 0.72)), 2),
        })
    with open(DATA_DIR / "trends.json", "w") as f:
        json.dump({"trends": trends}, f, indent=2)

    # 供应链地图
    carriers = ["Walmart_Logistics", "JB_Hunt", "Schneider", "Knight_Swift", "Werner"]
    statuses = ["in_transit", "delivered", "delayed", "pending"]
    node_coords = {n["id"]: n["coords"] for n in nodes}
    active_edges = np.random.choice(len(edges), size=max(1, int(len(edges) * 0.7)), replace=False)
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
    with open(DATA_DIR / "supply_chain_map.json", "w") as f:
        json.dump({
            "routes": map_routes,
            "total_in_transit": sum(1 for r in map_routes if r["status"] == "in_transit"),
            "total_delivered": sum(1 for r in map_routes if r["status"] == "delivered"),
            "total_delayed": sum(1 for r in map_routes if r["status"] == "delayed"),
            "total_pending": sum(1 for r in map_routes if r["status"] == "pending"),
        }, f, indent=2)

    # 保存原始 CSV
    import shutil
    shutil.copy("/tmp/walmart_forecast.csv", CSV_PATH)

    total_size = sum(f.stat().st_size for f in DATA_DIR.glob("*.json"))
    total_size += CSV_PATH.stat().st_size

    print(f"\n{'='*60}")
    print(f"✅ Walmart 数据集完成!")
    print(f"   目录: {DATA_DIR}")
    print(f"   商品: {len(weekly_data)} 种 (6 大部门)")
    print(f"   周数: {N_WEEKS} 周 (3 年)")
    print(f"   总大小: {total_size / 1024:.1f} KB")
    for dept_key, dept in DEPARTMENTS.items():
        print(f"     {dept['name']}: {len(dept['items'])} 种商品")


if __name__ == "__main__":
    main()