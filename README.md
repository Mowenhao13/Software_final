# AI 赋能企业供应链的可视化分析系统

基于 AI 技术（Chronos-2 / Moirai 时序大模型 + 图论路径优化）的企业供应链智能分析与可视化平台。核心聚焦两大能力：**供货需求预测**与**物流路径优化**，并通过预测结果动态影响路径决策，实现 AI 驱动的供应链智能优化。

## 选题背景

企业供应链管理面临需求波动大、物流路径复杂、多目标权衡困难等挑战。本系统利用 AI 技术对供应链全流程数据进行智能分析：

- **供货需求预测**：基于 ISOMORPH 风格仿真数据集（50 物品 × 7500 周），使用 Amazon Chronos-2 或 Salesforce Moirai-Small 时序大模型进行零样本需求预测，输出未来数周的需求量、置信区间、波动率与趋势方向。
- **物流路径优化**：将供应链网络建模为有向图（13 节点 23 边），采用 DFS + 贪心 + 去重算法，在运输时间、物流成本、边容量、运输方式等多因素约束下寻找 Top-K 最优路径。
- **AI 联动决策**：需求预测结果动态影响路径权重——预测到需求激增时自动提升容量权重、排除瓶颈边，实现"预测驱动的路径选择"。

## 技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                    前端 (React 18)                            │
│   Ant Design 5  │  ECharts 5  │  API (axios)                │
│                                                              │
│   📊 仪表盘    🗺️ 供应链全景    📈 需求预测    🚚 路径规划    │
├──────────────────────────────────────────────────────────────┤
│                  后端 API (FastAPI)                           │
│   dashboard  │  supply-chain  │  forecast  │  optimization   │
├──────────────────────────────────────────────────────────────┤
│                      AI 引擎                                  │
│   Chronos-2 (单变量, ~200M)  │  Moirai-Small (多变量, 117M)  │
│   Lag-Llama (协变量, ~50M, 需安装包)  │  规划算法             │
├──────────────────────────────────────────────────────────────┤
│               数据存储 (JSON 文件)                             │
│   demand_weekly.json (50×7500)  │  graph_topology.json       │
│   category_distribution.json  │  item_catalog.json            │
└──────────────────────────────────────────────────────────────┘
```

## 功能模块

| 模块 | 说明 |
|------|------|
| 📊 **仪表盘** | 8 项 KPI 指标卡片、30 天趋势图、5 品类分布饼图/柱状图、Top 10 物品需求对比、50 物品汇总表、月环比增长 |
| 🗺️ **供应链全景** | 物流路线地图、在途状态追踪、运输方式统计（16 条动态生成路由） |
| 📈 **需求预测看板** | 多模型切换（Chronos-2/Moirai）、52 周历史+12 周预测曲线、置信区间带状、历史分布直方图、逐周明细表含可视化条、品类对比、波动率 CV |
| 🚚 **物流路径规划** | 13 节点供应链图拓扑可视化、运输方式过滤、物品品类匹配、需求联动路径推荐、Top-K 路径对比表 |

## AI 能力详解

### 1. 供货需求预测（时序大模型）

**数据来源**：ISOMORPH 风格仿真生成器（50 物品 × 7500 周），5 分量需求信号叠加：
- AR(1) 漂移 + 年季节性(52 周) + 月季节性(4.33 周) + 突发事件 + 宏观冲击

**可用模型**：

| 模型 | 类型 | 参数 | 磁盘 | 本机支持 | 说明 |
|------|------|------|------|---------|------|
| **Chronos-2** | 单变量零样本 | ~200M | 456MB | ✅ 已集成 | 21 分位数输出, context=8192 |
| **Moirai-Small** | 多变量 | **117M** | **447MB** | ✅ **已集成** | 支持多序列联合预测 |
| **Lag-Llama** | 单变量+协变量 | ~50M | 28.1MB | ⚠️ 包需安装 | 支持已知未来协变量 |

**预测流程**：

```
ISOMORPH 风格仿真数据 (50物品 × 7500周)
      │
      ▼  preprocess.py
demand_weekly.json (周聚合需求矩阵)
      │
      ▼  Chronos-2 / Moirai 零样本推理
预测输出: p10 / p50 / p90 分位数, 置信区间, 趋势方向, 波动率
      │
      ▼  API /forecast/demand/{item_id}?model=chronos-2|moirai|auto
前端: 折线图 + 置信带 + 分布直方图 + 逐周明细表
```

**模型切换**：`GET /api/forecast/demand/{item_id}?model=chronos-2` — 支持 `auto` / `chronos-2` / `moirai`

**前端展示**（全面升级）：
- 6 项 KPI 卡片（近 4 周vs预测、置信度进度条、波动率 CV、品类对比、增长趋势%、历史极值）
- ECharts 主曲线：52 周历史（实线）+ 12 周预测（虚线）+ 置信区间带状
- 历史分布直方图 + 52 周历史概览柱状图 + 品类对比面板
- 逐周预测明细表（含置信区间可视化条）
- 模型快捷切换 Segmented 控件

---

### 2. 物流路径优化（DFS + 贪心 + 去重 图模型）

**图模型构建**：有向图 G = (N, E)：

```
N = {factory_A, factory_B, factory_C,       ← 3 个工厂（源节点）
     warehouse_1 ~ warehouse_9,             ← 9 个仓储（中转节点）
     NYC_destination}                       ← 1 个终点（需求方）

E = 23 条有向边，每条边包含：
  - travel_time_days   → 通行天数
  - capacity_per_day   → 日通行容量
  - cost               → 运输成本
  - mode               → 运输方式 (road / rail / air)
```

**路径搜索算法**：

```
算法: Weighted Greedy DFS (start, end, demand_volume, mode?)

1. 初始化栈: stack = [(start, [start], 累计时间, 累计成本, 容量惩罚)]
2. while stack 非空:
   a. 弹出栈顶，若到达终点 → 记录路径及综合得分
   b. 遍历当前节点出边:
      - 去重检查: 若 neighbor 已在 path 中 → 跳过
      - 容量检查: 若 demand > capacity → 叠加 capacity_penalty
      - transport mode 过滤: 仅匹配指定运输方式的边
3. 综合评分排序:
   score = w1 × (time归一化) + w2 × (cost归一化) + w3 × (容量惩罚归一化)
   默认权重: w1=0.35, w2=0.35, w3=0.30
4. 返回 Top-K 最优路径 (K=5)
```

**多目标权衡因素**：

| 因素 | 说明 | 权重 |
|------|------|------|
| 运输时间 | 货物从源到目的地的总通行天数 | 35% |
| 物流成本 | 路径上所有边的运输成本之和 | 35% |
| 容量适配 | 路径能否承载当前需求量，超载产生惩罚 | 30% |
| 运输方式 | 可选 road / rail / air 过滤 | 筛选条件 |

---

### 3. 需求预测与路径优化的 AI 联动（核心亮点）

系统将需求预测模块的输出作为路径优化的输入权重因子，实现"预测驱动的路径选择"：

```
Chronos-2 预测: 物品 I001 下月需求增长 45%
          │
          ▼
联动规则引擎:
  ├─ 增长率 > 30%  → 调高 w3 (容量权重) 从 0.30 → 0.50
  ├─ 增长率 > 50%  → 强制排除容量不足的瓶颈边（硬约束）
  └─ 增长率 < -20% → 调低 w3，偏向成本最低路径
          │
          ▼
路径搜索重新执行 → 返回适配高需求场景的最优路径
          │
          ▼
每条路径标注"需求适配度"得分 (0~100%)
```

**联动 API**：`POST /api/optimization/route/with-forecast` — 接收物品 ID，自动执行预测 → 联动 → 路径优化三步，返回一体化结果。

**前端交互**：需求联动开关 + 运输方式过滤 + 物品品类匹配展示

---

## 数据规模

| 指标 | 值 |
|------|-----|
| 物品数 | **50 种**（5 品类 × 10 种） |
| 时间跨度 | **7500 周**（~144 年仿真数据） |
| 总数据点 | **375,000** 个需求值 |
| 数据大小 | ~5.8MB（7 个 JSON 文件） |
| 图拓扑 | 13 节点 + 23 条边（含运输方式属性） |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | React 18 + TypeScript |
| UI 组件库 | Ant Design 5 |
| 图表库 | ECharts 5 |
| 后端框架 | FastAPI (Python 3.11+) |
| AI 模型 | Chronos-2 (~200M) / Moirai-Small (117M) / Lag-Llama (~50M) |
| 路径算法 | DFS + 贪心 + 去重（Python 原生实现） |
| 数据存储 | JSON 文件（`backend/data/`） |
| 数据生成 | ISOMORPH 风格仿真（5 分量需求信号叠加） |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 9+
- **本机环境**: Apple M4 + 16GB RAM（所有模型 CPU 推理可用）
- 磁盘空间：~1.5GB（模型 ~900MB + 数据 ~6MB）

### 1. 安装后端依赖

```bash
cd backend
uv venv
uv pip install -r requirements.txt
uv pip install chronos-forecasting uni2ts
```

### 2. 生成数据

```bash
cd scripts
python preprocess.py           # 生成 ISOMORPH 风格数据 → backend/data/
```

### 3. 下载模型

模型文件存放于 `backend/lab/models/`，使用 HuggingFace `huggingface_hub` 下载：

```bash
pip install huggingface_hub
```

#### Chronos-2（必需，456MB）

```python
from huggingface_hub import snapshot_download
# 或使用 hf 命令行: hf download amazon/chronos-2 --local-dir backend/lab/models/chronos-2
snapshot_download("amazon/chronos-2", local_dir="backend/lab/models/chronos-2")
```

#### Moirai-Small（可选，支持多变量预测，447MB）

```python
from huggingface_hub import snapshot_download
snapshot_download("salesforce/moirai-moe-1.0-r-small", local_dir="backend/lab/models/moirai-small")
```

#### Lag-Llama（可选，支持协变量预测，28MB）

```python
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id="time-series-foundation-models/lag-llama",
    filename="lag-llama.ckpt",
    local_dir="backend/lab/models/lag-llama",
)
# 安装 Lag-Llama 包（需 GitHub 访问）:
# git clone https://github.com/time-series-foundation-models/lag-llama.git
# pip install ./lag-llama
```

> 如果下载缓慢，可设置 HF 镜像：`export HF_ENDPOINT=https://hf-mirror.com`

### 4. 启动后端

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端运行在 http://localhost:8000
- API 文档： http://localhost:8000/api/docs

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## API 概览

### 仪表盘

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/dashboard/kpis` | GET | 核心 KPI 指标（总订单、在途量、物品数、月增长等） |
| `/api/dashboard/trends` | GET | 30 天趋势数据 |
| `/api/dashboard/supplier-distribution` | GET | 供应商地区分布 |
| `/api/dashboard/order-status` | GET | 订单状态分布 |
| `/api/dashboard/category-distribution` | GET | 品类分布（5 品类的物品数和总需求） |
| `/api/dashboard/items-summary` | GET | 50 物品详细统计（周均/标准差/最新值） |
| `/api/dashboard/item-catalog` | GET | 物品-品类映射 |

### 需求预测

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/forecast/models` | GET | 可用模型列表（含状态） |
| `/api/forecast/items` | GET | 可预测的物品列表 |
| `/api/forecast/demand/{item_id}` | GET | 需求预测（支持 `model=auto/chronos-2/moirai`，返回历史统计） |
| `/api/forecast/history/{item_id}` | GET | 历史需求数据（支持 `weeks` 参数） |
| `/api/forecast/batch` | POST | 批量预测多个物品 |

### 物流路径优化

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/optimization/graph` | GET | 图拓扑数据（节点 + 边含运输方式属性） |
| `/api/optimization/route` | POST | 路径搜索（支持 `mode` 运输方式过滤） |
| `/api/optimization/route/with-forecast` | POST | 需求联动路径规划 |

### 供应链

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/supply-chain/map` | GET | 物流地图数据（16 条动态路由） |
| `/api/supply-chain/stats` | GET | 在途/延迟/已送达统计 |

## 项目结构

```
supply-chain-analytics/
├── backend/
│   ├── main.py                      # FastAPI 入口
│   ├── config.py                    # 应用配置
│   ├── data/                        # JSON 数据存储
│   │   ├── demand_weekly.json       # 50物品×7500周需求时序
│   │   ├── graph_topology.json      # 13节点23边图拓扑
│   │   ├── kpi_snapshot.json        # 仪表盘 KPI 快照
│   │   ├── category_distribution.json  # 品类分布
│   │   ├── item_catalog.json        # 物品-品类映射
│   │   ├── supply_chain_map.json    # 供应链地图（动态生成）
│   │   ├── trends.json              # 趋势数据
│   │   └── predictions.json         # 历史预测缓存
│   ├── services/
│   │   ├── forecast_service.py      # 多模型预测（Chronos-2/Moirai/Lag-Llama）
│   │   ├── optimization_service.py  # DFS+贪心+去重路径优化
│   │   └── dashboard_service.py     # 仪表盘数据服务
│   ├── routers/
│   │   ├── dashboard.py             # 仪表盘 API
│   │   ├── forecast.py              # 预测 API（含多模型支持）
│   │   ├── optimization.py          # 路径优化 API（含运输方式过滤）
│   │   └── shipments.py             # 供应链地图 API
│   ├── lab/models/
│   │   ├── chronos-2/               # Chronos-2 模型（456MB, 已集成）
│   │   ├── moirai-small/            # Moirai-Small（447MB, 已集成）
│   │   └── lag-llama/               # Lag-Llama ckpt（28MB, 需装包）
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/index.ts             # API 封装（axios）
│       └── pages/
│           ├── Dashboard/           # 仪表盘（品类图+50物品表）
│           ├── SupplyChain/         # 供应链全景
│           ├── ForecastBoard/       # 需求预测看板（多模型+逐周明细）
│           └── RoutePlanner/        # 路径规划（运输方式过滤+品类匹配）
├── scripts/
│   ├── preprocess.py                # ISOMORPH 风格数据生成器
│   ├── download_isomorph.py         # HF 数据集下载（备选）
│   └── chronos2_test.py             # Chronos-2 测试脚本
└── README.md
```

## 已实现功能清单

- [x] ISOMORPH 风格数据生成器（50 物品 × 7500 周）
- [x] Chronos-2 零样本预测（context=2048, 21 分位数）
- [x] Moirai-Small 多变量预测（117M 参数, uni2ts）
- [x] Lag-Llama 协变量预测（checkpoint 已下载）
- [x] 多模型切换（auto/chronos-2/moirai）
- [x] DFS + 贪心 + 去重路径搜索（13 节点 23 边）
- [x] 运输方式过滤（road/rail/air）
- [x] 需求预测驱动的路径权重动态调整
- [x] 8 项 KPI 卡片 + 5 品类分布图
- [x] 50 物品汇总表 + Top 10 需求对比
- [x] 预测页面：分布直方图 + 52 周概览 + 品类对比
- [x] 逐周预测明细表（置信区间可视化条）
- [x] 供应链地图动态生成（从图拓扑）
- [x] 物品品类匹配（路径规划关联品类信息）