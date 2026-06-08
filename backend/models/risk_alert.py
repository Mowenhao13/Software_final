"""风险预警模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base
from datetime import datetime


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(30), comment="预警类型：inventory_shortage/delivery_delay/cost_spike/quality_issue/supplier_risk")
    severity = Column(String(10), comment="严重程度：high/medium/low")
    title = Column(String(200), comment="预警标题")
    description = Column(Text, comment="预警详情")
    risk_score = Column(Float, default=0.5, comment="风险评分(0-1)")
    related_entity_type = Column(String(30), comment="关联实体类型")
    related_entity_id = Column(Integer, comment="关联实体ID")
    status = Column(String(20), default="active", comment="状态：active/acknowledged/resolved")
    suggested_action = Column(Text, comment="建议措施")
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, comment="解决时间")
