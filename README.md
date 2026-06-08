# AI 赋能企业供应链的可视化分析系统

智能化的企业供应链全链路数据采集、分析与可视化平台。利用AI技术（需求预测、风险预警、异常检测、供应商评分）帮助企业实时监控供应链状态，识别潜在风险，优化资源配置。

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (React 18)                │
│  Ant Design 5  │  ECharts 5  │  WebSocket       │
├─────────────────────────────────────────────────┤
│              后端 API (FastAPI)                  │
│  RESTful API  │  WebSocket  │  AI Services      │
├─────────────────────────────────────────────────┤
│              AI 引擎 (scikit-learn)              │
│  需求预测  │  风险分析  │  异常检测  │  评分模型 │
├─────────────────────────────────────────────────┤
│              数据库 (SQLite/SQLAlchemy)          │
└─────────────────────────────────────────────────┘
```

## 功能模块

| 模块 | 功能 |
|------|------|
| 📊 **仪表盘** | KPI指标卡片、30天趋势图、供应商分布、订单状态、实时预警 |
| 🗺️ **供应链全景** | 物流路线地图、在途状态追踪、运输方式统计 |
| 🏢 **供应商管理** | CRUD、多维度评分雷达图、绩效排名、地区筛选 |
| 📦 **库存管理** | 库存状态表、安全库存预警、周转率分析、仓库筛选 |
| 📋 **订单管理** | 订单列表、状态流转、采购趋势、创建订单 |
| 🚚 **物流追踪** | 运单列表、运输方式成本对比、时效分析 |
| ⚠️ **风险监控** | 预警列表、风险检测、异常检测(IQR/Z-Score)、严重度分布 |
| 📈 **分析报表** | 成本构成、月度趋势、部门对比、供应商绩效散点图 |

## AI 能力

1. **需求预测** — Holt-Winters指数平滑，预测未来30天需求量（含置信区间）
2. **风险预警** — 自动化规则引擎 + 统计异常检测，实时识别库存/交付/质量/供应商风险
3. **供应商评分** — 四维度加权评估（准时率30% + 质量30% + 成本25% + 响应15%）
4. **异常检测** — Z-Score检测订单/成本异常，IQR检测库存异常
5. **实时推送** — WebSocket每3秒推送最新供应链动态

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 9+

### 1. 创建并激活虚拟环境

```bash
uv venv
source .venv/bin/activate
```

### 2. 开启后端

```bash
cd backend
uv pip install -r requirements.txt
python seed_data.py          # 初始化数据库
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端运行在 http://localhost:8000
- API 文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/api/health

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 4. 访问系统

浏览器打开 http://localhost:5173 即可查看完整系统。

## API 概览

| 端点 | 说明 |
|------|------|
| GET /api/dashboard/kpis | 核心KPI指标 |
| GET /api/dashboard/trends | 30天趋势 |
| GET /api/suppliers/ | 供应商列表 |
| GET /api/suppliers/ranking/list | 绩效排名 |
| GET /api/inventory/ | 库存列表 |
| GET /api/orders/ | 订单列表 |
| GET /api/shipments/map | 物流地图数据 |
| GET /api/forecast/demand | 需求预测 |
| GET /api/risks/ | 风险预警列表 |
| POST /api/risks/detect | 执行风险检测 |
| GET /api/analytics/cost | 成本分析 |
| GET /api/analytics/supplier-performance | 供应商绩效 |
| WS /ws/realtime | 实时推送 |

## 项目结构

```
supply-chain-analytics/
├── backend/
│   ├── main.py              # FastAPI 入口 + WebSocket
│   ├── config.py            # 配置
│   ├── database.py          # 数据库连接
│   ├── seed_data.py         # 演示数据(100+条)
│   ├── models/              # SQLAlchemy 数据模型 (7张表)
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── routers/             # API 路由 (9个模块)
│   └── services/            # AI 服务 (5个模块)
├── frontend/
│   └── src/
│       ├── api/             # API 封装
│       ├── pages/           # 页面组件 (8个页面)
│       ├── components/      # 通用组件
│       └── utils/           # WebSocket 客户端
└── README.md
```
