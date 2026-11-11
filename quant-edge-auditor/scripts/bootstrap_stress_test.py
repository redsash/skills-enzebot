#!/usr/bin/env python3
"""
bootstrap_stress_test.py - Quantitative Resampling, CLV Significance & Deflated Sharpe.

Audits sports betting logs for:
1. Closing Line Value (CLV) Yield and one-sample t-statistic against closing market.
2. Stationary Block Bootstrap for ROI and Maximum Drawdown confidence intervals.
3. Deflated Sharpe Ratio (DSR) adjusted for the number of discarded trials (N_trials).
4. Null Permutation Test: Scrambles outcomes 1,000 times to compute p-value of edge.

Accepts CSV or JSON with columns:
  - placed_odds (decimal)
  - closing_fair_odds (decimal, e.g. Shin-devigged benchmark)
  - stake (units, default 1.0)
  - outcome (1 for win, 0 for loss, push optional)
"""

import argparse
import csv
import json
import math
import random
import sys
from typing import List, Tuple


def calculate_clv(placed: float, closing_fair: float) -> float:
    """CLV = (placed_odds / closing_fair_odds) - 1.0"""
    return (placed / closing_fair) - 1.0


def calculate_pnl(placed: float, stake: float, outcome: float) -> float:
    """Profit/Loss for a single bet."""
    if outcome == 1.0:
        return stake * (placed - 1.0)
    elif outcome == 0.0:
        return -stake
    elif outcome == 0.5:  # Push
        return 0.0
    return 0.0


def max_drawdown(pnl_series: List[float]) -> Tuple[float, float]:
    """Calculate maximum drawdown in units and percentage from peak."""
    peak = 0.0
    cumulative = 0.0
    max_dd_units = 0.0

    for pnl in pnl_series:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd_units:
            max_dd_units = dd

    max_dd_pct = (max_dd_units / peak * 100.0) if peak > 0 else 0.0
    return max_dd_units, max_dd_pct


def deflated_sharpe_ratio(
    sharpe: float,
    num_trials: int,
    sample_len: int,
    skew: float = 0.0,
    kurtosis: float = 3.0
) -> float:
    """
    Bailey & López de Prado (2014) Deflated Sharpe Ratio.
    Computes the probability that observed Sharpe is greater than expected max Sharpe
    under null hypothesis across num_trials independent experiments.
    """
    if num_trials <= 1:
        gamma = 0.5772156649  # Euler-Mascheroni constant
        expected_max_sr = 0.0
    else:
        # Expected maximum Sharpe of N independent standard normal variables
        euler = 0.5772156649
        z_n = math.sqrt(2.0 * math.log(num_trials))
        expected_max_sr = z_n + (euler / z_n)

    # Standard error of the Sharpe ratio under non-normality
    sr_variance = (1.0 - skew * sharpe + ((kurtosis - 1.0) / 4.0) * (sharpe ** 2)) / max(1, sample_len - 1)
    sr_std = math.sqrt(max(1e-12, sr_variance))

    z_stat = (sharpe - expected_max_sr) / sr_std
    # Standard normal CDF approximation (erf)
    dsr = 0.5 * (1.0 + math.erf(z_stat / math.sqrt(2.0)))
    return dsr


def block_bootstrap(
    records: List[dict],
    block_size: int = 10,
    iterations: int = 1000
) -> Tuple[List[float], List[float]]:
    """Resample contiguous blocks to preserve temporal covariance."""
    n = len(records)
    num_blocks = math.ceil(n / block_size)
    rois = []
    drawdowns = []

    for _ in range(iterations):
        resampled = []
        for _ in range(num_blocks):
            start_idx = random.randint(0, max(0, n - block_size))
            resampled.extend(records[start_idx : start_idx + block_size])
        resampled = resampled[:n]

        total_stake = sum(r["stake"] for r in resampled)
        pnls = [r["pnl"] for r in resampled]
        net_profit = sum(pnls)
        roi = (net_profit / total_stake) if total_stake > 0 else 0.0
        mdd_units, _ = max_drawdown(pnls)

        rois.append(roi)
        drawdowns.append(mdd_units)

    return rois, drawdowns


def null_permutation_test(records: List[dict], iterations: int = 1000) -> float:
    """Scramble outcomes to test probability that observed profit is purely random."""
    observed_pnl = sum(r["pnl"] for r in records)
    outcomes = [r["outcome"] for r in records]
    placed_odds = [r["placed_odds"] for r in records]
    stakes = [r["stake"] for r in records]
    n = len(records)

    beat_count = 0
    for _ in range(iterations):
        shuffled = outcomes[:]
        random.shuffle(shuffled)
        sim_pnl = sum(calculate_pnl(placed_odds[i], stakes[i], shuffled[i]) for i in range(n))
        if sim_pnl >= observed_pnl:
            beat_count += 1

    return beat_count / iterations


def main():
    parser = argparse.ArgumentParser(
        description="Resampling, CLV Significance, and Deflated Sharpe Stress Tester."
    )
    parser.add_argument("file", help="Path to bet history CSV/JSON")
    parser.add_argument("--trials", type=int, default=1, help="Number of discarded model iterations/trials for Deflated Sharpe (default: 1)")
    parser.add_argument("--block-size", type=int, default=10, help="Block size for stationary bootstrap (default: 10)")
    parser.add_argument("--sims", type=int, default=1000, help="Number of bootstrap simulations (default: 1000)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    records = []
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content.startswith("[") or content.startswith("{"):
            raw = json.loads(content)
            data = raw.get("records", raw.get("data", raw)) if isinstance(raw, dict) else raw
        else:
            data = list(csv.DictReader(content.splitlines()))

    clv_list = []
    for row in data:
        placed = float(row.get("placed_odds", row.get("odds", 2.0)))
        closing_fair = float(row.get("closing_fair_odds", row.get("closing_odds", placed)))
        stake = float(row.get("stake", 1.0))
        outcome = float(row.get("outcome", row.get("result", 0.0)))

        pnl = calculate_pnl(placed, stake, outcome)
        clv = calculate_clv(placed, closing_fair)
        clv_list.append(clv)

        records.append({
            "placed_odds": placed,
            "closing_fair": closing_fair,
            "stake": stake,
            "outcome": outcome,
            "pnl": pnl,
            "clv": clv
        })

    n = len(records)
    if n == 0:
        sys.stderr.write("No records loaded.\n")
        sys.exit(1)

    # Basic Metrics
    total_staked = sum(r["stake"] for r in records)
    total_pnl = sum(r["pnl"] for r in records)
    observed_roi = (total_pnl / total_staked) if total_staked > 0 else 0.0
    wins = sum(1 for r in records if r["outcome"] == 1.0)
    win_rate = wins / n
    pnls = [r["pnl"] for r in records]
    max_dd_u, max_dd_pct = max_drawdown(pnls)

    # CLV t-stat
    mean_clv = sum(clv_list) / n
    var_clv = sum((x - mean_clv) ** 2 for x in clv_list) / max(1, n - 1)
    std_clv = math.sqrt(var_clv)
    se_clv = std_clv / math.sqrt(n)
    t_stat_clv = (mean_clv / se_clv) if se_clv > 0 else 0.0

    # Sharpe ratio (per-bet annualized approximation)
    mean_pnl = total_pnl / n
    var_pnl = sum((x - mean_pnl) ** 2 for x in pnls) / max(1, n - 1)
    std_pnl = math.sqrt(var_pnl)
    sharpe = (mean_pnl / std_pnl) if std_pnl > 0 else 0.0
    dsr = deflated_sharpe_ratio(sharpe, args.trials, n)

    # Bootstrap & Null test
    boot_rois, boot_dds = block_bootstrap(records, block_size=args.block_size, iterations=args.sims)
    boot_rois.sort()
    boot_dds.sort()
    roi_ci_low = boot_rois[int(0.025 * len(boot_rois))]
    roi_ci_high = boot_rois[int(0.975 * len(boot_rois))]
    dd_95th = boot_dds[int(0.95 * len(boot_dds))]

    null_p_val = null_permutation_test(records, iterations=args.sims)

    results = {
        "sample_size": n,
        "total_staked_units": round(total_staked, 2),
        "net_profit_units": round(total_pnl, 2),
        "observed_roi_pct": round(observed_roi * 100.0, 2),
        "win_rate_pct": round(win_rate * 100.0, 2),
        "observed_max_drawdown_units": round(max_dd_u, 2),
        "clv_analysis": {
            "mean_clv_pct": round(mean_clv * 100.0, 2),
            "clv_t_statistic": round(t_stat_clv, 3),
            "clv_verdict": "STATISTICALLY_SIGNIFICANT" if t_stat_clv >= 3.0 else "INCONCLUSIVE_OR_NOISE"
        },
        "overfitting_and_significance": {
            "per_bet_sharpe": round(sharpe, 4),
            "trials_tested": args.trials,
            "deflated_sharpe_ratio_dsr": round(dsr, 4),
            "null_permutation_p_value": round(null_p_val, 4),
            "edge_verdict": "DURABLE_EDGE" if (t_stat_clv >= 3.0 and dsr > 0.95 and null_p_val < 0.01) else "SUSPECT_OR_REJECTED"
        },
        "bootstrap_resampling": {
            "block_size": args.block_size,
            "simulations": args.sims,
            "roi_95_ci_pct": [round(roi_ci_low * 100.0, 2), round(roi_ci_high * 100.0, 2)],
            "max_drawdown_95th_percentile_units": round(dd_95th, 2)
        }
    }

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"### Quantitative Stress Test & Edge Audit (N={n} bets)\n")
        print(f"- **Observed ROI**: `{results['observed_roi_pct']}%` | **Net Units**: `{results['net_profit_units']}` | **Win Rate**: `{results['win_rate_pct']}%`")
        print(f"- **Max Drawdown**: `{results['observed_max_drawdown_units']}` units (95th Pct Worst-Case: `{results['bootstrap_resampling']['max_drawdown_95th_percentile_units']}` units)")
        print(f"- **95% Bootstrap ROI Interval**: `[{results['bootstrap_resampling']['roi_95_ci_pct'][0]}%, {results['bootstrap_resampling']['roi_95_ci_pct'][1]}%]`")

        print("\n#### 1. Closing Line Value (CLV) Ground Truth:")
        clv = results["clv_analysis"]
        print(f"- **Mean CLV**: `{clv['mean_clv_pct']}%`")
        print(f"- **CLV $t$-statistic**: `{clv['clv_t_statistic']}` (Threshold >= 3.0) -> **{clv['clv_verdict']}**")

        print("\n#### 2. Multiple Testing & Deflated Sharpe:")
        overfit = results["overfitting_and_significance"]
        print(f"- **Reported Trials Tested ($N_{{trials}}$)**: `{overfit['trials_tested']}`")
        print(f"- **Deflated Sharpe Ratio (DSR)**: `{overfit['deflated_sharpe_ratio_dsr']}` (Hurdle > 0.95)")
        print(f"- **Null Permutation $p$-value**: `{overfit['null_permutation_p_value']}` (Scrambled Target Test)")
        print(f"\n### Final Audit Verdict: **{overfit['edge_verdict']}**")


if __name__ == "__main__":
    main()
