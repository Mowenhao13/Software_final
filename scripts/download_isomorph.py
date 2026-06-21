"""
从 HuggingFace 下载 ISOMORPH Supply Chain Benchmark 数据集的 baseline 场景
仅下载 C=50 场景 (约500MB)，包含需求信号和图拓扑
"""
import os
from pathlib import Path

HF_DATASET = "Isomorph2026/isomorph-supply-chain-benchmark"
BASE_DIR = Path(__file__).resolve().parent.parent / "backend" / "lab" / "datasets"
CACHE_DIR = BASE_DIR / "hf_cache"


def download_baseline():
    """下载 ISOMORPH baseline C=50 场景的核心文件"""
    print(f"正在从 HF 加载数据集: {HF_DATASET}")
    os.makedirs(CACHE_DIR, exist_ok=True)

    from datasets import load_dataset

    # 仅加载 output_item50 场景
    ds = load_dataset(
        HF_DATASET,
        split=None,
        cache_dir=str(CACHE_DIR),
        streaming=False,
    )
    print(f"数据集加载完成. 结构: {ds}")
    return ds


if __name__ == "__main__":
    download_baseline()
    print("下载完成！数据集已缓存到 backend/lab/datasets/hf_cache/")