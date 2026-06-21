"""需求预测服务 — Chronos-2 / Lag-Llama / Moirai 多模型支持

模型能力对比:
  - Chronos-2: 单变量零样本，21分位数输出，长上下文(8192)
  - Lag-Llama: 单变量+协变量(支持future known covariates)
  - Moirai:   多变量联合预测 (支持多个序列一起预测)
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODELS_DIR = Path(__file__).resolve().parent.parent / "lab" / "models"

# HF 镜像
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Chronos-2 分位数
QUANTILES = [
    0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
    0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99
]
MAX_CONTEXT = 2048

# 全局模型实例 (延迟加载)
_chronos_pipeline = None
_lagllama_model = None
_moirai_pipeline = None

MODEL_NAMES = Literal["chronos-2", "lag-llama", "moirai", "auto"]

# ==================== 模型加载 ====================

def _load_chronos():
    """延迟加载 Chronos-2"""
    global _chronos_pipeline
    if _chronos_pipeline is not None:
        return _chronos_pipeline
    model_path = MODELS_DIR / "chronos-2"
    if not (model_path / "model.safetensors").exists():
        print("Chronos-2 模型文件不存在")
        return None
    try:
        from chronos import Chronos2Pipeline
        print(f"加载 Chronos-2: {model_path}")
        _chronos_pipeline = Chronos2Pipeline.from_pretrained(str(model_path), device_map="cpu")
        print("Chronos-2 加载完成")
    except Exception as e:
        print(f"Chronos-2 加载失败: {e}")
        _chronos_pipeline = None
    return _chronos_pipeline


def _load_lagllama():
    """延迟加载 Lag-Llama (支持协变量)"""
    global _lagllama_model
    if _lagllama_model is not None:
        return _lagllama_model
    ckpt_path = MODELS_DIR / "lag-llama" / "lag-llama.ckpt"
    if not ckpt_path.exists():
        print(f"Lag-Llama 模型文件不存在: {ckpt_path}")
        return None
    try:
        import torch
        from lag_llama.gluon.estimator import LagLlamaEstimator
        print(f"加载 Lag-Llama: {ckpt_path}")
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        estimator_args = ckpt["hyper_parameters"]["model_kwargs"]
        _lagllama_model = LagLlamaEstimator(
            ckpt_path=str(ckpt_path),
            prediction_length=12,
            context_length=256,
            input_size=estimator_args.get("input_size", 1),
            n_layer=estimator_args.get("n_layer", 6),
            n_embd_per_head=estimator_args.get("n_embd_per_head", 32),
            n_head=estimator_args.get("n_head", 4),
            n_embd=estimator_args.get("n_embd", 128),
            scaling=estimator_args.get("scaling", "mean"),
            time_feat=estimator_args.get("time_feat", False),
            dropout=estimator_args.get("dropout", 0.0),
            num_parallel_samples=20,
        )
        print("Lag-Llama 加载完成")
    except Exception as e:
        print(f"Lag-Llama 加载失败: {e}")
        _lagllama_model = None
    return _lagllama_model


def _load_moirai():
    """延迟加载 Moirai-Small (多变量支持)"""
    global _moirai_pipeline
    if _moirai_pipeline is not None:
        return _moirai_pipeline
    model_path = MODELS_DIR / "moirai-small"
    config_path = model_path / "config.json"
    if not config_path.exists():
        print(f"Moirai 模型文件不存在: {model_path}")
        return None
    try:
        from uni2ts.model.moirai import MoiraiModule, MoiraiForecast
        print(f"加载 Moirai: {model_path}")
        module = MoiraiModule.from_pretrained(str(model_path))
        _moirai_pipeline = {
            "module": module,
            "model": MoiraiForecast(
                prediction_length=12,
                target_dim=1,
                feat_dynamic_real_dim=0,
                past_feat_dynamic_real_dim=0,
                context_length=512,
                module=module,
                patch_size="auto",
                num_samples=100,
            ),
        }
        _moirai_pipeline["model"].eval()
        _moirai_pipeline["predictor"] = _moirai_pipeline["model"].create_predictor(batch_size=1)
        print(f"Moirai 加载完成 (d_model={module.d_model})")
    except Exception as e:
        print(f"Moirai 加载失败: {e}")
        _moirai_pipeline = None
    return _moirai_pipeline


def get_available_models() -> List[Dict[str, Any]]:
    """返回可用模型列表"""
    models = []
    if (MODELS_DIR / "chronos-2" / "model.safetensors").exists():
        models.append({"name": "chronos-2", "type": "univariate", "context": 8192, "quantiles": 21, "status": "ready"})
    if (MODELS_DIR / "lag-llama" / "lag-llama.ckpt").exists():
        models.append({"name": "lag-llama", "type": "univariate+covariates", "context": 256,
                       "status": "package_needed", "note": "需要从 GitHub 安装 lag-llama 包 (git clone)"})
    if (MODELS_DIR / "moirai-small" / "config.json").exists():
        models.append({"name": "moirai", "type": "multivariate", "context": 512, "params_M": "~117M", "status": "ready"})
    return models


# ==================== 数据加载 ====================

def _load_demand_data() -> Dict[str, Any]:
    path = DATA_DIR / "demand_weekly.json"
    if not path.exists():
        return {"weeks": [], "items": {}}
    with open(path) as f:
        return json.load(f)


def get_available_items() -> List[Dict[str, Any]]:
    data = _load_demand_data()
    return [
        {"item_id": iid, "weeks": len(item.get("weekly_demand", [])), "category": item.get("category", "")}
        for iid, item in data.get("items", {}).items()
    ]


# ==================== 预测主入口 ====================

def predict_demand(
    item_id: str,
    horizon: int = 12,
    model: MODEL_NAMES = "auto",
    covariates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """需求预测入口

    Args:
        item_id: 物品ID
        horizon: 预测步长(周)
        model: 模型选择 (auto/chronos-2/lag-llama/moirai)
        covariates: 协变量 (仅 Lag-Llama 支持, e.g. {"holiday": [0,1,0,...]})
    """
    data = _load_demand_data()
    items = data.get("items", {})
    item = items.get(item_id)
    if not item:
        return {"error": f"物品 {item_id} 未找到", "forecast": [], "confidence": 0, "trend": "unknown"}

    history = np.array(item["weekly_demand"], dtype=np.float32)
    category = item.get("category", "")

    # 历史统计
    hist_stats = {
        "mean": round(float(np.mean(history[-104:])), 1),   # 近2年均值
        "std": round(float(np.std(history[-104:])), 1),
        "min": round(float(np.min(history[-104:])), 1),
        "max": round(float(np.max(history[-104:])), 1),
        "recent_4w_avg": round(float(np.mean(history[-4:])), 1),
        "recent_8w_avg": round(float(np.mean(history[-8:])), 1),
        "total": round(float(np.sum(history)), 0),
        "cv": round(float(np.std(history[-104:]) / (np.mean(history[-104:]) + 0.001)), 2),  # 变异系数
    }

    # auto: 优先 Chronos-2 → Lag-Llama → Moirai → Holt-Winters
    result = None
    if model == "auto":
        if covariates:
            result = _predict_lagllama(item_id, history, horizon, covariates)
        else:
            p = _load_chronos()
            if p is not None:
                try:
                    result = _predict_chronos(p, item_id, history, horizon)
                except Exception as e:
                    print(f"Chronos-2 预测失败: {e}")
            if result is None:
                result = _holt_winters_fallback(history, horizon)
    elif model == "chronos-2":
        p = _load_chronos()
        if p is not None:
            result = _predict_chronos(p, item_id, history, horizon)
        else:
            return {"error": "Chronos-2 模型不可用"}
    elif model == "lag-llama":
        result = _predict_lagllama(item_id, history, horizon, covariates or {})
    elif model == "moirai":
        result = _predict_moirai(item_id, history, horizon)
    else:
        return {"error": f"未知模型: {model}"}

    if "error" in result:
        return result

    # 注入品类和历史统计信息
    result["item_id"] = item_id
    result["category"] = category
    result["hist_stats"] = hist_stats
    result["model_name"] = model
    return result


# ==================== 多物品批量预测 (Moirai 多变量模式) ====================

def batch_predict_moirai(
    item_ids: List[str],
    horizon: int = 12,
) -> Dict[str, Any]:
    """使用 Moirai 进行多变量批量预测 (一次预测多个物品)"""
    data = _load_demand_data()
    items = data.get("items", {})

    pipeline = _load_moirai()
    if pipeline is None:
        return {"error": "Moirai 模型不可用", "results": []}

    results = []
    for iid in item_ids:
        item = items.get(iid)
        if not item:
            continue
        hist = np.array(item["weekly_demand"], dtype=np.float32)[-512:]
        result = _predict_moirai(iid, hist, horizon)
        results.append(result)
    return {"model": "moirai", "results": results, "total_items": len(results)}


def batch_predict(item_ids: List[str], horizon: int = 12, model: MODEL_NAMES = "auto") -> List[Dict[str, Any]]:
    """批量预测"""
    if model == "moirai":
        br = batch_predict_moirai(item_ids, horizon)
        return br.get("results", [])
    return [predict_demand(iid, horizon, model) for iid in item_ids]


# ==================== Chronos-2 预测 ====================

def _predict_chronos(pipeline, item_id: str, history: np.ndarray, horizon: int) -> Dict[str, Any]:
    n_context = min(len(history), MAX_CONTEXT)
    hist = history[-n_context:]
    hist_3d = hist.reshape(1, 1, -1).astype(np.float32)
    print(f"  Chronos-2 预测 {item_id}: context={n_context}, horizon={horizon}")

    forecast = pipeline.predict(hist_3d, prediction_length=horizon)
    quantile_preds = forecast[0][0, :, :].numpy()

    result = []
    for w in range(horizon):
        p50 = float(quantile_preds[QUANTILES.index(0.5), w])
        p10 = float(quantile_preds[QUANTILES.index(0.1), w])
        p90 = float(quantile_preds[QUANTILES.index(0.9), w])
        result.append({"week": w + 1, "predicted": round(p50, 1), "p10": round(p10, 1), "p90": round(p90, 1)})

    trend = _calc_trend(hist[-8:], [f["predicted"] for f in result])
    confidence = _calc_confidence(result)

    return {
        "item_id": item_id, "forecast": result, "confidence": confidence,
        "trend": trend, "method": "chronos-2", "context_length": n_context,
        "history": [round(float(v), 2) for v in hist[-52:].tolist()],
    }


# ==================== Lag-Llama 预测 (含协变量) ====================

def _predict_lagllama(
    item_id: str,
    history: np.ndarray,
    horizon: int,
    covariates: Dict[str, Any],
) -> Dict[str, Any]:
    """使用 Lag-Llama 预测 (支持协变量)"""
    estimator = _load_lagllama()
    if estimator is None:
        print("Lag-Llama 不可用, 回退 Chronos-2")
        p = _load_chronos()
        if p is not None:
            return _predict_chronos(p, item_id, history, horizon)
        return _holt_winters_fallback(history, horizon)

    try:
        import torch
        ctx = min(len(history), 256)
        hist = history[-ctx:]

        # 构建 Lag-Llama 输入 (单变量 + 可选协变量)
        # Lag-Llama 期望: (batch, time)
        hist_tensor = torch.tensor(hist, dtype=torch.float32).unsqueeze(0)

        # 如果有协变量，构造 future_feat_dynamic_real
        future_cov = None
        if covariates:
            cov_values = list(covariates.values())
            if cov_values:
                # shape: (batch, n_covariates, horizon)
                future_cov = torch.tensor(cov_values, dtype=torch.float32).unsqueeze(0)

        # 预测
        print(f"  Lag-Llama 预测 {item_id}: context={ctx}, horizon={horizon}, covariates={list(covariates.keys())}")
        forecast = estimator.predict(
            hist_tensor,
            prediction_length=horizon,
            future_feat_dynamic_real=future_cov,
        )

        # 处理输出
        if hasattr(forecast, "numpy"):
            samples = forecast.numpy()
        else:
            samples = forecast

        if isinstance(samples, (list, tuple)):
            samples = np.array(samples)

        if samples.ndim == 3:
            samples = samples[0]
        elif samples.ndim == 1:
            samples = samples.reshape(1, -1)

        # 从样本估算分位数
        result = []
        for w in range(min(horizon, samples.shape[-1])):
            vals = samples[:, w] if samples.ndim > 1 else samples
            p50 = float(np.median(vals))
            p10 = float(np.percentile(vals, 10))
            p90 = float(np.percentile(vals, 90))
            result.append({"week": w + 1, "predicted": round(p50, 1), "p10": round(p10, 1), "p90": round(p90, 1)})

        trend = _calc_trend(hist[-8:], [f["predicted"] for f in result])
        confidence = _calc_confidence(result)

        return {
            "item_id": item_id, "forecast": result, "confidence": confidence,
            "trend": trend, "method": "lag-llama", "covariates": list(covariates.keys()) if covariates else [],
            "history": [round(float(v), 2) for v in hist[-52:].tolist()],
        }
    except Exception as e:
        print(f"Lag-Llama 预测失败: {e}, 回退")
        p = _load_chronos()
        if p is not None:
            return _predict_chronos(p, item_id, history, horizon)
        return _holt_winters_fallback(history, horizon)


# ==================== Moirai 预测 (多变量) ====================

def _predict_moirai(
    item_id: str,
    history: np.ndarray,
    horizon: int,
) -> Dict[str, Any]:
    """使用 Moirai (uni2ts) 进行单序列预测"""
    pipeline = _load_moirai()
    if pipeline is None:
        print("Moirai 不可用, 回退 Chronos-2")
        p = _load_chronos()
        if p is not None:
            return _predict_chronos(p, item_id, history, horizon)
        return _holt_winters_fallback(history, horizon)

    try:
        import pandas as pd
        predictor = pipeline["predictor"]
        ctx = min(len(history), 512)
        hist = history[-ctx:]

        # 计算 forecast_start
        start = pd.Period("2020-01-01", freq="W")
        forecast_start = start + len(hist)

        print(f"  Moirai 预测 {item_id}: context={ctx}, horizon={horizon}")

        # GluonTS 数据格式
        data = [{
            "target": hist.astype(np.float32),
            "start": start,
            "forecast_start": forecast_start,
            "item_id": item_id,
            "info": {},
        }]

        results = list(predictor.predict(data))
        if not results:
            raise ValueError("Moirai 未返回结果")

        f = results[0]
        samples = f.samples  # (num_samples, horizon)
        mean = f.mean

        result = []
        for w in range(min(horizon, samples.shape[1])):
            vals = samples[:, w]
            p50 = float(np.median(vals))
            p10 = float(np.percentile(vals, 10))
            p90 = float(np.percentile(vals, 90))
            # 需求不可能为负，截断到0
            result.append({
                "week": w + 1,
                "predicted": round(max(0, p50), 1),
                "p10": round(max(0, p10), 1),
                "p90": round(max(0, p90), 1),
            })

        trend = _calc_trend(hist[-8:], [r["predicted"] for r in result])
        confidence = _calc_confidence(result)

        return {
            "item_id": item_id, "forecast": result, "confidence": confidence,
            "trend": trend, "method": "moirai",
            "history": [round(float(v), 2) for v in hist[-52:].tolist()],
        }
    except Exception as e:
        print(f"Moirai 预测失败: {e}, 回退 Chronos-2")
        import traceback
        traceback.print_exc()
        p = _load_chronos()
        if p is not None:
            return _predict_chronos(p, item_id, history, horizon)
        return _holt_winters_fallback(history, horizon)


# ==================== 工具函数 ====================

def _calc_trend(recent: np.ndarray, forecast_vals: List[float]) -> str:
    recent_avg = float(np.mean(recent))
    forecast_avg = float(np.mean(forecast_vals)) if forecast_vals else recent_avg
    if forecast_avg > recent_avg * 1.08:
        return "up"
    if forecast_avg < recent_avg * 0.92:
        return "down"
    return "stable"


def _calc_confidence(forecast: List[Dict]) -> float:
    widths = [(f["p90"] - f["p10"]) / (max(f["predicted"], 1)) for f in forecast]
    avg_norm_width = float(np.mean(widths)) if widths else 0.5
    return round(max(0.1, min(1.0, 1.0 - avg_norm_width * 0.5)), 2)


def _holt_winters_fallback(history: np.ndarray, horizon: int = 12) -> Dict:
    """Holt-Winters 回退预测"""
    alpha, beta, gamma = 0.3, 0.1, 0.1
    season_len = 4

    level = history[0]
    trend = history[1] - history[0] if len(history) > 1 else 0
    seasonal = [0] * season_len

    fitted = []
    for t, y in enumerate(history):
        if t < season_len:
            fitted.append(float(y))
            continue
        s_idx = (t - season_len) % season_len
        f = float(max(0, level + trend + seasonal[s_idx]))
        fitted.append(f)
        new_level = alpha * (y - seasonal[s_idx]) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        new_seasonal = gamma * (y - new_level) + (1 - gamma) * seasonal[s_idx]
        level, trend = new_level, new_trend
        seasonal[s_idx] = new_seasonal

    errors = [abs(history[i] - fitted[i]) for i in range(season_len, len(fitted))]
    mae = float(np.mean(errors)) if errors else float(np.mean(history) * 0.15)

    forecast = []
    f_level, f_trend = level, trend
    for i in range(horizon):
        s_idx = (len(history) + i) % season_len
        pred = float(max(0, f_level + f_trend + seasonal[s_idx]))
        forecast.append({
            "week": i + 1, "predicted": round(pred, 1),
            "p10": round(max(0, pred - 1.28 * mae), 1),
            "p90": round(pred + 1.28 * mae, 1),
        })

    trend_dir = _calc_trend(history[-8:], [f["predicted"] for f in forecast])
    confidence = round(max(0, min(1, 1 - mae / (float(np.mean(history)) + 0.001))), 2)

    return {"forecast": forecast, "confidence": confidence, "trend": trend_dir, "method": "holt-winters"}