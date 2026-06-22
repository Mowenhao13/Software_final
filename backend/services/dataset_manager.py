"""数据集管理器 — 多数据集切换的中央模块

数据目录结构:
  backend/data/
    dataset_config.json    # {"active": "standard", "datasets": [...]}
    standard/              # 基础数据集 (50物品 × 156周, 5通用品类)
    detailed/              # 精细化数据集 (40物品 × 156周, 具体商品名)
"""
import json
from pathlib import Path
from typing import List, Dict, Any

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CONFIG_FILE = _DATA_DIR / "dataset_config.json"

# 数据集元信息
DATASET_META = {
    "standard": {
        "id": "standard",
        "name": "基础数据集",
        "description": "50 物品 × 156 周，5 个通用品类（电子产品/服装/汽车/食品/医药）",
        "items": 50,
        "weeks": 156,
    },
    "detailed": {
        "id": "detailed",
        "name": "精细化数据集",
        "description": "40 种具体商品 × 156 周，含真实商品名（如智能手机、冷冻三文鱼等）",
        "items": 40,
        "weeks": 156,
    },
    "walmart": {
        "id": "walmart",
        "name": "Walmart 销售数据集",
        "description": "30 种 Walmart 商品 × 156 周，基于 HF 真实销售数据（6 大部门：食品杂货/电子/家居/服装/运动/婴儿）",
        "items": 30,
        "weeks": 156,
    },
}


def _ensure_config():
    """确保配置文件和基础目录存在"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    for ds_id in DATASET_META:
        ds_dir = _DATA_DIR / ds_id
        ds_dir.mkdir(parents=True, exist_ok=True)

    if not _CONFIG_FILE.exists():
        _write_config("standard")


def _read_config() -> dict:
    _ensure_config()
    try:
        with open(_CONFIG_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"active": "standard"}


def _write_config(active: str):
    _ensure_config()
    with open(_CONFIG_FILE, "w") as f:
        json.dump({"active": active, "datasets": list(DATASET_META.keys())}, f, indent=2)


def get_data_dir() -> Path:
    """返回当前活跃数据集的目录路径"""
    config = _read_config()
    active = config.get("active", "standard")
    return _DATA_DIR / active


def get_active_dataset() -> Dict[str, Any]:
    """返回当前活跃数据集的信息"""
    config = _read_config()
    active = config.get("active", "standard")
    meta = DATASET_META.get(active, DATASET_META["standard"])
    return {**meta, "active": active}


def list_datasets() -> List[Dict[str, Any]]:
    """列出所有可用数据集"""
    return list(DATASET_META.values())


def switch_dataset(dataset_id: str) -> Dict[str, Any]:
    """切换到指定数据集"""
    if dataset_id not in DATASET_META:
        raise ValueError(f"未知数据集: {dataset_id}，可用: {list(DATASET_META.keys())}")
    _write_config(dataset_id)
    return get_active_dataset()