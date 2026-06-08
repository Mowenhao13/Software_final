"""成本记录模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base
from datetime import datetime


class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(30), comment="成本类别：procurement/logistics/inventory/quality/other")
    subcategory = Column(String(50), comment="子类别")
    amount = Column(Float, comment="金额")
    department = Column(String(50), comment="部门")
    date = Column(DateTime, comment="日期")
    description = Column(Text, comment="描述")
    created_at = Column(DateTime, default=datetime.now)
