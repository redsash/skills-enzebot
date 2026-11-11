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


def main():
    parser = argparse.ArgumentParser(
        description="Master Quantitative Edge Auditor Runner."
    )
    parser.add_argument("file", help="Path to input predictions / bet history CSV or JSON")
    parser.add_argument("--trials", type=int, default=1, help="Number of discarded model iterations/trials")
    parser.add_argument("--odds", nargs="*", help="Optional odds vector to test devigging directly")
    parser.add_argument("--json", action="store_true", help="Output full JSON audit summary")
    args = parser.parse_args()

    # Step 0: Detect environment
    _, env_out, _ = run_command([sys.executable, str(SCRIPT_DIR / "detect_environment.py")])
    try:
        env_data = json.loads(env_out)
    except Exception:
        env_data = {}

    audit_summary = {
        "dataset": args.file,
        "runtime_environment": env_data.get("runtime", {}),
        "stage_results": {}
    }

    # Step 1: Temporal Causal Integrity
    ret, out_leak, _ = run_command([
        sys.executable, str(SCRIPT_DIR / "asof_leakage_verifier.py"), args.file, "--json"
    ])
    try:
        audit_summary["stage_results"]["stage_1_temporal_integrity"] = json.loads(out_leak)
    except Exception:
        audit_summary["stage_results"]["stage_1_temporal_integrity"] = {"raw_output": out_leak}

    # Step 2: Probability Calibration & Murphy
    ret, out_brier, _ = run_command([
        sys.executable, str(SCRIPT_DIR / "brier_murphy_decomp.py"), args.file, "--json"
    ])
    try:
        audit_summary["stage_results"]["stage_2_calibration"] = json.loads(out_brier)
    except Exception:
        audit_summary["stage_results"]["stage_2_calibration"] = {"raw_output": out_brier}

    # Step 3: Market Microstructure & Devig
    if args.odds:
        ret, out_devig, _ = run_command([
            sys.executable, str(SCRIPT_DIR / "devig_market.py"), *args.odds, "--json", "--method", "all"
        ])
        try:
            audit_summary["stage_results"]["stage_3_devig"] = json.loads(out_devig)
        except Exception:
            audit_summary["stage_results"]["stage_3_devig"] = {"raw_output": out_devig}

    # Step 4: Stress Testing, CLV & Deflated Sharpe
    ret, out_stress, _ = run_command([
        sys.executable, str(SCRIPT_DIR / "bootstrap_stress_test.py"), args.file,
        "--trials", str(args.trials), "--json"
    ])
    try:
        audit_summary["stage_results"]["stage_4_stress_test"] = json.loads(out_stress)
    except Exception:
        audit_summary["stage_results"]["stage_4_stress_test"] = {"raw_output": out_stress}

    if args.json:
        print(json.dumps(audit_summary, indent=2))
    else:
        print("# Quantitative Model Edge Audit Scorecard\n")
        print(f"**Target Dataset**: `{args.file}`")
        print(f"**Prior Discarded Trials ($N_{{trials}}$)**: `{args.trials}`\n")

        s1 = audit_summary["stage_results"].get("stage_1_temporal_integrity", {})
        print("### 1. Forensic Causal Integrity")
        print(f"- Integrity Rate: `{s1.get('causal_integrity_rate', 'N/A')}%` | Violations: `{s1.get('violation_count', 'N/A')}`")

        s2 = audit_summary["stage_results"].get("stage_2_calibration", {})
        print("\n### 2. Probability Calibration & Decomposition")
        print(f"- Brier Score: `{s2.get('overall_brier_score', 'N/A')}` | Log Loss: `{s2.get('log_loss', 'N/A')}`")
        murphy = s2.get("murphy_decomposition", {})
        print(f"- Reliability Penalty: `{murphy.get('reliability_penalty', 'N/A')}` | Resolution: `{murphy.get('resolution_discrimination', 'N/A')}`")
        cal = s2.get("calibration_metrics", {})
        print(f"- Expected Calibration Error (ECE): `{cal.get('expected_calibration_error_ece', 'N/A')}`")

        s4 = audit_summary["stage_results"].get("stage_4_stress_test", {})
        print("\n### 3. Market Efficiency & Stress Testing")
        clv = s4.get("clv_analysis", {})
        print(f"- Mean CLV: `{clv.get('mean_clv_pct', 'N/A')}%` (t-stat: `{clv.get('clv_t_statistic', 'N/A')}` -> {clv.get('clv_verdict', 'N/A')})")
        overfit = s4.get("overfitting_and_significance", {})
        print(f"- Deflated Sharpe Ratio (DSR): `{overfit.get('deflated_sharpe_ratio_dsr', 'N/A')}`")
        print(f"- Null Permutation p-value: `{overfit.get('null_permutation_p_value', 'N/A')}`")
        print(f"\n## OVERALL VERDICT: **{overfit.get('edge_verdict', 'INCOMPLETE_DATA')}**")


if __name__ == "__main__":
    main()
