"""AI 服务层"""
from services.forecast_service import predict_demand, get_available_items, batch_predict
from services.optimization_service import get_graph, find_routes, find_route_with_forecast