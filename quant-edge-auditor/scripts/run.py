#!/usr/bin/env python3
"""
run.py - Unified Master Quantitative Edge Audit Runner.

Runs the complete 4-stage audit protocol across:
  Stage 1: Forensic Causal Integrity (as-of leakage)
  Stage 2: Statistical Calibration & Murphy Brier Decomposition
  Stage 3: Market Microstructure & Shin De-vigging
  Stage 4: Adversarial Stress, Deflated Sharpe & Null Permutation

Accepts input dataset, outputs a comprehensive audit scorecard.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_command(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode, res.stdout, res.stderr


def _invoke_stage(stage_name: str, cmd: list, stage_exit_codes: dict) -> tuple:
    ret, out, err = run_command(cmd)
    stage_exit_codes[stage_name] = ret
    if err and err.strip():
        sys.stderr.write(f"[{stage_name} stderr] {err.strip()}\n")
    try:
        parsed = json.loads(out) if out.strip() else {}
        ok = (ret == 0) and not parsed.get("error")
        return parsed, ok
    except Exception as exc:
        return {
            "error": f"Failed to parse JSON output ({exc})",
            "raw_output": out,
            "stderr": err,
        }, False


def main():
    parser = argparse.ArgumentParser(
        description="Master Quantitative Edge Auditor Runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/run.py evals/files/sample_bets.csv --trials 25 --json\n"
            "  python3 scripts/run.py evals/files/sample_bets.csv --trials 25 --odds -450 +350"
        ),
    )
    parser.add_argument("file", help="Path to input predictions / bet history CSV or JSON")
    parser.add_argument("--trials", type=int, default=1, help="Number of discarded model iterations/trials")
    parser.add_argument("--odds", nargs="*", help="Optional odds vector to test devigging directly")
    parser.add_argument("--json", action="store_true", help="Output full JSON audit summary")
    args = parser.parse_args()

    stage_exit_codes = {}
    overall_passed = True
    audit_summary = {
        "dataset": args.file,
        "overall_passed": False,
        "overall_verdict": "INCOMPLETE_DATA",
        "stage_exit_codes": stage_exit_codes,
        "stage_results": {},
    }

    # Step 1: Temporal Causal Integrity
    s1_res, s1_ok = _invoke_stage(
        "stage_1_temporal_integrity",
        [sys.executable, str(SCRIPT_DIR / "asof_leakage_verifier.py"), args.file, "--json"],
        stage_exit_codes,
    )
    audit_summary["stage_results"]["stage_1_temporal_integrity"] = s1_res
    if not s1_ok:
        overall_passed = False

    # Step 2: Probability Calibration & Murphy
    s2_res, s2_ok = _invoke_stage(
        "stage_2_calibration",
        [sys.executable, str(SCRIPT_DIR / "brier_murphy_decomp.py"), args.file, "--json"],
        stage_exit_codes,
    )
    audit_summary["stage_results"]["stage_2_calibration"] = s2_res
    if not s2_ok:
        overall_passed = False

    # Step 3: Market Microstructure & Devig
    if args.odds:
        s3_res, s3_ok = _invoke_stage(
            "stage_3_devig",
            [sys.executable, str(SCRIPT_DIR / "devig_market.py"), *args.odds, "--json", "--method", "all"],
            stage_exit_codes,
        )
        audit_summary["stage_results"]["stage_3_devig"] = s3_res
        if not s3_ok:
            overall_passed = False

    # Step 4: Stress Testing, CLV & Deflated Sharpe
    s4_res, s4_ok = _invoke_stage(
        "stage_4_stress_test",
        [
            sys.executable,
            str(SCRIPT_DIR / "bootstrap_stress_test.py"),
            args.file,
            "--trials",
            str(args.trials),
            "--json",
        ],
        stage_exit_codes,
    )
    audit_summary["stage_results"]["stage_4_stress_test"] = s4_res
    if not s4_ok:
        overall_passed = False

    has_leakage = (
        stage_exit_codes.get("stage_1_temporal_integrity", 0) != 0
        or s1_res.get("violation_count", 0) > 0
        or s1_res.get("closing_odds_match_stats", {}).get("retroactive_odds_leakage", False)
    )
    overfit = s4_res.get("overfitting_and_significance", {})
    if has_leakage:
        final_verdict = "REJECTED_LEAKAGE"
        overall_passed = False
    else:
        final_verdict = overfit.get("edge_verdict", "INCOMPLETE_DATA")

    audit_summary["overall_passed"] = overall_passed
    audit_summary["overall_verdict"] = final_verdict

    if args.json:
        print(json.dumps(audit_summary, indent=2))
    else:
        print("# Quantitative Model Edge Audit Scorecard\n")
        print(f"**Target Dataset**: `{args.file}`")
        print(f"**Prior Discarded Trials ($N_{{trials}}$)**: `{args.trials}`\n")

        print("### 1. Forensic Causal Integrity")
        print(
            f"- Integrity Rate: `{s1_res.get('causal_integrity_rate', 'N/A')}%` | "
            f"Violations: `{s1_res.get('violation_count', 'N/A')}` | "
            f"Retroactive Odds Leakage: `{s1_res.get('closing_odds_match_stats', {}).get('retroactive_odds_leakage', 'N/A')}`"
        )

        print("\n### 2. Probability Calibration & Decomposition")
        print(f"- Brier Score: `{s2_res.get('overall_brier_score', 'N/A')}` | Log Loss: `{s2_res.get('log_loss', 'N/A')}`")
        murphy = s2_res.get("murphy_decomposition", {})
        print(f"- Reliability Penalty: `{murphy.get('reliability_penalty', 'N/A')}` | Resolution: `{murphy.get('resolution_discrimination', 'N/A')}`")
        cal = s2_res.get("calibration_metrics", {})
        print(f"- Expected Calibration Error (ECE): `{cal.get('expected_calibration_error_ece', 'N/A')}`")

        print("\n### 3. Market Efficiency & Stress Testing")
        clv = s4_res.get("clv_analysis", {})
        print(f"- Mean CLV: `{clv.get('mean_clv_pct', 'N/A')}%` (t-stat: `{clv.get('clv_t_statistic', 'N/A')}` -> {clv.get('clv_verdict', 'N/A')})")
        print(f"- Deflated Sharpe Ratio (DSR): `{overfit.get('deflated_sharpe_ratio_dsr', 'N/A')}`")
        print(f"- Null Permutation p-value: `{overfit.get('null_permutation_p_value', 'N/A')}`")
        print(f"\n## OVERALL VERDICT: **{final_verdict}**")

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
