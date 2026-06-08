"""AI 赋能企业供应链的可视化分析系统 — 后端入口"""
import asyncio
import json
import random
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect

from config import CORS_ORIGINS
from database import engine, Base
from routers import dashboard, suppliers, products, inventory, orders, shipments, forecast, risks, analytics
from seed_data import seed_all

# 创建应用
app = FastAPI(
    title="AI供应链可视化分析系统",
    description="AI-Empowered Enterprise Supply Chain Visualization Analysis System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router)
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(shipments.router)
app.include_router(forecast.router)
app.include_router(risks.router)
app.include_router(analytics.router)


@app.on_event("startup")
async def on_startup():
    """应用启动 — 创建表并填充种子数据"""
    Base.metadata.create_all(bind=engine)
    seed_all()


@app.get("/")
def root():
    return {
        "name": "AI供应链可视化分析系统",
        "version": "1.0.0",
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
            # 模拟实时供应链数据推送 (每3秒)
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
                            "新订单PO-2025-1061已确认",
                            "运单SF2025100105已到达南京中转站",
                            "库存预警: MCU芯片低于安全库存",
                            "供应商评分已更新",
                            "物流时效恢复正常",
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
