"""仪表盘 API"""
from fastapi import APIRouter
from services.dashboard_service import (
    get_kpis, get_trends, get_supplier_distribution, get_order_status,
    get_category_distribution, get_all_items_summary, get_item_catalog
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis")
def kpis():
    return get_kpis()


@router.get("/trends")
def trends():
    return {"trends": get_trends()}


@router.get("/supplier-distribution")
def supplier_distribution():
    return get_supplier_distribution()


@router.get("/order-status")
def order_status():
    return get_order_status()


@router.get("/category-distribution")
def category_distribution():
    return get_category_distribution()


@router.get("/items-summary")
def items_summary():
    return get_all_items_summary()


@router.get("/item-catalog")
def item_catalog():
    return get_item_catalog()