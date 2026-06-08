"""物流运输模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from datetime import datetime


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_no = Column(String(50), unique=True, comment="运单号")
    order_id = Column(Integer, ForeignKey("orders.id"))
    origin = Column(String(100), comment="始发地")
    destination = Column(String(100), comment="目的地")
    origin_lng = Column(Float, comment="始发地经度")
    origin_lat = Column(Float, comment="始发地纬度")
    dest_lng = Column(Float, comment="目的地经度")
    dest_lat = Column(Float, comment="目的地纬度")
    current_lng = Column(Float, comment="当前位置经度")
    current_lat = Column(Float, comment="当前位置纬度")
    carrier = Column(String(50), comment="承运商")
    transport_mode = Column(String(20), default="road", comment="运输方式:road/rail/air/sea")
    status = Column(String(20), default="in_transit", comment="状态:pending/in_transit/delivered/delayed")
    cost = Column(Float, comment="运输成本")
    departure_time = Column(DateTime, comment="出发时间")
    arrival_time = Column(DateTime, comment="预计到达时间")
    actual_arrival = Column(DateTime, comment="实际到达时间")
    created_at = Column(DateTime, default=datetime.now)
