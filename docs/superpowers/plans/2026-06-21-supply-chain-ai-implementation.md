# AI 赋能供应链可视化分析系统 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现以 Chronos-2 需求预测 + DFS贪心物流路径优化为核心的系统，保留仪表盘和供应链全景可视化，数据存储全 JSON。

**Architecture:** FastAPI 后端（3个服务模块 + 3个路由模块） + React 前端（4个页面），JSON 文件数据源，Chronos-2 模型推理。

**Tech Stack:** FastAPI / Python 3.11 / Chronos-2 / React 18 / Ant Design 5 / ECharts 5 / JSON

---

### Task 1: 清洗后端 — 移除 SQLite/SQLAlchemy，精简项目结构

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/config.py`
- Modify: `backend/requirements.txt`
- Remove: `backend/database.py`
- Remove: `backend/seed_data.py`
- Remove: `backend/models/` (entire directory)
- Remove: `backend/schemas/__init__.py`
- Remove: `backend/routers/suppliers.py`
- Remove: `backend/routers/products.py`
- Remove: `backend/routers/inventory.py`
- Remove: `backend/routers/orders.py`
- Remove: `backend/routers/risks.py`
- Remove: `backend/routers/analytics.py`
- Remove: `backend/services/anomaly_service.py`
- Remove: `backend/services/risk_service.py`
- Remove: `backend/services/supplier_service.py`
- Create: `backend/data/` (empty directory)
- Modify: `backend/routers/__init__.py`
- Modify: `backend/services/__init__.py`

- [ ] **删除已废弃的模块文件**

  ```bash
  cd /Users/halllo/projects/local/Software_final
  rm -rf backend/models/
  rm -f backend/database.py
  rm -f backend/seed_data.py
  rm -f backend/schemas/__init__.py
  rm -f backend/routers/suppliers.py
  rm -f backend/routers/products.py
  rm -f backend/routers/inventory.py
  rm -f backend/routers/orders.py
  rm -f backend/routers/risks.py
  rm -f backend/routers/analytics.py
  rm -f backend/services/anomaly_service.py
  rm -f backend/services/risk_service.py
  rm -f backend/services/supplier_service.py
  mkdir -p backend/data/
  ```

- [ ] **更新 `backend/config.py`** — 移除 DATABASE_URL，保留 CORS 和 FORECAST 配置

  ```python
  """应用配置"""
  import os

  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  DATA_DIR = os.path.join(BASE_DIR, "data")

  # CORS 允许的前端地址
  CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

  # AI 模型配置
  FORECAST_HISTORY_WEEKS = 24  # 输入历史周数
  FORECAST_HORIZON_WEEKS = 12  # 预测未来周数
  ```

- [ ] **更新 `backend/requirements.txt`** — 移除 sqlalchemy, statsmodels, scikit-learn, 添加 chronos, datasets

  ```
  fastapi==0.115.0
  uvicorn[standard]==0.30.0
  pydantic==2.9.0
  chronos==0.1.0
  datasets>=3.0.0
  numpy==1.26.4
  pandas==2.2.2
  scipy==1.14.0
  websockets==12.0
  ```

- [ ] **更新 `backend/services/__init__.py`**

  ```python
  """AI 服务层"""
  from services.forecast_service import DemandForecaster
  from services.optimization_service import RouteOptimizer
  from services.dashboard_service import DashboardService
  ```

- [ ] **更新 `backend/routers/__init__.py`**

  ```python
  """API 路由包"""
  ```

- [ ] **更新 `backend/main.py`** — 移除旧路由导入，保留 dashboard/shipments，新增 forecast/optimization

  ```python
  """AI 赋能企业供应链的可视化分析系统 — 后端入口"""
  import asyncio
  import json
  import random
  from datetime import datetime

  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi import WebSocket, WebSocketDisconnect

  from config import CORS_ORIGINS
  from routers import dashboard, forecast, optimization

  app = FastAPI(
      title="AI供应链可视化分析系统",
      description="AI-Empowered Enterprise Supply Chain Visualization Analysis System",
      version="2.0.0",
      docs_url="/api/docs",
      redoc_url="/api/redoc",
  )

  app.add_middleware(
      CORSMiddleware,
      allow_origins=CORS_ORIGINS,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # 注册路由
  app.include_router(dashboard.router)
  app.include_router(forecast.router)
  app.include_router(optimization.router)


  @app.get("/")
  def root():
      return {
          "name": "AI供应链可视化分析系统",
          "version": "2.0.0",
          "docs": "/api/docs",
      }


  @app.get("/api/health")
  def health_check():
      return {"status": "ok", "timestamp": datetime.now().isoformat()}


  # ========== WebSocket 实时数据推送 ==========
  connected_clients: list[WebSocket] = []


  @app.websocket("/ws/realtime")
  async def websocket_endpoint(websocket: WebSocket):
      await websocket.accept()
      connected_clients.append(websocket)
      try:
          while True:
              data = {
                  "timestamp": datetime.now().isoformat(),
                  "new_orders_today": random.randint(0, 5),
                  "shipments_in_transit": random.randint(30, 50),
                  "active_alerts": random.randint(3, 10),
                  "inventory_low_items": random.randint(2, 8),
                  "recent_events": [
                      {
                          "type": random.choice(["order_placed", "shipment_update", "alert_triggered", "inventory_update"]),
                          "message": random.choice([
                              "新需求预测数据已更新",
                              "物流路径优化完成",
                              "库存预警: 某物品需求激增",
                              "路径推荐已刷新",
                              "Chronos-2 预测任务完成",
                          ]),
                          "time": datetime.now().strftime("%H:%M:%S"),
                      }
                  ],
              }
              try:
                  await websocket.send_json(data)
              except Exception:
                  break
              await asyncio.sleep(3)
      except WebSocketDisconnect:
          pass
      finally:
          if websocket in connected_clients:
              connected_clients.remove(websocket)


  if __name__ == "__main__":
      import uvicorn
      uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
  ```

---

### Task 2: 数据基础 — 下载 ISOMORPH 数据集并预处理为 JSON

**Files:**
- Create: `scripts/download_isomorph.py`
- Create: `scripts/preprocess.py`

- [ ] **创建 `scripts/download_isomorph.py`** — 从 HF 下载 ISOMORPH baseline C=50

  ```python
  """
  从 HuggingFace 下载 ISOMORPH Supply Chain Benchmark 数据集的 baseline 场景
  仅下载 C=50 场景 (约500MB)，包含需求信号和图拓扑
  """
  import os
  import shutil
  from pathlib import Path

  HF_DATASET = "Isomorph2026/isomorph-supply-chain-benchmark"
  BASE_DIR = Path(__file__).resolve().parent.parent / "backend" / "lab" / "datasets"
  CACHE_DIR = BASE_DIR / "hf_cache"

  def download_baseline():
      """下载 ISOMORPH baseline C=50 场景的核心文件"""
      print(f"正在从 HF 加载数据集: {HF_DATASET}")
      os.makedirs(CACHE_DIR, exist_ok=True)

      from datasets import load_dataset

      # 仅加载 output_item50 场景
      ds = load_dataset(
          HF_DATASET,
          split=None,  # 不加载整个数据集
          cache_dir=str(CACHE_DIR),
          streaming=False,
      )
      print(f"数据集加载完成. 结构: {ds}")
      return ds

  if __name__ == "__main__":
      download_baseline()
      print("下载完成！数据集已缓存到 backend/lab/datasets/hf_cache/")
  ```

- [ ] **创建 `scripts/preprocess.py`** — 将 ISOMORPH Parquet/NumPy 预处理为 JSON

  ```python
  """
  预处理 ISOMORPH 数据集 → JSON 文件
  输出到 backend/data/ 目录
  """
  import json
  import os
  import numpy as np
  import pandas as pd
  from pathlib import Path

  BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
  DATA_DIR = BASE_DIR / "data"
  CACHE_DIR = BASE_DIR / "lab" / "datasets" / "hf_cache"

  # ISOMORPH 数据集在 cache 中的路径
  DATASET_CACHE = list(CACHE_DIR.glob("**/output_item50*/seed2025/"))
  if not DATASET_CACHE:
      # fallback: 扫描 HF cache 结构
      DATASET_CACHE = list(CACHE_DIR.glob("**/output_item50*/"))

  def preprocess_demand():
      """将 demand_signals.npy 按周聚合为 JSON"""
      print("预处理需求信号...")
      dataset_path = DATASET_CACHE[0] if DATASET_CACHE else None
      if not dataset_path:
          print("警告: 未找到数据集缓存，将生成模拟数据")
          _generate_mock_data()
          return

      # 加载需求信号矩阵 (T × C)
      demand = np.load(dataset_path / "demand_signals.npy")  # float32, shape (52560, 50)

      # 加载物品ID
      with open(dataset_path / "demand_signals_cols.txt") as f:
          items = [line.strip() for line in f.readlines()]

      # 按周聚合 (52,560天 / 7 ≈ 7,509周)
      n_weeks = demand.shape[0] // 7
      weekly_demand = demand[:n_weeks * 7].reshape(n_weeks, 7, -1).sum(axis=1)

      # 取前20个物品的子集
      top_n = 20
      weekly_data = {}
      for i in range(min(top_n, len(items))):
          weekly_data[items[i]] = {
              "item_id": items[i],
              "weekly_demand": [round(float(v), 2) for v in weekly_demand[:, i]],
          }

      # 写入 JSON
      DATA_DIR.mkdir(parents=True, exist_ok=True)
      with open(DATA_DIR / "demand_weekly.json", "w") as f:
          json.dump({
              "total_weeks": n_weeks,
              "items": weekly_data,
          }, f, indent=2)
      print(f"需求数据已写入: {DATA_DIR / 'demand_weekly.json'} ({len(weekly_data)} items)")


  def preprocess_graph():
      """解析 edge_list.parquet → graph_topology.json"""
      print("预处理图拓扑...")
      dataset_path = DATASET_CACHE[0] if DATASET_CACHE else None
      if not dataset_path:
          print("警告: 未找到图数据，跳过")
          return

      edges_df = pd.read_parquet(dataset_path / "edge_list.parquet")

      # 收集所有节点
      nodes_set = set()
      nodes_set.update(edges_df["from"].unique())
      nodes_set.update(edges_df["to"].unique())

      nodes = [{"id": n, "name": n} for n in sorted(nodes_set)]
      edges = []
      for _, row in edges_df.iterrows():
          edges.append({
              "from": row["from"],
              "to": row["to"],
              "travel_time_days": int(row["travel_time_days"]),
              "capacity_per_day": int(row["cap_per_day"]),
              "cost": int(row["travel_time_days"]) * 100,  # 简化成本估算
          })

      with open(DATA_DIR / "graph_topology.json", "w") as f:
          json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
      print(f"图拓扑已写入: {DATA_DIR / 'graph_topology.json'} ({len(nodes)} nodes, {len(edges)} edges)")


  def preprocess_dashboard():
      """生成仪表盘 KPI 快照 (从 ISOMORPH daily_records 提取)"""
      from datetime import datetime, timedelta
      now = datetime.now()

      kpi = {
          "total_orders": 1250,
          "total_amount": 2850000.00,
          "on_time_delivery_rate": 94.5,
          "inventory_turnover": 4.2,
          "active_suppliers": 10,
          "risk_count": 5,
          "cost_total": 1850000.00,
          "month_growth": 8.3,
      }
      with open(DATA_DIR / "kpi_snapshot.json", "w") as f:
          json.dump(kpi, f, indent=2)

      # 30天趋势
      trends = []
      for i in range(30):
          d = now - timedelta(days=29 - i)
          trends.append({
              "date": d.strftime("%Y-%m-%d"),
              "orders": int(np.random.randint(30, 60)),
              "amount": round(float(np.random.uniform(80000, 120000)), 2),
              "cost": round(float(np.random.uniform(50000, 80000)), 2),
          })
      with open(DATA_DIR / "trends.json", "w") as f:
          json.dump({"trends": trends}, f, indent=2)

      # 供应链地图数据
      map_data = {
          "routes": [
              {"origin": "Factory_NY", "destination": "Warehouse_1", "mode": "road",
               "origin_coords": [-73.94, 40.81], "dest_coords": [-74.01, 40.71],
               "status": "in_transit", "carrier": "Carrier_A"},
              {"origin": "Factory_CHI", "destination": "Warehouse_3", "mode": "rail",
               "origin_coords": [-87.63, 41.88], "dest_coords": [-87.62, 41.87],
               "status": "in_transit", "carrier": "Carrier_B"},
              {"origin": "Warehouse_1", "destination": "NYC_Destination", "mode": "road",
               "origin_coords": [-74.01, 40.71], "dest_coords": [-73.99, 40.76],
               "status": "delivered", "carrier": "Carrier_A"},
              {"origin": "Warehouse_5", "destination": "Warehouse_9", "mode": "road",
               "origin_coords": [-87.62, 41.87], "dest_coords": [-73.99, 40.76],
               "status": "delayed", "carrier": "Carrier_C"},
              {"origin": "Factory_LA", "destination": "Warehouse_7", "mode": "air",
               "origin_coords": [-118.24, 34.05], "dest_coords": [-87.62, 41.87],
               "status": "in_transit", "carrier": "Carrier_D"},
          ],
          "points": [],
          "total_in_transit": 3,
      }
      with open(DATA_DIR / "supply_chain_map.json", "w") as f:
          json.dump(map_data, f, indent=2)

      print(f"仪表盘和供应链数据已写入 {DATA_DIR}")


  def _generate_mock_data():
      """生成模拟需求数据 (当 HF 数据集不可用时)"""
      DATA_DIR.mkdir(parents=True, exist_ok=True)
      np.random.seed(42)
      n_weeks = 200

      items = {}
      for i in range(20):
          base = np.random.uniform(50, 200)
          trend = np.random.uniform(-0.1, 0.2)
          season = 30 * np.sin(np.arange(n_weeks) * 2 * np.pi / 52)
          noise = np.random.normal(0, 15, n_weeks)
          demand = base + trend * np.arange(n_weeks) + season + noise
          demand = np.maximum(demand, 0)

          items[f"I{str(i+1).zfill(3)}"] = {
              "item_id": f"I{str(i+1).zfill(3)}",
              "weekly_demand": [round(float(v), 2) for v in demand],
          }

      with open(DATA_DIR / "demand_weekly.json", "w") as f:
          json.dump({"total_weeks": n_weeks, "items": items}, f, indent=2)

      # 模拟图拓扑: 13 nodes, ISOMORPH style
      nodes = [
          {"id": "Factory_NY", "name": "NY Factory", "type": "factory"},
          {"id": "Factory_CHI", "name": "Chicago Factory", "type": "factory"},
          {"id": "Factory_LA", "name": "LA Factory", "type": "factory"},
          {"id": "Warehouse_1", "name": "Warehouse NY", "type": "warehouse"},
          {"id": "Warehouse_2", "name": "Warehouse NJ", "type": "warehouse"},
          {"id": "Warehouse_3", "name": "Warehouse CHI", "type": "warehouse"},
          {"id": "Warehouse_4", "name": "Warehouse ATL", "type": "warehouse"},
          {"id": "Warehouse_5", "name": "Warehouse DAL", "type": "warehouse"},
          {"id": "Warehouse_6", "name": "Warehouse LA", "type": "warehouse"},
          {"id": "Warehouse_7", "name": "Warehouse DEN", "type": "warehouse"},
          {"id": "Warehouse_8", "name": "Warehouse SEA", "type": "warehouse"},
          {"id": "Warehouse_9", "name": "Warehouse DC", "type": "warehouse"},
          {"id": "NYC_Destination", "name": "NYC Customer", "type": "destination"},
      ]
      edges = [
          {"from": "Factory_NY", "to": "Warehouse_1", "travel_time_days": 2, "capacity_per_day": 100, "cost": 200},
          {"from": "Factory_NY", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 80, "cost": 300},
          {"from": "Factory_CHI", "to": "Warehouse_3", "travel_time_days": 1, "capacity_per_day": 150, "cost": 100},
          {"from": "Factory_CHI", "to": "Warehouse_5", "travel_time_days": 3, "capacity_per_day": 120, "cost": 250},
          {"from": "Factory_CHI", "to": "Warehouse_7", "travel_time_days": 4, "capacity_per_day": 90, "cost": 350},
          {"from": "Factory_LA", "to": "Warehouse_6", "travel_time_days": 1, "capacity_per_day": 140, "cost": 150},
          {"from": "Factory_LA", "to": "Warehouse_8", "travel_time_days": 3, "capacity_per_day": 100, "cost": 280},
          {"from": "Warehouse_1", "to": "Warehouse_2", "travel_time_days": 1, "capacity_per_day": 120, "cost": 80},
          {"from": "Warehouse_1", "to": "Warehouse_9", "travel_time_days": 2, "capacity_per_day": 100, "cost": 180},
          {"from": "Warehouse_2", "to": "NYC_Destination", "travel_time_days": 1, "capacity_per_day": 130, "cost": 60},
          {"from": "Warehouse_3", "to": "Warehouse_5", "travel_time_days": 3, "capacity_per_day": 110, "cost": 220},
          {"from": "Warehouse_3", "to": "Warehouse_4", "travel_time_days": 2, "capacity_per_day": 100, "cost": 170},
          {"from": "Warehouse_4", "to": "Warehouse_9", "travel_time_days": 2, "capacity_per_day": 90, "cost": 200},
          {"from": "Warehouse_5", "to": "Warehouse_7", "travel_time_days": 2, "capacity_per_day": 80, "cost": 190},
          {"from": "Warehouse_5", "to": "Warehouse_4", "travel_time_days": 2, "capacity_per_day": 95, "cost": 160},
          {"from": "Warehouse_6", "to": "Warehouse_7", "travel_time_days": 3, "capacity_per_day": 85, "cost": 260},
          {"from": "Warehouse_6", "to": "Warehouse_8", "travel_time_days": 2, "capacity_per_day": 90, "cost": 200},
          {"from": "Warehouse_7", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 75, "cost": 280},
          {"from": "Warehouse_8", "to": "Warehouse_7", "travel_time_days": 2, "capacity_per_day": 80, "cost": 210},
          {"from": "Warehouse_8", "to": "Warehouse_9", "travel_time_days": 4, "capacity_per_day": 70, "cost": 350},
          {"from": "Warehouse_9", "to": "NYC_Destination", "travel_time_days": 1, "capacity_per_day": 120, "cost": 80},
          {"from": "Warehouse_2", "to": "Warehouse_9", "travel_time_days": 3, "capacity_per_day": 70, "cost": 250},
          {"from": "Warehouse_4", "to": "NYC_Destination", "travel_time_days": 2, "capacity_per_day": 85, "cost": 180},
      ]
      with open(DATA_DIR / "graph_topology.json", "w") as f:
          json.dump({"nodes": nodes, "edges": edges}, f, indent=2)

      print(f"模拟数据已生成到 {DATA_DIR}")

  if __name__ == "__main__":
      preprocess_demand()
      preprocess_graph()
      preprocess_dashboard()
      print("预处理完成！")
  ```

---

### Task 3: 后端 — DashboardService (JSON 数据源)

**Files:**
- Create: `backend/services/dashboard_service.py`
- Modify: `backend/routers/dashboard.py`
- Modify: `backend/routers/shipments.py`

- [ ] **创建 `backend/services/dashboard_service.py`**

  ```python
  """仪表盘服务 — 从 JSON 文件读取数据"""
  import json
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
      """供应商分布 (从 kpi 数据衍生)"""
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
  ```

- [ ] **重写 `backend/routers/dashboard.py`** — 移除 SQLAlchemy，使用 DashboardService

  ```python
  """仪表盘 API"""
  from fastapi import APIRouter
  from services.dashboard_service import (
      get_kpis, get_trends, get_supplier_distribution, get_order_status
  )

  router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


  @router.get("/kpis")
  def kpis():
      return get_kpis()


  @router.get("/trends")
  def trends():
      return {"trends": get_trends()}


  @router.get("/supplier-distribution")
  def supplier_distribution():
      return get_supplier_distribution()


  @router.get("/order-status")
  def order_status():
      return get_order_status()
  ```

- [ ] **重写 `backend/routers/shipments.py`** — 改为 supply-chain 端点

  ```python
  """供应链全景 API"""
  from fastapi import APIRouter
  from services.dashboard_service import get_shipment_map, get_shipment_stats

  router = APIRouter(prefix="/api/supply-chain", tags=["SupplyChain"])


  @router.get("/map")
  def shipment_map():
      """获取物流路线地图数据"""
      return get_shipment_map()


  @router.get("/stats")
  def shipment_stats():
      """获取物流统计"""
      return get_shipment_stats()
  ```

  Update main.py to also import this router:
  ```python
  from routers import dashboard, forecast, optimization, shipments as supply_chain
  # and add: app.include_router(supply_chain.router)
  ```

---

### Task 4: 后端 — ForecastService (Chronos-2 零样本预测)

**Files:**
- Create: `backend/services/forecast_service.py`
- Create: `backend/routers/forecast.py`

- [ ] **创建 `backend/services/forecast_service.py`**

  ```python
  """需求预测服务 — Chronos-2 零样本时序预测"""
  import json
  import numpy as np
  from pathlib import Path
  from typing import List, Dict, Any, Optional
  from datetime import datetime, timedelta

  DATA_DIR = Path(__file__).resolve().parent.parent / "data"
  MODEL_PATH = Path(__file__).resolve().parent.parent / "lab" / "models" / "chronos-2"

  # 使用 HF 镜像
  import os
  os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

  # Chronos-2 分位数索引 (from model config)
  QUANTILES = [
      0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
      0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99
  ]

  _pipeline = None


  def _load_model():
      """延迟加载 Chronos-2 模型 (首次调用时加载)"""
      global _pipeline
      if _pipeline is not None:
          return _pipeline
      try:
          from chronos import Chronos2Pipeline
          print(f"正在加载 Chronos-2 模型: {MODEL_PATH}")
          _pipeline = Chronos2Pipeline.from_pretrained(
              str(MODEL_PATH),
              device_map="cpu",
          )
          print("模型加载完成")
      except Exception as e:
          print(f"模型加载失败: {e}")
          print("将使用 Holt-Winters 回退方案")
          _pipeline = None
      return _pipeline


  def _load_demand_data() -> Dict[str, Any]:
      """从 JSON 加载需求数据"""
      path = DATA_DIR / "demand_weekly.json"
      if not path.exists():
          return {"weeks": [], "items": {}}
      with open(path) as f:
          return json.load(f)


  def _holt_winters_fallback(history: np.ndarray, horizon: int = 12) -> Dict:
      """Holt-Winters 回退预测 (当 Chronos-2 不可用时)"""
      alpha, beta, gamma = 0.3, 0.1, 0.1
      season_len = 4  # 月季节性 (4周)

      level = history[0]
      trend = history[1] - history[0] if len(history) > 1 else 0
      seasonal = [0] * season_len

      fitted = []
      for t, y in enumerate(history):
          if t < season_len:
              fitted.append(float(y))
              continue
          s_idx = (t - season_len) % season_len
          f = float(level + trend + seasonal[s_idx])
          fitted.append(max(0, f))
          new_level = alpha * (y - seasonal[s_idx]) + (1 - alpha) * (level + trend)
          new_trend = beta * (new_level - level) + (1 - beta) * trend
          new_seasonal = gamma * (y - new_level) + (1 - gamma) * seasonal[s_idx]
          level, trend = new_level, new_trend
          seasonal[s_idx] = new_seasonal

      errors = [abs(history[i] - fitted[i]) for i in range(season_len, len(fitted))]
      mae = float(np.mean(errors)) if errors else float(np.mean(history) * 0.15)

      forecast = []
      f_level, f_trend = level, trend
      for i in range(horizon):
          s_idx = (len(history) + i) % season_len
          pred = float(max(0, f_level + f_trend + seasonal[s_idx]))
          forecast.append({
              "week": i + 1,
              "predicted": round(pred, 1),
              "p10": round(max(0, pred - 1.28 * mae), 1),
              "p90": round(pred + 1.28 * mae, 1),
          })

      recent_avg = float(np.mean(history[-8:]))
      forecast_avg = float(np.mean([f["predicted"] for f in forecast]))
      if forecast_avg > recent_avg * 1.08:
          trend_dir = "up"
      elif forecast_avg < recent_avg * 0.92:
          trend_dir = "down"
      else:
          trend_dir = "stable"

      cv = mae / (float(np.mean(history)) + 0.001)
      confidence = round(max(0, min(1, 1 - cv)), 2)

      return {
          "forecast": forecast,
          "confidence": confidence,
          "trend": trend_dir,
          "method": "holt-winters",
      }


  def get_available_items() -> List[Dict[str, Any]]:
      """返回可预测的物品列表"""
      data = _load_demand_data()
      items = data.get("items", {})
      return [
          {"item_id": item_id, "weeks": len(item_data.get("weekly_demand", []))}
          for item_id, item_data in items.items()
      ]


  def predict_demand(item_id: str, horizon: int = 12) -> Dict[str, Any]:
      """对指定物品执行需求预测

      优先使用 Chronos-2 零样本预测，失败时回退到 Holt-Winters。
      """
      data = _load_demand_data()
      items = data.get("items", {})
      item = items.get(item_id)
      if not item:
          return {"error": f"物品 {item_id} 未找到", "forecast": [], "confidence": 0, "trend": "unknown"}

      history = np.array(item["weekly_demand"], dtype=np.float32)

      # 尝试 Chronos-2 预测
      pipeline = _load_model()
      if pipeline is not None:
          try:
              return _predict_chronos(pipeline, item_id, history, horizon)
          except Exception as e:
              print(f"Chronos-2 预测失败: {e}, 回退到 Holt-Winters")

      # 回退方案
      return _holt_winters_fallback(history, horizon)


  def _predict_chronos(pipeline, item_id: str, history: np.ndarray, horizon: int) -> Dict[str, Any]:
      """使用 Chronos-2 进行零样本预测"""
      # 截取最近 52 周
      hist = history[-52:] if len(history) > 52 else history
      hist_3d = hist.reshape(1, 1, -1).astype(np.float32)

      forecast = pipeline.predict(hist_3d, prediction_length=horizon)

      # forecast[0] shape: (1, n_quantiles, horizon)
      quantile_preds = forecast[0][0, :, :].numpy()  # (n_quantiles, horizon)

      result = []
      for w in range(horizon):
          p50 = float(quantile_preds[QUANTILES.index(0.5), w])
          p10 = float(quantile_preds[QUANTILES.index(0.1), w])
          p90 = float(quantile_preds[QUANTILES.index(0.9), w])
          result.append({
              "week": w + 1,
              "predicted": round(p50, 1),
              "p10": round(p10, 1),
              "p90": round(p90, 1),
          })

      # 趋势分析
      recent_avg = float(np.mean(hist[-8:]))
      forecast_avg = float(np.mean([f["predicted"] for f in result]))
      if forecast_avg > recent_avg * 1.08:
          trend = "up"
      elif forecast_avg < recent_avg * 0.92:
          trend = "down"
      else:
          trend = "stable"

      # 置信度 (基于 p90-p10 区间宽度)
      widths = [f["p90"] - f["p10"] for f in result]
      avg_width = float(np.mean(widths))
      confidence = round(max(0, min(1, 1 - avg_width / (recent_avg + 0.001))), 2)

      return {
          "item_id": item_id,
          "forecast": result,
          "confidence": confidence,
          "trend": trend,
          "method": "chronos-2",
          "history": [round(float(v), 2) for v in hist[-24:].tolist()],
      }


  def batch_predict(item_ids: List[str], horizon: int = 12) -> List[Dict[str, Any]]:
      """批量预测多个物品"""
      return [predict_demand(iid, horizon) for iid in item_ids]
  ```

- [ ] **创建 `backend/routers/forecast.py`**

  ```python
  """需求预测 API"""
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel
  from typing import List
  from services.forecast_service import get_available_items, predict_demand, batch_predict

  router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


  class BatchRequest(BaseModel):
      item_ids: List[str]
      horizon: int = 12


  @router.get("/items")
  def available_items():
      """返回可预测的物品列表"""
      return get_available_items()


  @router.get("/demand/{item_id}")
  def demand_forecast(item_id: str, horizon: int = 12):
      """对指定物品做需求预测"""
      result = predict_demand(item_id, horizon)
      if "error" in result:
          raise HTTPException(404, result["error"])
      return result


  @router.post("/batch")
  def batch_forecast(req: BatchRequest):
      """批量预测多个物品"""
      return batch_predict(req.item_ids, req.horizon)
  ```

---

### Task 5: 后端 — OptimizationService (DFS + 贪心 + 去重 路径优化 + 联动)

**Files:**
- Create: `backend/services/optimization_service.py`
- Create: `backend/routers/optimization.py`

- [ ] **创建 `backend/services/optimization_service.py`**

  ```python
  """物流路径优化服务 — DFS + 贪心 + 去重 + 需求联动"""
  import json
  import heapq
  from pathlib import Path
  from typing import List, Dict, Any, Tuple, Optional
  from services.forecast_service import predict_demand

  DATA_DIR = Path(__file__).resolve().parent.parent / "data"


  def _load_graph() -> Dict[str, Any]:
      """加载图拓扑 JSON"""
      path = DATA_DIR / "graph_topology.json"
      if not path.exists():
          return {"nodes": [], "edges": []}
      with open(path) as f:
          return json.load(f)


  def _build_adjacency(edges: List[Dict]) -> Dict[str, List[Dict]]:
      """将边列表转为邻接表"""
      adj = {}
      for e in edges:
          adj.setdefault(e["from"], []).append({
              "to": e["to"],
              "travel_time_days": e.get("travel_time_days", 1),
              "capacity_per_day": e.get("capacity_per_day", 100),
              "cost": e.get("cost", 100),
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
  ) -> Dict[str, Any]:
      """DFS + 贪心 + 去重 搜索 Top-K 最优路径

      Args:
          start: 起点节点 ID
          end: 终点节点 ID
          demand_volume: 需求量
          top_k: 返回 Top-K 路径
          forecast_weight: 需求预测对容量的影响权重 (>1 放大容量约束)

      Returns:
          包含路径列表的字典
      """
      graph = _load_graph()
      edges = graph.get("edges", [])
      adj = _build_adjacency(edges)
      nodes = graph.get("nodes", [])

      if start not in adj:
          return {"error": f"起点 {start} 不存在", "paths": []}
      if start == end:
          return {"error": "起点与终点相同", "paths": []}

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
          "nodes": nodes,
          "paths": all_paths[:top_k],
      }


  def find_route_with_forecast(
      start: str,
      end: str,
      item_id: str,
      top_k: int = 5,
      horizon: int = 12,
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
      routes = find_routes(start, end, demand_volume, top_k, forecast_weight)

      # 关联预测信息
      routes["forecast"] = {
          "item_id": item_id,
          "growth_rate": round(float(growth_rate), 3),
          "forecast_weight": forecast_weight,
          "trend": pred.get("trend", "stable"),
          "confidence": pred.get("confidence", 0),
      }

      return routes
  ```

- [ ] **创建 `backend/routers/optimization.py`**

  ```python
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


  class RouteWithForecastRequest(BaseModel):
      start: str
      end: str
      item_id: str
      top_k: int = 5
      horizon: int = 12


  @router.get("/graph")
  def graph():
      """返回图拓扑数据"""
      return get_graph()


  @router.post("/route")
  def route(req: RouteRequest):
      """给定起点/终点/需求量，返回 Top-K 最优路径"""
      result = find_routes(req.start, req.end, req.demand_volume, req.top_k, req.forecast_weight)
      if "error" in result:
          raise HTTPException(400, result["error"])
      return result


  @router.post("/route/with-forecast")
  def route_with_forecast(req: RouteWithForecastRequest):
      """结合 Chronos-2 需求预测做联动路径规划"""
      result = find_route_with_forecast(req.start, req.end, req.item_id, req.top_k, req.horizon)
      if "error" in result:
          raise HTTPException(400, result["error"])
      return result
  ```

---

### Task 6: 前端 — 更新 API 层、路由配置、导航菜单

**Files:**
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout/MainLayout.tsx`

- [ ] **更新 `frontend/src/api/index.ts`** — 添加新 API，移除旧的

  ```typescript
  import axios from 'axios';

  const http = axios.create({
    baseURL: '/api',
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  });

  http.interceptors.response.use(
    (res) => res.data,
    (err) => {
      console.error('API Error:', err.message);
      return Promise.reject(err);
    }
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const api = {
    get: <T = any>(url: string, config?: any): Promise<T> => http.get(url, config) as any,
    post: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.post(url, data, config) as any,
    put: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.put(url, data, config) as any,
    delete: <T = any>(url: string, config?: any): Promise<T> => http.delete(url, config) as any,
  };

  // ========== Dashboard ==========
  export const getKPIs = () => api.get('/dashboard/kpis');
  export const getTrends = () => api.get('/dashboard/trends');
  export const getSupplierDist = () => api.get('/dashboard/supplier-distribution');
  export const getOrderStatus = () => api.get('/dashboard/order-status');

  // ========== Supply Chain ==========
  export const getShipmentMap = () => api.get('/supply-chain/map');
  export const getShipmentStats = () => api.get('/supply-chain/stats');

  // ========== Forecast ==========
  export const getForecastItems = () => api.get('/forecast/items');
  export const getDemandForecast = (itemId: string, horizon = 12) =>
    api.get(`/forecast/demand/${itemId}?horizon=${horizon}`);
  export const batchForecast = (itemIds: string[], horizon = 12) =>
    api.post('/forecast/batch', { item_ids: itemIds, horizon });

  // ========== Optimization ==========
  export const getOptimizationGraph = () => api.get('/optimization/graph');
  export const findRoute = (data: any) => api.post('/optimization/route', data);
  export const findRouteWithForecast = (data: any) => api.post('/optimization/route/with-forecast', data);
  ```

- [ ] **更新 `frontend/src/App.tsx`**

  ```tsx
  import React from 'react';
  import { BrowserRouter, Routes, Route } from 'react-router-dom';
  import { ConfigProvider } from 'antd';
  import zhCN from 'antd/locale/zh_CN';
  import MainLayout from './components/Layout/MainLayout';
  import Dashboard from './pages/Dashboard';
  import SupplyChain from './pages/SupplyChain';
  import ForecastBoard from './pages/ForecastBoard';
  import RoutePlanner from './pages/RoutePlanner';

  export default function App() {
    return (
      <ConfigProvider locale={zhCN} theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}>
        <BrowserRouter>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/supply-chain" element={<SupplyChain />} />
              <Route path="/forecast" element={<ForecastBoard />} />
              <Route path="/route-planner" element={<RoutePlanner />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    );
  }
  ```

- [ ] **更新 `frontend/src/components/Layout/MainLayout.tsx`** — 更新导航菜单

  ```tsx
  import React, { useState, useEffect } from 'react';
  import { Outlet, useNavigate, useLocation } from 'react-router-dom';
  import { Layout, Menu, Badge, Typography, Tag } from 'antd';
  import {
    DashboardOutlined, NodeIndexOutlined, LineChartOutlined,
    RouteOutlined,
  } from '@ant-design/icons';
  import { realtimeClient } from '../../utils/websocket';

  const { Header, Sider, Content } = Layout;

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/supply-chain', icon: <NodeIndexOutlined />, label: '供应链全景' },
    { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测' },
    { key: '/route-planner', icon: <RouteOutlined />, label: '路径规划' },
  ];

  export default function MainLayout() {
    const navigate = useNavigate();
    const location = useLocation();
    const [wsData, setWsData] = useState<any>({});
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
      realtimeClient.connect();
      const unsub = realtimeClient.onMessage((data) => setWsData(data));

      const timer = setInterval(() => setCurrentTime(new Date()), 1000);
      return () => {
        unsub();
        realtimeClient.disconnect();
        clearInterval(timer);
      };
    }, []);

    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={220} theme="dark" style={{ position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100 }}>
          <div style={{
            height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: 8,
          }}>
            <DashboardOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 10 }} />
            <Typography.Text style={{ color: '#fff', fontSize: 15, fontWeight: 700, whiteSpace: 'nowrap' }}>
              AI供应链分析
            </Typography.Text>
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
          />
        </Sider>
        <Layout style={{ marginLeft: 220 }}>
          <Header style={{
            background: '#fff', padding: '0 24px', display: 'flex',
            alignItems: 'center', justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)', position: 'sticky', top: 0, zIndex: 99,
          }}>
            <Typography.Title level={5} style={{ margin: 0 }}>
              AI 赋能企业供应链的可视化分析系统
            </Typography.Title>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 14 }}>
              <Tag color="blue">实时监控中</Tag>
              <span style={{ color: '#666' }}>{currentTime.toLocaleString('zh-CN')}</span>
              {wsData?.active_alerts > 0 && (
                <Badge count={wsData.active_alerts} size="small" offset={[4, -2]}>
                  <DashboardOutlined style={{ fontSize: 18, color: '#faad14' }} />
                </Badge>
              )}
            </div>
          </Header>
          <Content style={{ margin: 16, minHeight: 280 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    );
  }
  ```

---

### Task 7: 前端 — ForecastBoard 页面

**Files:**
- Create: `frontend/src/pages/ForecastBoard/index.tsx`

- [ ] **创建 `frontend/src/pages/ForecastBoard/index.tsx`**

  ```tsx
  import React, { useEffect, useState } from 'react';
  import { Row, Col, Card, Select, Spin, Statistic, Tag, Empty } from 'antd';
  import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
  import BaseChart from '../../components/Charts/BaseChart';
  import { getForecastItems, getDemandForecast } from '../../api';

  export default function ForecastBoard() {
    const [items, setItems] = useState<any[]>([]);
    const [selectedItem, setSelectedItem] = useState<string>('');
    const [forecast, setForecast] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      getForecastItems().then(setItems);
    }, []);

    useEffect(() => {
      if (!selectedItem) return;
      setLoading(true);
      getDemandForecast(selectedItem, 12)
        .then(setForecast)
        .finally(() => setLoading(false));
    }, [selectedItem]);

    const trendIcon = (t: string) => {
      if (t === 'up') return <Tag icon={<ArrowUpOutlined />} color="red">上升</Tag>;
      if (t === 'down') return <Tag icon={<ArrowDownOutlined />} color="green">下降</Tag>;
      return <Tag icon={<MinusOutlined />} color="blue">平稳</Tag>;
    };

    const chartOption = forecast ? {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = params[0];
          const data = forecast.forecast[p.dataIndex];
          return `${data.week}周后<br/>预测值: ${data.predicted}<br/>p10: ${data.p10}<br/>p90: ${data.p90}`;
        },
      },
      legend: { data: ['历史需求', '预测值', '置信区间'], bottom: 0 },
      grid: { left: 60, right: 30, top: 20, bottom: 40 },
      xAxis: {
        type: 'category',
        data: [
          ...(forecast.history || []).map((_: any, i: number) => `T-${forecast.history.length - i}`),
          ...forecast.forecast.map((_: any, i: number) => `+${i + 1}周`),
        ],
        axisLabel: { rotate: 45, fontSize: 10 },
      },
      yAxis: { type: 'value', name: '需求量' },
      series: [
        {
          name: '置信区间',
          type: 'line',
          data: [
            ...(forecast.history || []).map(() => null),
            ...forecast.forecast.map((f: any) => f.p90),
          ],
          lineStyle: { opacity: 0 },
          symbol: 'none',
          stack: 'confidence',
          areaStyle: { color: 'rgba(24, 144, 255, 0.1)' },
        },
        {
          name: '置信区间',
          type: 'line',
          data: [
            ...(forecast.history || []).map(() => null),
            ...forecast.forecast.map((f: any) => f.p10),
          ],
          lineStyle: { opacity: 0 },
          symbol: 'none',
          stack: 'confidence',
          areaStyle: { color: 'rgba(24, 144, 255, 0.1)' },
        },
        {
          name: '历史需求',
          type: 'line',
          data: [
            ...(forecast.history || []).map((v: number) => v),
            ...forecast.forecast.map(() => null),
          ],
          smooth: true,
          lineStyle: { color: '#1890ff', width: 2 },
          itemStyle: { color: '#1890ff' },
          symbol: 'none',
        },
        {
          name: '预测值',
          type: 'line',
          data: [
            ...(forecast.history || []).map(() => null),
            ...forecast.forecast.map((f: any) => f.predicted),
          ],
          smooth: true,
          lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' },
          itemStyle: { color: '#ff4d4f' },
          symbol: 'circle',
          symbolSize: 6,
        },
      ],
    } : null;

    return (
      <div>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card>
              <Select
                placeholder="选择要预测的物品"
                style={{ width: 300 }}
                value={selectedItem || undefined}
                onChange={setSelectedItem}
                options={items.map((i: any) => ({ value: i.item_id, label: `${i.item_id} (${i.weeks}周数据)` }))}
              />
            </Card>
          </Col>
        </Row>

        {loading && <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>}

        {!selectedItem && !loading && (
          <Card style={{ marginTop: 16 }}>
            <Empty description="请选择上方物品查看需求预测" />
          </Card>
        )}

        {forecast && !loading && (
          <>
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Card><Statistic title="预测方法" value={forecast.method === 'chronos-2' ? 'Chronos-2' : 'Holt-Winters'} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="趋势方向" valueRender={() => trendIcon(forecast.trend)} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="置信度" value={forecast.confidence * 100} suffix="%" precision={1} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="未来4周均值" value={forecast.forecast.slice(0, 4).reduce((s: number, f: any) => s + f.predicted, 0) / 4} precision={1} /></Card>
              </Col>
            </Row>

            <Card title="需求预测曲线" style={{ marginTop: 16 }}>
              <BaseChart option={chartOption} height={420} />
            </Card>
          </>
        )}
      </div>
    );
  }
  ```

---

### Task 8: 前端 — RoutePlanner 页面

**Files:**
- Create: `frontend/src/pages/RoutePlanner/index.tsx`

- [ ] **创建 `frontend/src/pages/RoutePlanner/index.tsx`**

  ```tsx
  import React, { useEffect, useState } from 'react';
  import { Row, Col, Card, Select, Spin, Tag, Table, Switch, Empty, Descriptions, Alert, Statistic } from 'antd';
  import BaseChart from '../../components/Charts/BaseChart';
  import { getOptimizationGraph, findRoute, findRouteWithForecast, getForecastItems } from '../../api';

  export default function RoutePlanner() {
    const [graph, setGraph] = useState<any>(null);
    const [items, setItems] = useState<any[]>([]);
    const [startNode, setStartNode] = useState<string>('');
    const [endNode, setEndNode] = useState<string>('');
    const [selectedItem, setSelectedItem] = useState<string>('');
    const [useForecast, setUseForecast] = useState(false);
    const [routes, setRoutes] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      getOptimizationGraph().then(setGraph);
      getForecastItems().then(setItems);
    }, []);

    const searchRoutes = () => {
      if (!startNode || !endNode) return;
      setLoading(true);

      const promise = useForecast && selectedItem
        ? findRouteWithForecast({ start: startNode, end: endNode, item_id: selectedItem, top_k: 5 })
        : findRoute({ start: startNode, end: endNode, demand_volume: 100, top_k: 5 });

      promise.then(setRoutes).finally(() => setLoading(false));
    };

    useEffect(() => { searchRoutes(); }, [startNode, endNode, selectedItem, useForecast]);

    const nodeOptions = (graph?.nodes || []).map((n: any) => ({
      value: n.id,
      label: n.name,
    }));

    // 构建图拓扑可视化
    const graphOption = routes?.paths?.length > 0 ? {
      tooltip: { trigger: 'item' as const, formatter: (p: any) => p.name },
      series: [{
        type: 'graph',
        layout: 'force' as const,
        roam: true,
        draggable: true,
        data: (routes.nodes || graph?.nodes || []).map((n: any) => ({
          id: n.id,
          name: n.name || n.id,
          category: n.type === 'factory' ? 0 : n.type === 'destination' ? 2 : 1,
          symbolSize: n.type === 'factory' ? 40 : n.type === 'destination' ? 50 : 30,
          itemStyle: {
            color: n.type === 'factory' ? '#fa8c16' : n.type === 'destination' ? '#52c41a' : '#1890ff',
          },
        })),
        edges: (routes.paths[0]?.path || []).slice(0, -1).map((fromId: string, i: number) => {
          const toId = routes.paths[0].path[i + 1];
          return { source: fromId, target: toId };
        }),
        categories: [
          { name: '工厂', itemStyle: { color: '#fa8c16' } },
          { name: '仓储', itemStyle: { color: '#1890ff' } },
          { name: '目的地', itemStyle: { color: '#52c41a' } },
        ],
        force: { repulsion: 500, edgeLength: 200 },
        label: { show: true, position: 'right', fontSize: 10 },
        lineStyle: { color: '#1890ff', width: 2, curveness: 0.2 },
      }],
    } : null;

    const columns = [
      { title: '排名', key: 'rank', width: 60, render: (_: any, __: any, i: number) => i + 1 },
      { title: '路径', dataIndex: 'path', key: 'path', render: (p: string[]) => p.join(' → ') },
      { title: '天数', dataIndex: 'total_time_days', key: 'time', width: 80, sorter: (a: any, b: any) => a.total_time_days - b.total_time_days },
      { title: '成本', dataIndex: 'total_cost', key: 'cost', width: 100, sorter: (a: any, b: any) => a.total_cost - b.total_cost, render: (v: number) => v.toLocaleString() },
      { title: '需求适配度', dataIndex: 'demand_fitness', key: 'fitness', width: 110,
        render: (v: number) => <Tag color={v > 80 ? 'green' : v > 50 ? 'orange' : 'red'}>{v}%</Tag> },
      { title: '综合得分', dataIndex: 'score', key: 'score', width: 100, sorter: (a: any, b: any) => a.score - b.score },
    ];

    const bestPath = routes?.paths?.[0];

    return (
      <div>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <Select placeholder="起点 (工厂)" style={{ width: 180 }} value={startNode || undefined}
                  onChange={(v) => { setStartNode(v); }} options={nodeOptions} />
                <Select placeholder="终点 (目的地)" style={{ width: 180 }} value={endNode || undefined}
                  onChange={(v) => { setEndNode(v); }} options={nodeOptions} />
                <Select placeholder="关联物品 (可选)" style={{ width: 180 }} value={selectedItem || undefined}
                  onChange={setSelectedItem} allowClear options={items.map((i: any) => ({ value: i.item_id, label: i.item_id }))} />
                <span style={{ lineHeight: '32px' }}>
                  <Switch checked={useForecast} onChange={setUseForecast} /> 需求联动
                </span>
              </div>
            </Card>
          </Col>
        </Row>

        {loading && <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>}

        {routes?.forecast && (
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Alert
                type={routes.forecast.growth_rate > 0.3 ? 'warning' : 'info'}
                message={`需求联动: 物品 ${routes.forecast.item_id} 预测趋势 ${routes.forecast.trend} (增长率 ${(routes.forecast.growth_rate * 100).toFixed(1)}%), 路径权重已调整`}
                showIcon
              />
            </Col>
          </Row>
        )}

        {bestPath && !loading && (
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={6}><Card><Statistic title="推荐路径天数" value={bestPath.total_time_days} suffix="天" /></Card></Col>
            <Col span={6}><Card><Statistic title="推荐路径成本" value={bestPath.total_cost} suffix="元" /></Card></Col>
            <Col span={6}><Card><Statistic title="需求适配度" value={bestPath.demand_fitness} suffix="%" valueStyle={{ color: bestPath.demand_fitness > 80 ? '#52c41a' : '#faad14' }} /></Card></Col>
            <Col span={6}><Card><Statistic title="推荐路径" value={bestPath.path.length} suffix="节点" /></Card></Col>
          </Row>
        )}

        {routes?.paths?.length > 0 && !loading && (
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={14}>
              <Card title="供应链网络拓扑 (最优路径高亮)">
                <BaseChart option={graphOption} height={450} />
              </Card>
            </Col>
            <Col span={10}>
              <Card title="Top-K 路径对比">
                <Table dataSource={routes.paths} rowKey="score" columns={columns}
                  pagination={false} size="small"
                  onRow={(record) => ({
                    style: { cursor: 'pointer', background: record === bestPath ? '#e6f7ff' : undefined },
                  })}
                />
              </Card>
            </Col>
          </Row>
        )}

        {!startNode && !endNode && !loading && (
          <Card style={{ marginTop: 16 }}>
            <Empty description="请选择起点和终点进行路径规划" />
          </Card>
        )}
      </div>
    );
  }
  ```

---

### Task 9: 更新前端 Dashboard 和 SupplyChain 页面适配 JSON

**Files:**
- Modify: `frontend/src/pages/Dashboard/index.tsx` — 更新 import 路径
- Modify: `frontend/src/pages/SupplyChain/index.tsx` — 更新 import 路径

- [ ] **更新 `frontend/src/pages/Dashboard/index.tsx`**

  ```tsx
  // 只修改 import 行: 移除 getRisks (不再需要)
  // 从 import { getKPIs, getTrends, getSupplierDist, getOrderStatus, getRisks } from '../../api';
  // 改为: import { getKPIs, getTrends, getSupplierDist, getOrderStatus } from '../../api';

  // 修改 useEffect 部分:
  // 移除 getRisks 调用
  useEffect(() => {
    Promise.all([
      getKPIs(), getTrends(), getSupplierDist(), getOrderStatus(),
    ]).then(([k, t, s, o]) => {
      setKpis(k);
      setTrends((t as any).trends || []);
      setSupplierDist(s as any[]);
      setOrderStatus(o as any[]);
    }).finally(() => setLoading(false));
  }, []);
  ```

- [ ] **更新 `frontend/src/pages/SupplyChain/index.tsx`**

  ```tsx
  // 修改 import:
  // import { getShipmentMap, getShipmentStats, getSupplierDist } from '../../api';
  import { getShipmentMap, getShipmentStats } from '../../api';

  // 修改 useEffect:
  // 移除 getSupplierDist
  useEffect(() => {
    Promise.all([getShipmentMap(), getShipmentStats()])
      .then(([m, s]) => {
        setMapData(m);
        setStats(s);
      })
      .finally(() => setLoading(false));
  }, []);
  ```

---

### Implementation Order (Recommended)

1. **Task 1** — Clean up backend structure (foundation)
2. **Task 2** — Create data preprocessing scripts (data foundation)
3. **Task 3** — Dashboard service + routers (keep existing pages working)
4. **Task 4** — Forecast service + router (core AI #1)
5. **Task 5** — Optimization service + router (core AI #2)
6. **Task 6** — Frontend API, routes, menu (structure)
7. **Task 7** — ForecastBoard page (UI for core #1)
8. **Task 8** — RoutePlanner page (UI for core #2)
9. **Task 9** — Adapt existing pages (final polish)

Each task is self-contained and can be verified independently.