"""库存模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from datetime import datetime


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse = Column(String(50), comment="仓库名称")
    quantity = Column(Integer, default=0, comment="当前库存量")
    safety_stock = Column(Integer, default=100, comment="安全库存")
    max_stock = Column(Integer, default=5000, comment="最大库存")
    turnover_rate = Column(Float, default=0.0, comment="库存周转率")
    last_restock = Column(DateTime, comment="最近补货时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
