"""Pydantic 请求/响应 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 供应商 ==========
class SupplierBase(BaseModel):
    name: str
    category: str = ""
    region: str = ""
    contact: str = ""
    phone: str = ""
    status: str = "active"

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    score: float
    delivery_rate: float
    quality_rate: float
    cost_score: float
    response_time: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupplierScoreResponse(BaseModel):
    supplier_id: int
    supplier_name: str
    overall_score: float
    dimensions: dict

# ========== 产品 ==========
class ProductBase(BaseModel):
    name: str
    code: str
    category: str = ""
    unit_price: float = 0
    supplier_id: Optional[int] = None
    lead_time: int = 7
    min_stock: int = 100

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ========== 库存 ==========
class InventoryBase(BaseModel):
    product_id: int
    warehouse: str = ""
    quantity: int = 0
    safety_stock: int = 100
    max_stock: int = 5000

class InventoryResponse(InventoryBase):
    id: int
    turnover_rate: float
    last_restock: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True

# ========== 订单 ==========
class OrderBase(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int
    amount: float
    status: str = "pending"

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    order_no: str
    order_date: datetime
    expected_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# ========== 物流 ==========
class ShipmentResponse(BaseModel):
    id: int
    tracking_no: str
    order_id: int
    origin: str
    destination: str
    origin_lng: Optional[float]
    origin_lat: Optional[float]
    dest_lng: Optional[float]
    dest_lat: Optional[float]
    current_lng: Optional[float]
    current_lat: Optional[float]
    carrier: str
    transport_mode: str
    status: str
    cost: Optional[float]
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    actual_arrival: Optional[datetime]

    class Config:
        from_attributes = True

# ========== 风险预警 ==========
class RiskAlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    risk_score: float
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    status: str
    suggested_action: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ========== 成本 ==========
class CostRecordResponse(BaseModel):
    id: int
    category: str
    subcategory: Optional[str]
    amount: float
    department: str
    date: datetime
    description: Optional[str]

    class Config:
        from_attributes = True

# ========== 仪表盘 ==========
class KPIData(BaseModel):
    total_orders: int
    total_amount: float
    on_time_delivery_rate: float
    inventory_turnover: float
    active_suppliers: int
    risk_count: int
    cost_total: float
    month_growth: float

class TrendItem(BaseModel):
    date: str
    orders: int
    amount: float
    cost: float

# ========== 预测 ==========
class ForecastItem(BaseModel):
    date: str
    predicted: float
    lower_bound: float
    upper_bound: float
    actual: Optional[float] = None

class ForecastResponse(BaseModel):
    product_name: str
    unit: str
    forecast: List[ForecastItem]
    confidence: float
    trend: str  # up/stable/down

# ========== 分析 ==========
class AnalyticsResponse(BaseModel):
    category: str
    value: float
    change: Optional[float] = None
    details: Optional[dict] = None
