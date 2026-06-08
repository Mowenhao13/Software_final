"""供应商模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base
from datetime import datetime


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="供应商名称")
    category = Column(String(50), comment="供应类别：原材料/零部件/包装/物流")
    region = Column(String(50), comment="所在地区")
    contact = Column(String(50), comment="联系人")
    phone = Column(String(20), comment="联系电话")
    score = Column(Float, default=80.0, comment="综合评分(0-100)")
    delivery_rate = Column(Float, default=0.95, comment="准时交付率")
    quality_rate = Column(Float, default=0.98, comment="质量合格率")
    cost_score = Column(Float, default=80.0, comment="成本竞争力评分")
    response_time = Column(Float, default=24.0, comment="平均响应时间(小时)")
    status = Column(String(20), default="active", comment="状态：active/inactive/suspended")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
