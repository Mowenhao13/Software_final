"""应用配置"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# CORS 允许的前端地址
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

# AI 模型配置
FORECAST_HISTORY_WEEKS = 24  # 输入历史周数
FORECAST_HORIZON_WEEKS = 12  # 预测未来周数