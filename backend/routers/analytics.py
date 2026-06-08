"""分析报表 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.optimization_service import get_logistics_analysis, get_cost_analysis
from services.supplier_service import get_supplier_performance_ranking, update_all_scores

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/logistics")
def logistics_analysis(db: Session = Depends(get_db)):
    """物流分析"""
    return get_logistics_analysis(db)


@router.get("/cost")
def cost_analysis(db: Session = Depends(get_db)):
    """成本分析"""
    return get_cost_analysis(db)


@router.get("/supplier-performance")
def supplier_performance(db: Session = Depends(get_db)):
    """供应商绩效分析"""
    update_all_scores(db)
    return get_supplier_performance_ranking(db)
