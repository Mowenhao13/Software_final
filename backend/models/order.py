"""采购订单模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from datetime import datetime


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, comment="订单编号")
    product_id = Column(Integer, ForeignKey("products.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    quantity = Column(Integer, comment="采购数量")
    amount = Column(Float, comment="订单金额")
    status = Column(String(20), default="pending", comment="状态:pending/confirmed/shipping/delivered/cancelled")
    order_date = Column(DateTime, default=datetime.now)
    expected_delivery = Column(DateTime, comment="预计交付日期")
    actual_delivery = Column(DateTime, comment="实际交付日期")
    created_at = Column(DateTime, default=datetime.now)
