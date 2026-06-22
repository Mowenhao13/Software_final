"""数据集切换 API"""
from fastapi import APIRouter, HTTPException
from services.dataset_manager import list_datasets, get_active_dataset, switch_dataset

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.get("")
def list_all_datasets():
    """列出所有可用数据集"""
    return {
        "datasets": list_datasets(),
        "active": get_active_dataset(),
    }


@router.post("/switch/{dataset_id}")
def switch_active_dataset(dataset_id: str):
    """切换到指定数据集"""
    try:
        result = switch_dataset(dataset_id)
        return {"success": True, "dataset": result}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/active")
def current_dataset():
    """返回当前活跃数据集信息"""
    return get_active_dataset()