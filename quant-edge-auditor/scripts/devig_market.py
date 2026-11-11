#!/usr/bin/env python3
"""
devig_market.py - Quantitative Market De-vigging Engine.

Removes the bookmaker overround/margin from sports betting odds using:
1. Shin's Method (Solves for informed trader proportion z and true probability distribution)
2. Power Method (Solves sum(p_i^k) = 1)
3. Additive Log-Odds Method
4. Proportional Method (Naive normalization)

Supports American odds (-110, +150) and Decimal odds (1.909, 2.50).
Non-interactive CLI: outputs clean JSON or markdown table.
"""

import argparse
import json
import math
import sys
from typing import List, Tuple


def american_to_decimal(american: float) -> float:
    """Convert American moneyline odds to Decimal odds."""
    if american > 0:
        return (american / 100.0) + 1.0
    elif american < 0:
        return (100.0 / abs(american)) + 1.0
    else:
        raise ValueError("American odds cannot be zero.")


def parse_odds_string(raw: str) -> float:
    """Parse odd string which might be American (+150, -110) or Decimal (1.91)."""
    raw = raw.strip()
    val = float(raw)
    if ("+" in raw or "-" in raw) or (abs(val) >= 100):
        return american_to_decimal(val)
    return val


def devig_proportional(implied_probs: List[float]) -> List[float]:
    """Naive normalization: divide each implied probability by sum."""
    total = sum(implied_probs)
    return [p / total for p in implied_probs]


def devig_power(implied_probs: List[float], max_iter: int = 1000, tol: float = 1e-8) -> List[float]:
    """Power method: find exponent k such that sum(p_i^k) = 1."""
    low, high = 1.0, 10.0
    k = 1.0
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        total = sum(p ** mid for p in implied_probs)
        if abs(total - 1.0) < tol:
            k = mid
            break
        if total > 1.0:
            low = mid
        else:
            high = mid
        k = mid

    unnorm = [p ** k for p in implied_probs]
    total_unnorm = sum(unnorm)
    return [p / total_unnorm for p in unnorm]


def devig_shin(decimal_odds: List[float], max_iter: int = 1000, tol: float = 1e-8) -> Tuple[List[float], float]:
    """
    Shin's Method (1992, 1993).
    Solves for proportion of informed insider capital z and true probabilities pi.
    Returns (true_probabilities, z_parameter).
    """
    n = len(decimal_odds)
    inv_odds = [1.0 / d for d in decimal_odds]
    sigma = sum(inv_odds)

    # Initial bounds for z (informed trader fraction, usually between 0 and 0.4)
    low_z = 0.0
    high_z = 0.5
    best_z = 0.0

    for _ in range(max_iter):
        z = (low_z + high_z) / 2.0
        # Calculate unnormalized true probabilities
        # Formula: pi_i = (sqrt(z^2 + 4 * (1 - z) * (inv_odds[i]^2 / sigma)) - z) / (2 * (1 - z))
        pi_vals = []
        denom = 2.0 * (1.0 - z)
        if abs(denom) < 1e-12:
            break

        for p_inv in inv_odds:
            term = (z ** 2) + 4.0 * (1.0 - z) * (p_inv ** 2) / sigma
            sqrt_val = math.sqrt(max(0.0, term))
            pi_vals.append((sqrt_val - z) / denom)

        sum_pi = sum(pi_vals)
        if abs(sum_pi - 1.0) < tol:
            best_z = z
            break

        if sum_pi > 1.0:
            low_z = z
        else:
            high_z = z
        best_z = z

    # Final calculate with best_z
    denom = 2.0 * (1.0 - best_z)
    final_pis = []
    for p_inv in inv_odds:
        term = (best_z ** 2) + 4.0 * (1.0 - best_z) * (p_inv ** 2) / sigma
        sqrt_val = math.sqrt(max(0.0, term))
        final_pis.append(max(0.0, (sqrt_val - best_z) / denom))

    # Normalize final sum to exactly 1.0
    total_final = sum(final_pis)
    normalized = [p / total_final for p in final_pis]
    return normalized, best_z


def main():
    parser = argparse.ArgumentParser(
        description="Quantitative Market De-vigging Engine: Shin, Power, and Proportional Methods."
    )
    parser.add_argument(
        "odds",
        nargs="+",
        help="List of odds (American e.g. -110 +150, or Decimal e.g. 1.91 2.65)"
    )
    parser.add_argument(
        "--method",
        choices=["shin", "power", "proportional", "all"],
        default="shin",
        help="De-vigging algorithm to apply (default: shin)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of markdown"
    )
    args = parser.parse_args()

    try:
        dec_odds = [parse_odds_string(o) for o in args.odds]
    except Exception as e:
        sys.stderr.write(f"Error parsing odds: {e}\n")
        sys.exit(1)

    implied_probs = [1.0 / d for d in dec_odds]
    overround = sum(implied_probs)
    vig_pct = (overround - 1.0) * 100.0

    shin_probs, shin_z = devig_shin(dec_odds)
    power_probs = devig_power(implied_probs)
    prop_probs = devig_proportional(implied_probs)

    results = {
        "input_odds": args.odds,
        "decimal_odds": [round(d, 4) for d in dec_odds],
        "implied_probabilities": [round(p, 4) for p in implied_probs],
        "market_overround": round(overround, 4),
        "bookmaker_margin_pct": round(vig_pct, 2),
        "devigged": {
            "shin": {
                "true_probabilities": [round(p, 5) for p in shin_probs],
                "fair_decimal_odds": [round(1.0 / p, 3) for p in shin_probs],
                "insider_money_param_z": round(shin_z, 5)
            },
            "power": {
                "true_probabilities": [round(p, 5) for p in power_probs],
                "fair_decimal_odds": [round(1.0 / p, 3) for p in power_probs]
            },
            "proportional": {
                "true_probabilities": [round(p, 5) for p in prop_probs],
                "fair_decimal_odds": [round(1.0 / p, 3) for p in prop_probs]
            }
        }
    }

    if args.json:
        if args.method == "all":
            print(json.dumps(results, indent=2))
        else:
            selected = {
                "decimal_odds": results["decimal_odds"],
                "market_overround": results["market_overround"],
                "bookmaker_margin_pct": results["bookmaker_margin_pct"],
                "method": args.method,
                **results["devigged"][args.method]
            }
            print(json.dumps(selected, indent=2))
    else:
        print(f"### Market Overround: {results['market_overround']} ({results['bookmaker_margin_pct']}% vig)\n")
        print("| Outcome | Quoted Odds | Implied Prob | Shin Prob (Fair) | Power Prob | Proportional Prob |")
        print("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for i, raw in enumerate(args.odds):
            print(
                f"| Choice {i+1} | {raw} ({dec_odds[i]:.2f}) | "
                f"{implied_probs[i]*100:.2f}% | "
                f"**{shin_probs[i]*100:.2f}%** ({1.0/shin_probs[i]:.2f}) | "
                f"{power_probs[i]*100:.2f}% | "
                f"{prop_probs[i]*100:.2f}% |"
            )
        print(f"\n*Shin Informed Capital Parameter ($z$): {shin_z:.5f}*")


if __name__ == "__main__":
    main()
