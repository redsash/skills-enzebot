#!/usr/bin/env python3
"""
brier_murphy_decomp.py - Probability Calibration & Murphy Brier Decomposition.

Performs:
1. Standard Brier Score and Binary Log Loss calculation.
2. Murphy (1973) Brier Score Decomposition:
     Brier = Reliability - Resolution + Uncertainty
   where:
     - Uncertainty: Base rate entropy (inherent game outcome variance)
     - Reliability: Calibration error penalty (0 is perfectly calibrated; lower is better)
     - Resolution: Discrimination ability (how well model sorts events; higher is better)
3. Equal-frequency quantile Expected Calibration Error (ECE) & Maximum Calibration Error (MCE).

Accepts a CSV or JSON file with columns/keys: 'prediction' (float 0-1) and 'outcome' (int 0 or 1).
"""

import argparse
import csv
import json
import math
import sys
from typing import List, Tuple


def calculate_log_loss(predictions: List[float], outcomes: List[int], eps: float = 1e-15) -> float:
    """Calculate binary cross-entropy (log loss)."""
    loss = 0.0
    for p, y in zip(predictions, outcomes):
        p_clipped = max(eps, min(1.0 - eps, p))
        loss -= y * math.log(p_clipped) + (1 - y) * math.log(1 - p_clipped)
    return loss / len(predictions)


def murphy_decomposition(
    predictions: List[float],
    outcomes: List[int],
    num_bins: int = 10,
    strategy: str = "quantile"
) -> dict:
    """
    Decomposes Brier score into Reliability, Resolution, Uncertainty.
    Supports 'quantile' (equal frequency) and 'uniform' (equal width) binning.
    """
    n = len(predictions)
    base_rate = sum(outcomes) / n
    uncertainty = base_rate * (1.0 - base_rate)

    paired = sorted(zip(predictions, outcomes), key=lambda x: x[0])

    # Construct bins
    bins = []
    if strategy == "quantile":
        bin_size = math.ceil(n / num_bins)
        for i in range(0, n, bin_size):
            chunk = paired[i : i + bin_size]
            if chunk:
                bins.append(chunk)
    else:  # uniform
        bin_buckets = [[] for _ in range(num_bins)]
        for p, y in paired:
            idx = min(int(p * num_bins), num_bins - 1)
            bin_buckets[idx].append((p, y))
        bins = [b for b in bin_buckets if b]

    reliability = 0.0
    resolution = 0.0
    weighted_ece = 0.0
    max_ce = 0.0
    bin_details = []

    for b in bins:
        n_k = len(b)
        mean_pred = sum(p for p, _ in b) / n_k
        obs_rate = sum(y for _, y in b) / n_k

        # Murphy components
        rel_k = n_k * ((mean_pred - obs_rate) ** 2)
        res_k = n_k * ((obs_rate - base_rate) ** 2)
        reliability += rel_k
        resolution += res_k

        # ECE & MCE
        cal_diff = abs(mean_pred - obs_rate)
        weighted_ece += n_k * cal_diff
        if cal_diff > max_ce:
            max_ce = cal_diff

        bin_details.append({
            "count": n_k,
            "mean_prediction": round(mean_pred, 4),
            "observed_win_rate": round(obs_rate, 4),
            "calibration_gap": round(cal_diff, 4)
        })

    reliability /= n
    resolution /= n
    ece = weighted_ece / n
    overall_brier = sum((p - y) ** 2 for p, y in zip(predictions, outcomes)) / n
    reconstructed_brier = reliability - resolution + uncertainty

    return {
        "sample_size": n,
        "base_rate": round(base_rate, 4),
        "overall_brier_score": round(overall_brier, 6),
        "murphy_decomposition": {
            "reliability_penalty": round(reliability, 6),
            "resolution_discrimination": round(resolution, 6),
            "uncertainty_base_entropy": round(uncertainty, 6),
            "reconstructed_brier": round(reconstructed_brier, 6),
        },
        "calibration_metrics": {
            "expected_calibration_error_ece": round(ece, 6),
            "maximum_calibration_error_mce": round(max_ce, 6),
            "binning_strategy": strategy,
            "bins_evaluated": len(bin_details),
        },
        "bin_diagnostics": bin_details
    }


def load_data(filepath: str, pred_col: str, outcome_col: str) -> Tuple[List[float], List[int]]:
    predictions = []
    outcomes = []
    with open(filepath, "r", encoding="utf-8") as f:
        # Check if json
        content = f.read().strip()
        if content.startswith("[") or content.startswith("{"):
            data = json.loads(content)
            if isinstance(data, dict):
                data = data.get("records", data.get("data", []))
            for row in data:
                predictions.append(float(row[pred_col]))
                outcomes.append(int(row[outcome_col]))
        else:
            reader = csv.DictReader(content.splitlines())
            for row in reader:
                predictions.append(float(row[pred_col]))
                outcomes.append(int(row[outcome_col]))
    return predictions, outcomes


def main():
    parser = argparse.ArgumentParser(
        description="Probability Calibration & Murphy Brier Decomposition Engine."
    )
    parser.add_argument("file", help="Path to CSV or JSON file containing predictions and actual outcomes")
    parser.add_argument("--pred-col", default="prediction", help="Name of prediction probability column (default: prediction)")
    parser.add_argument("--outcome-col", default="outcome", help="Name of outcome column 0 or 1 (default: outcome)")
    parser.add_argument("--bins", type=int, default=10, help="Number of calibration bins (default: 10)")
    parser.add_argument("--strategy", choices=["quantile", "uniform"], default="quantile", help="Binning strategy (default: quantile)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        preds, acts = load_data(args.file, args.pred_col, args.outcome_col)
    except Exception as e:
        sys.stderr.write(f"Error loading file: {e}\n")
        sys.exit(1)

    if not preds:
        sys.stderr.write("No valid rows found.\n")
        sys.exit(1)

    results = murphy_decomposition(preds, acts, num_bins=args.bins, strategy=args.strategy)
    log_loss = calculate_log_loss(preds, acts)
    results["log_loss"] = round(log_loss, 6)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"### Probability Calibration & Murphy Brier Decomposition (N={results['sample_size']})\n")
        print(f"- **Overall Brier Score**: `{results['overall_brier_score']}` | **Log Loss**: `{results['log_loss']}`")
        print(f"- **Base Rate (Uncertainty)**: `{results['base_rate']}`")
        print("\n#### Murphy Brier Components (`Brier = Reliability - Resolution + Uncertainty`):")
        m = results["murphy_decomposition"]
        print(f"| Component | Value | Interpretation |")
        print(f"| :--- | :--- | :--- |")
        print(f"| **Reliability** (Penalty) | `{m['reliability_penalty']}` | Lower is better (0 = perfect calibration). Measures deviation from empirical win rate. |")
        print(f"| **Resolution** (Discrimination) | `{m['resolution_discrimination']}` | Higher is better. Measures ability to separate wins from losses. |")
        print(f"| **Uncertainty** (Entropy) | `{m['uncertainty_base_entropy']}` | Inherent difficulty of predicting the baseline sport outcome. |")
        print(f"\n- **ECE (Expected Calibration Error)**: `{results['calibration_metrics']['expected_calibration_error_ece']*100:.2f}%`")
        print(f"- **MCE (Max Calibration Error)**: `{results['calibration_metrics']['maximum_calibration_error_mce']*100:.2f}%`")

        print("\n#### Calibration Quantile Bins:")
        print("| Bin | Count | Mean Pred | Obs Win Rate | Gap |")
        print("| :--- | :--- | :--- | :--- | :--- |")
        for i, b in enumerate(results["bin_diagnostics"]):
            print(f"| {i+1} | {b['count']} | {b['mean_prediction']*100:.1f}% | {b['observed_win_rate']*100:.1f}% | {b['calibration_gap']*100:.2f}% |")


if __name__ == "__main__":
    main()
