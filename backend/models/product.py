"""产品模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from datetime import datetime


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="产品名称")
    code = Column(String(50), unique=True, comment="产品编码")
    category = Column(String(50), comment="产品类别")
    unit_price = Column(Float, default=0.0, comment="单价")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), comment="主要供应商")
    lead_time = Column(Integer, default=7, comment="采购提前期(天)")
    min_stock = Column(Integer, default=100, comment="最低安全库存")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
