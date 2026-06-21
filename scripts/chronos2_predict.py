"""
Supply Chain Disruption Prediction using Chronos-2

This script uses the Chronos-2 time series foundation model to predict supply chain
disruption shocks. Since the original dataset contains LLM prompts and probability
estimates rather than raw time series data, we reconstruct time series from the
parsed context and use Chronos-2 for zero-shot forecasting.

Dataset Structure:
- sample_id: Unique identifier for each prediction
- prediction_date: Date when prediction was made (monthly)
- correct_answer: Ground truth (0=no shock, 1=shock)
- parsed_answer: Model's probability estimate (0-1)
- prompt: Full prompt containing disruption index value, change, and threshold
- reasoning: Model's reasoning process

Usage:
    cd backend && source .venv/bin/activate
    python ../scripts/chronos2_predict.py
"""

import os
import re
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
from chronos import Chronos2Pipeline

# ============================================================
# Configuration
# ============================================================
# Use HF mirror for China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
MODEL_PATH = BASE_DIR / "lab" / "models" / "chronos-2"
DATA_PATH = BASE_DIR / "lab" / "datasets" / "test_data.json"
OUTPUT_DIR = BASE_DIR / "lab" / "predictions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Forecasting parameters
PREDICTION_LENGTH = 1  # Predict next month

# Chronos-2 quantiles (from model config)
QUANTILES = [
    0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
    0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99
]


# ============================================================
# Data Parsing
# ============================================================
def parse_prompt_for_timeseries(prompt: List[Dict]) -> Dict:
    """Extract time series relevant information from the prompt."""
    content = prompt[0]["content"] if isinstance(prompt, list) else prompt

    # Extract current value
    current_value_match = re.search(r"current value of ([\d.]+)", content)
    current_value = float(current_value_match.group(1)) if current_value_match else None

    # Extract change
    change_match = re.search(r"changed ([+-]?[\d.]+) from", content)
    change = float(change_match.group(1)) if change_match else None

    # Extract standard deviation
    std_match = re.search(r"standard deviation \(([\d.]+)\)", content)
    std_dev = float(std_match.group(1)) if std_match else None

    # Extract target type
    target_match = re.search(r"for (\w+) ", content)
    target_type = target_match.group(1) if target_match else "unknown"

    return {
        "current_value": current_value,
        "previous_change": change,
        "std_threshold": std_dev,
        "target_type": target_type,
    }


def reconstruct_history(parsed_info: Dict, lookback: int = 24) -> np.ndarray:
    """Reconstruct a synthetic historical time series.

    Uses the observed change as trend signal to create a meaningful series
    for Chronos-2 to forecast from.
    """
    current = parsed_info["current_value"]
    change = parsed_info["previous_change"]
    std = parsed_info["std_threshold"]

    if current is None or std is None:
        return np.array([0.5])  # Default fallback

    noise_scale = std * 0.3

    # Build history backwards from current value
    history = [current]
    for i in range(lookback - 1):
        drift = -change * 0.5  # Reverse direction when going backwards
        np.random.seed(42 + i)
        noise = np.random.normal(drift, noise_scale)
        prev = history[-1] - noise
        prev = np.clip(prev, 0, 1)
        history.append(prev)

    # Reverse to get chronological order
    history = history[::-1]
    return np.array(history, dtype=np.float32)


# ============================================================
# Chronos-2 Prediction
# ============================================================
def load_model(model_path: str, device: str = "cpu") -> Chronos2Pipeline:
    """Load the Chronos-2 model from local directory."""
    print(f"Loading Chronos-2 model from: {model_path}")
    pipeline = Chronos2Pipeline.from_pretrained(
        model_path,
        device_map=device,
    )
    print(f"Model loaded on {device}")
    return pipeline


def predict_shock(
    pipeline: Chronos2Pipeline,
    history: np.ndarray,
    prediction_length: int = 1,
    threshold: float = None,
) -> Dict:
    """Use Chronos-2 to forecast and determine if a shock will occur.

    Chronos-2 returns quantile forecasts with shape (1, n_quantiles, prediction_length).
    We use the quantile distribution to estimate shock probability.
    """
    # Chronos-2 expects 3D input: (n_series, n_variates, history_length)
    history_3d = history.reshape(1, 1, -1).astype(np.float32)

    # Generate forecast
    # Returns: list of tensors, each (1, n_quantiles, prediction_length)
    forecast = pipeline.predict(
        history_3d,
        prediction_length=prediction_length,
    )

    # Extract first step predictions (all quantiles)
    # Shape: (1, n_quantiles, prediction_length) -> (n_quantiles,)
    quantile_preds = forecast[0][0, :, 0].numpy()

    # Build CDF from quantile predictions
    current_value = history[-1]
    shock_threshold = threshold if threshold else 0.35

    # Interpolate to estimate P(next_value > current_value + threshold)
    from scipy.interpolate import interp1d

    # Create inverse CDF (quantile function)
    inv_cdf = interp1d(QUANTILES, quantile_preds, fill_value="extrapolate")

    # Predicted median (p50)
    predicted_next = float(quantile_preds[QUANTILES.index(0.5)])

    # Expected change
    expected_change = predicted_next - current_value

    # Estimate shock probability using the quantile distribution
    # P(shock) = P(next > current + threshold) = 1 - CDF(current + threshold)
    # We approximate CDF by inverting the quantile function
    shock_value = current_value + shock_threshold

    # Find which quantile corresponds to shock_value
    try:
        # Use interpolation to find approximate quantile of shock_value
        cdf_func = interp1d(quantile_preds, QUANTILES, fill_value=(0, 1), bounds_error=False)
        shock_cdf = float(cdf_func(shock_value))
        shock_probability = max(0, min(1, 1 - shock_cdf))
    except Exception:
        # Fallback: use simple heuristic
        p90 = float(quantile_preds[QUANTILES.index(0.9)])
        p10 = float(quantile_preds[QUANTILES.index(0.1)])
        if shock_value >= p90:
            shock_probability = 0.05
        elif shock_value <= p10:
            shock_probability = 0.95
        else:
            shock_probability = 0.5

    # Probability of any increase
    increase_cdf = float(cdf_func(current_value)) if 'cdf_func' in dir() else 0.5
    increase_probability = max(0, min(1, 1 - increase_cdf))

    return {
        "current_value": float(current_value),
        "predicted_next_value": predicted_next,
        "predicted_change": float(expected_change),
        "shock_probability": float(shock_probability),
        "increase_probability": float(increase_probability),
        "p10": float(quantile_preds[QUANTILES.index(0.1)]),
        "p50": predicted_next,
        "p90": float(quantile_preds[QUANTILES.index(0.9)]),
        "prediction_binary": int(shock_probability > 0.1 or (increase_probability > 0.6 and expected_change > 0)),
    }


# ============================================================
# Main Pipeline
# ============================================================
def run_predictions():
    """Main function to run predictions on all samples."""
    print("=" * 60)
    print("Supply Chain Disruption Prediction with Chronos-2")
    print("=" * 60)

    # Load data
    print(f"\nLoading dataset from: {DATA_PATH}")
    df = pd.read_json(DATA_PATH, lines=True)
    print(f"Dataset shape: {df.shape}")
    print(f"Class distribution: {df['correct_answer'].value_counts().to_dict()}")

    # Load model
    print("\n" + "-" * 40)
    pipeline = load_model(str(MODEL_PATH), device="cpu")

    # Process samples
    print("\n" + "-" * 40)
    print("Running predictions...")

    results = []
    total = len(df)

    for idx, row in df.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"  Progress: {idx + 1}/{total} ({(idx+1)/total*100:.1f}%)")

        # Parse prompt
        parsed_info = parse_prompt_for_timeseries(row["prompt"])

        # Reconstruct historical series
        history = reconstruct_history(parsed_info, lookback=24)

        # Make prediction
        pred_result = predict_shock(
            pipeline=pipeline,
            history=history,
            prediction_length=PREDICTION_LENGTH,
            threshold=parsed_info["std_threshold"],
        )

        results.append(
            {
                "sample_id": row["sample_id"],
                "prediction_date": row["prediction_date"],
                "target_type": parsed_info["target_type"],
                "current_value": parsed_info["current_value"],
                "std_threshold": parsed_info["std_threshold"],
                "correct_answer": row["correct_answer"],
                "baseline_prob": row["parsed_answer"],
                "chronos_predicted_next": pred_result["predicted_next_value"],
                "chronos_predicted_change": pred_result["predicted_change"],
                "chronos_shock_probability": pred_result["shock_probability"],
                "chronos_increase_probability": pred_result["increase_probability"],
                "chronos_prediction_binary": pred_result["prediction_binary"],
                "p10": pred_result["p10"],
                "p50": pred_result["p50"],
                "p90": pred_result["p90"],
            }
        )

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Save results
    output_path = OUTPUT_DIR / "chronos2_predictions.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nPredictions saved to: {output_path}")

    # ============================================================
    # Evaluation
    # ============================================================
    print("\n" + "=" * 60)
    print("Evaluation Results")
    print("=" * 60)

    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
        brier_score_loss,
        classification_report,
    )

    y_true = results_df["correct_answer"]
    y_pred_chronos = results_df["chronos_prediction_binary"]
    y_prob_chronos = results_df.apply(
        lambda row: max(row["chronos_shock_probability"], row["chronos_increase_probability"] * 0.3), axis=1
    )
    y_prob_baseline = results_df["baseline_prob"]
    y_pred_baseline = (y_prob_baseline > 0.5).astype(int)

    print("\n--- Chronos-2 Performance ---")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred_chronos):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred_chronos, zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred_chronos, zero_division=0):.4f}")
    print(f"F1 Score:  {f1_score(y_true, y_pred_chronos, zero_division=0):.4f}")
    try:
        print(f"AUC-ROC:   {roc_auc_score(y_true, y_prob_chronos):.4f}")
    except ValueError:
        print("AUC-ROC:   N/A (single class predicted)")
    print(f"Brier:     {brier_score_loss(y_true, y_prob_chronos):.4f}")

    print("\n--- Baseline (LLM) Performance ---")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred_baseline):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred_baseline, zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred_baseline, zero_division=0):.4f}")
    print(f"F1 Score:  {f1_score(y_true, y_pred_baseline, zero_division=0):.4f}")
    try:
        print(f"AUC-ROC:   {roc_auc_score(y_true, y_prob_baseline):.4f}")
    except ValueError:
        print("AUC-ROC:   N/A (single class predicted)")
    print(f"Brier:     {brier_score_loss(y_true, y_prob_baseline):.4f}")

    print("\n--- Classification Report (Chronos-2) ---")
    print(classification_report(y_true, y_pred_chronos, zero_division=0))

    # Summary statistics
    print("\n--- Prediction Distribution ---")
    print(f"Chronos-2 predicted shocks: {y_pred_chronos.sum()}/{len(y_pred_chronos)}")
    print(f"Actual shocks: {y_true.sum()}/{len(y_true)}")
    print(f"Mean shock probability (Chronos-2): {y_prob_chronos.mean():.4f}")
    print(f"Mean shock probability (Baseline):  {y_prob_baseline.mean():.4f}")

    return results_df


if __name__ == "__main__":
    results = run_predictions()
    print("\nDone!")
