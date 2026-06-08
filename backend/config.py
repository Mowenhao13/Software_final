"""应用配置"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'supply_chain.db')}"

# CORS 允许的前端地址
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

# AI 模型配置
FORECAST_WINDOW = 30  # 预测未来30天
RISK_THRESHOLD = 0.7  # 风险阈值
