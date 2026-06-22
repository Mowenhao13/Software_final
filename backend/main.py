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
from routers.shipments import router as supply_chain_router
from routers.risk_monitor import router as risk_monitor_router
from routers.datasets import router as datasets_router

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
app.include_router(supply_chain_router)
app.include_router(risk_monitor_router)
app.include_router(datasets_router)


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