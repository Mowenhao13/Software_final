"""供应商管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.supplier import Supplier
from schemas import SupplierCreate, SupplierResponse, SupplierScoreResponse
from services.supplier_service import calculate_supplier_score, get_supplier_performance_ranking, update_all_scores

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


@router.get("/")
def list_suppliers(skip: int = 0, limit: int = 20, search: str = "", region: str = "",
                   db: Session = Depends(get_db)):
    """获取供应商列表"""
    query = db.query(Supplier)
    if search:
        query = query.filter(Supplier.name.contains(search))
    if region:
        query = query.filter(Supplier.region == region)
    total = query.count()
    suppliers = query.offset(skip).limit(limit).all()
    return {"total": total, "items": suppliers}


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "供应商不存在")
    return supplier


@router.post("/")
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}")
def update_supplier(supplier_id: int, data: SupplierCreate, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "供应商不存在")
    for k, v in data.model_dump().items():
        setattr(supplier, k, v)
    db.commit()
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "供应商不存在")
    db.delete(supplier)
    db.commit()
    return {"message": "已删除"}


@router.get("/{supplier_id}/score")
def get_supplier_score(supplier_id: int, db: Session = Depends(get_db)):
    """获取供应商综合评分详情"""
    result = calculate_supplier_score(db, supplier_id)
    if not result:
        raise HTTPException(404, "供应商不存在")
    return result


@router.get("/ranking/list")
def get_ranking(db: Session = Depends(get_db)):
    """供应商绩效排名"""
    update_all_scores(db)
    return get_supplier_performance_ranking(db)
