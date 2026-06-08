"""数据模型包"""
from database import Base

# 导入所有模型，确保 create_all 能发现它们
from models.supplier import Supplier
from models.product import Product
from models.inventory import Inventory
from models.order import Order
from models.shipment import Shipment
from models.risk_alert import RiskAlert
from models.cost_record import CostRecord

__all__ = ["Base", "Supplier", "Product", "Inventory", "Order", "Shipment", "RiskAlert", "CostRecord"]
