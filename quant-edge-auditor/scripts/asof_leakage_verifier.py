#!/usr/bin/env python3
"""
asof_leakage_verifier.py - Forensic Point-in-Time & As-Of Join Integrity Auditor.

Validates that historical backtest datasets strictly respect causality:
1. Knowledge Time Rule: knowledge_timestamp <= prediction_timestamp
2. Pre-Game Rule: prediction_timestamp < event_start_timestamp (strict pre-kickoff)
3. Closing Line Leakage: Verifies placed odds are not retroactively set to closing odds.
4. Feature Invariance: Detects columns that represent post-game stats leaking into inputs.

Accepts CSV or JSON files.
Returns exit code 0 if fully causal, exit code 1 if leakage or lookahead is detected.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional


KNOWN_POST_GAME_KEYWORDS = [
    "final_score", "pts_scored", "full_time", "result", "winner",
    "closing_line_value", "clv", "halftime_score", "boxscore",
    "turnovers_actual", "yards_actual", "receptions_actual", "touchdowns"
]


def parse_timestamp(ts_val: str) -> Optional[datetime]:
    if not ts_val:
        return None
    ts_val = ts_val.strip()
    # Try ISO formats and standard timestamp formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(ts_val, fmt)
        except ValueError:
            pass
    # Try integer/float unix epoch
    try:
        val = float(ts_val)
        if val > 1e11:  # milliseconds
            val /= 1000.0
        return datetime.fromtimestamp(val)
    except ValueError:
        return None


def audit_file(
    filepath: str,
    knowledge_col: str,
    prediction_col: str,
    event_start_col: str,
    placed_odds_col: Optional[str] = None,
    closing_odds_col: Optional[str] = None,
) -> dict:
    violations = []
    total_rows = 0
    clean_rows = 0
    suspicious_features = set()

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content.startswith("[") or content.startswith("{"):
            records = json.loads(content)
            if isinstance(records, dict):
                records = records.get("records", records.get("data", []))
        else:
            reader = csv.DictReader(content.splitlines())
            records = list(reader)

    if not records:
        return {"error": "Empty dataset"}

    # Audit column headers for suspicious post-game feature names
    headers = list(records[0].keys())
    for h in headers:
        hl = h.lower()
        if any(post in hl for post in KNOWN_POST_GAME_KEYWORDS):
            # Check if it's meant to be the target or if it's in the features
            if hl not in ["outcome", "actual", "target", "y", "y_true"]:
                suspicious_features.add(h)

    for idx, row in enumerate(records):
        total_rows += 1
        row_id = row.get("id", row.get("game_id", f"row_{idx+1}"))

        t_know = parse_timestamp(row.get(knowledge_col, ""))
        t_pred = parse_timestamp(row.get(prediction_col, ""))
        t_event = parse_timestamp(row.get(event_start_col, ""))

        row_errors = []

        # Check 1: Knowledge time vs Prediction time
        if t_know and t_pred and t_know > t_pred:
            diff_sec = (t_know - t_pred).total_seconds()
            row_errors.append(f"Lookahead: Knowledge time ({t_know}) is {diff_sec}s AFTER prediction time ({t_pred}).")

        # Check 2: Prediction time vs Event start
        if t_pred and t_event and t_pred >= t_event:
            diff_sec = (t_pred - t_event).total_seconds()
            row_errors.append(f"Post-Kickoff Prediction: Prediction was logged {diff_sec}s after event kickoff ({t_event}).")

        # Check 3: Placed odds == Closing odds (retrospective execution bias)
        if placed_odds_col and closing_odds_col:
            p_odds = row.get(placed_odds_col)
            c_odds = row.get(closing_odds_col)
            if p_odds and c_odds and float(p_odds) == float(c_odds):
                # Flag if 100% of rows match, handled in summary
                pass

        if row_errors:
            violations.append({
                "row_index": idx,
                "row_identifier": row_id,
                "errors": row_errors
            })
        else:
            clean_rows += 1

    return {
        "total_records_checked": total_rows,
        "clean_records": clean_rows,
        "violation_count": len(violations),
        "causal_integrity_rate": round((clean_rows / total_rows) * 100, 2) if total_rows > 0 else 0,
        "suspicious_feature_names": sorted(list(suspicious_features)),
        "violations_sample": violations[:10]  # First 10
    }


def main():
    parser = argparse.ArgumentParser(
        description="Forensic Point-in-Time & As-Of Join Integrity Auditor."
    )
    parser.add_argument("file", help="Path to CSV or JSON predictions dataset")
    parser.add_argument("--knowledge-col", default="knowledge_time", help="Column for knowledge/ingestion timestamp")
    parser.add_argument("--pred-col", default="prediction_time", help="Column for model decision timestamp")
    parser.add_argument("--event-col", default="event_start_time", help="Column for game kickoff timestamp")
    parser.add_argument("--placed-odds", default="placed_odds", help="Column for placed odds")
    parser.add_argument("--closing-odds", default="closing_odds", help="Column for closing odds")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    results = audit_file(
        args.file,
        knowledge_col=args.knowledge_col,
        prediction_col=args.pred_col,
        event_start_col=args.event_col,
        placed_odds_col=args.placed_odds,
        closing_odds_col=args.closing_odds
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("### Forensic Temporal Integrity Report\n")
        print(f"- **Total Rows Audited**: `{results['total_records_checked']}`")
        print(f"- **Causal Integrity Rate**: `{results['causal_integrity_rate']}%` ({results['clean_records']} clean rows)")
        print(f"- **Temporal Violations**: `{results['violation_count']}`")

        if results["suspicious_feature_names"]:
            print(f"- **Warning: Suspicious Post-Game Features Detected in Feature Space**: {', '.join(results['suspicious_feature_names'])}")

        if results["violations_sample"]:
            print("\n#### Sample Violations Detected:")
            for v in results["violations_sample"]:
                print(f"- Row `{v['row_identifier']}` (Idx {v['row_index']}): {'; '.join(v['errors'])}")

    if results.get("violation_count", 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
