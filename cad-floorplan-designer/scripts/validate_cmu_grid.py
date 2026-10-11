#!/usr/bin/env python3
"""
validate_cmu_grid.py

Validates architectural spans, building footprints, and site setback envelopes
against standard Concrete Masonry Unit (CMU) modular grid increments (8" and 16").

Standards:
- Standard stretcher block: 8" x 8" x 16" nominal (includes 3/8" mortar joint).
- Modular increments: Spans must divide evenly by 8" (half block) or 16" (full block).
"""

import argparse
import json
import math
import re
import sys
from typing import Dict, List, Optional, Tuple


def parse_dimension(dim_str: str) -> float:
    """
    Parse a dimension string into total inches.
    Supports formats:
      - 24' 8", 24'-8", 24ft 8in, 24'8"
      - 24' (feet only)
      - 8" (inches only)
      - 296 (raw integer/float assumed inches)
      - 24.5' (decimal feet)
    """
    s = str(dim_str).strip()
    if not s:
        raise ValueError("Empty dimension string")

    # Pure number -> assumed inches
    try:
        return float(s)
    except ValueError:
        pass

    # Feet and inches: e.g. 24' 8", 24'-8", 24ft 8in
    ft_in_pattern = re.compile(
        r"""^\s*
        (?:(?P<feet>\d+(?:\.\d+)?)\s*(?:'|ft|feet)\s*[-]?\s*)?
        (?:(?P<inches>\d+(?:\.\d+)?)\s*(?:"|in|inches)?)?
        \s*$""",
        re.VERBOSE | re.IGNORECASE,
    )

    match = ft_in_pattern.match(s)
    if match and (match.group("feet") or match.group("inches")):
        feet = float(match.group("feet") or 0)
        inches = float(match.group("inches") or 0)
        return (feet * 12.0) + inches

    # Decimal feet: e.g. 24.5'
    if s.endswith("'") or s.lower().endswith("ft"):
        num_str = re.sub(r"[^\d.]", "", s)
        return float(num_str) * 12.0

    # Decimal inches: e.g. 192"
    if s.endswith('"') or s.lower().endswith("in"):
        num_str = re.sub(r"[^\d.]", "", s)
        return float(num_str)

    raise ValueError(f"Unable to parse dimension: '{dim_str}'")


def format_feet_inches(total_inches: float) -> str:
    """Convert inches to standard architectural feet and inches string."""
    feet = int(total_inches // 12)
    rem_inches = total_inches - (feet * 12)
    if abs(rem_inches - round(rem_inches)) < 1e-4:
        return f"{feet}'-{int(round(rem_inches))}\""
    return f"{feet}'-{rem_inches:.2f}\""


def check_cmu_modularity(inches: float) -> Dict:
    """
    Analyze if an inch dimension conforms to 8" (half block) and 16" (full block) CMU modular units.
    """
    is_exact_16 = (inches % 16.0) == 0
    is_exact_8 = (inches % 8.0) == 0

    full_blocks = int(inches // 16)
    remainder = inches % 16.0
    half_blocks = 1 if remainder >= 8.0 else 0
    excess_inches = remainder - (half_blocks * 8.0)

    snap_down_8 = math.floor(inches / 8.0) * 8.0
    snap_up_8 = math.ceil(inches / 8.0) * 8.0
    snap_down_16 = math.floor(inches / 16.0) * 16.0
    snap_up_16 = math.ceil(inches / 16.0) * 16.0

    status = "FULL_BLOCK_ALIGNED" if is_exact_16 else ("HALF_BLOCK_ALIGNED" if is_exact_8 else "OFF_GRID")

    return {
        "raw_inches": inches,
        "formatted": format_feet_inches(inches),
        "status": status,
        "is_modular_8": is_exact_8,
        "is_modular_16": is_exact_16,
        "full_blocks_16in": full_blocks,
        "half_blocks_8in": half_blocks,
        "off_grid_variance_in": round(excess_inches, 3),
        "recommendations": {
            "snap_down_8in": {
                "inches": snap_down_8,
                "formatted": format_feet_inches(snap_down_8),
                "delta_in": round(snap_down_8 - inches, 2),
            },
            "snap_up_8in": {
                "inches": snap_up_8,
                "formatted": format_feet_inches(snap_up_8),
                "delta_in": round(snap_up_8 - inches, 2),
            },
            "snap_down_16in": {
                "inches": snap_down_16,
                "formatted": format_feet_inches(snap_down_16),
                "delta_in": round(snap_down_16 - inches, 2),
            },
            "snap_up_16in": {
                "inches": snap_up_16,
                "formatted": format_feet_inches(snap_up_16),
                "delta_in": round(snap_up_16 - inches, 2),
            },
        },
    }


def calculate_buildable_envelope(
    lot_width: float,
    lot_depth: float,
    front_setback: float,
    rear_setback: float,
    left_setback: float,
    right_setback: float,
) -> Dict:
    """
    Calculate maximum buildable footprint inside zoning setbacks,
    and snap outer structural dimensions inward to the nearest CMU 16" and 8" modules.
    """
    raw_buildable_width = lot_width - (left_setback + right_setback)
    raw_buildable_depth = lot_depth - (front_setback + rear_setback)

    if raw_buildable_width <= 0 or raw_buildable_depth <= 0:
        return {
            "error": "Setbacks exceed lot boundaries. No buildable envelope remains.",
            "raw_width_in": raw_buildable_width,
            "raw_depth_in": raw_buildable_depth,
        }

    # Snap INWARD (downward) to guarantee zoning setback compliance
    snapped_width_16 = math.floor(raw_buildable_width / 16.0) * 16.0
    snapped_depth_16 = math.floor(raw_buildable_depth / 16.0) * 16.0
    snapped_width_8 = math.floor(raw_buildable_width / 8.0) * 8.0
    snapped_depth_8 = math.floor(raw_buildable_depth / 8.0) * 8.0

    lot_area_sqft = (lot_width * lot_depth) / 144.0
    envelope_16_sqft = (snapped_width_16 * snapped_depth_16) / 144.0
    envelope_8_sqft = (snapped_width_8 * snapped_depth_8) / 144.0

    coverage_ratio_16 = (envelope_16_sqft / lot_area_sqft) * 100.0 if lot_area_sqft > 0 else 0.0

    return {
        "lot": {
            "width": format_feet_inches(lot_width),
            "depth": format_feet_inches(lot_depth),
            "area_sqft": round(lot_area_sqft, 1),
            "area_sqm": round(lot_area_sqft * 0.092903, 1),
        },
        "setbacks": {
            "front": format_feet_inches(front_setback),
            "rear": format_feet_inches(rear_setback),
            "left": format_feet_inches(left_setback),
            "right": format_feet_inches(right_setback),
        },
        "unadjusted_envelope": {
            "width": format_feet_inches(raw_buildable_width),
            "depth": format_feet_inches(raw_buildable_depth),
        },
        "snapped_envelope_16in": {
            "width": format_feet_inches(snapped_width_16),
            "depth": format_feet_inches(snapped_depth_16),
            "width_inches": snapped_width_16,
            "depth_inches": snapped_depth_16,
            "blocks_wide": int(snapped_width_16 // 16),
            "blocks_deep": int(snapped_depth_16 // 16),
            "footprint_sqft": round(envelope_16_sqft, 1),
            "footprint_sqm": round(envelope_16_sqft * 0.092903, 1),
            "lot_coverage_pct": round(coverage_ratio_16, 2),
        },
        "snapped_envelope_8in": {
            "width": format_feet_inches(snapped_width_8),
            "depth": format_feet_inches(snapped_depth_8),
            "footprint_sqft": round(envelope_8_sqft, 1),
            "footprint_sqm": round(envelope_8_sqft * 0.092903, 1),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate architectural spans and site envelopes against CMU 8-inch/16-inch modular grids."
    )
    parser.add_argument(
        "--check-spans",
        nargs="+",
        metavar="SPAN",
        help="One or more span dimensions to check (e.g. \"24' 8\\\"\" \"16'-0\\\"\" \"296\")",
    )
    parser.add_argument(
        "--site-envelope",
        action="store_true",
        help="Calculate buildable envelope and snap footprint to CMU grid",
    )
    parser.add_argument("--lot-width", help="Lot width dimension (e.g. \"60' 0\\\"\")")
    parser.add_argument("--lot-depth", help="Lot depth dimension (e.g. \"100' 0\\\"\")")
    parser.add_argument("--front-setback", default="20' 0\"", help="Front setback (default: 20'-0\")")
    parser.add_argument("--rear-setback", default="15' 0\"", help="Rear setback (default: 15'-0\")")
    parser.add_argument("--side-setback", help="Uniform side setback (applied to left and right)")
    parser.add_argument("--left-setback", default="10' 0\"", help="Left side setback (default: 10'-0\")")
    parser.add_argument("--right-setback", default="10' 0\"", help="Right side setback (default: 10'-0\")")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    results = {}

    if args.check_spans:
        span_results = []
        for raw_s in args.check_spans:
            try:
                inches = parse_dimension(raw_s)
                res = check_cmu_modularity(inches)
                res["input"] = raw_s
                span_results.append(res)
            except Exception as e:
                span_results.append({"input": raw_s, "error": str(e)})
        results["spans"] = span_results

    if args.site_envelope:
        if not args.lot_width or not args.lot_depth:
            sys.stderr.write("Error: --site-envelope requires --lot-width and --lot-depth.\n")
            sys.exit(1)

        try:
            lw = parse_dimension(args.lot_width)
            ld = parse_dimension(args.lot_depth)
            fs = parse_dimension(args.front_setback)
            rs = parse_dimension(args.rear_setback)
            ls = parse_dimension(args.side_setback or args.left_setback)
            rgs = parse_dimension(args.side_setback or args.right_setback)

            results["envelope"] = calculate_buildable_envelope(lw, ld, fs, rs, ls, rgs)
        except Exception as e:
            sys.stderr.write(f"Error calculating envelope: {e}\n")
            sys.exit(1)

    if not results:
        parser.print_help()
        sys.exit(0)

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
        return

    # Formatted Markdown Table Output
    if "spans" in results:
        print("### CMU Modular Grid Validation")
        print("| Input | Dimension | Status | 16\" Blocks | 8\" Half-Blocks | Off-Grid Err | Snap Down (16\") | Snap Up (16\") |")
        print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for s in results["spans"]:
            if "error" in s:
                print(f"| {s['input']} | ERROR | {s['error']} | - | - | - | - | - |")
            else:
                stat = "✅ Full (16\")" if s["is_modular_16"] else ("⚠️ Half (8\")" if s["is_modular_8"] else "❌ Off-Grid")
                err_str = f"{s['off_grid_variance_in']}\"" if s['off_grid_variance_in'] else "0\""
                down16 = s["recommendations"]["snap_down_16in"]["formatted"]
                up16 = s["recommendations"]["snap_up_16in"]["formatted"]
                print(f"| {s['input']} | {s['formatted']} | {stat} | {s['full_blocks_16in']} | {s['half_blocks_8in']} | {err_str} | {down16} | {up16} |")
        print()

    if "envelope" in results:
        env = results["envelope"]
        if "error" in env:
            print(f"**Envelope Error:** {env['error']}")
        else:
            print("### Site & Buildable Envelope Calibration")
            print(f"- **Lot Dimensions:** {env['lot']['width']} x {env['lot']['depth']} ({env['lot']['area_sqft']} sq ft / {env['lot']['area_sqm']} m²)")
            print(f"- **Mandatory Setbacks:** Front: {env['setbacks']['front']} | Rear: {env['setbacks']['rear']} | Sides: {env['setbacks']['left']} / {env['setbacks']['right']}")
            print(f"- **Unadjusted Buildable Area:** {env['unadjusted_envelope']['width']} x {env['unadjusted_envelope']['depth']}")
            print(f"- **Snapped CMU Modular Footprint (16\"):** **{env['snapped_envelope_16in']['width']} x {env['snapped_envelope_16in']['depth']}**")
            print(f"  - Modular Span: {env['snapped_envelope_16in']['blocks_wide']} blocks wide x {env['snapped_envelope_16in']['blocks_deep']} blocks deep")
            print(f"  - Ground Footprint: {env['snapped_envelope_16in']['footprint_sqft']} sq ft ({env['snapped_envelope_16in']['footprint_sqm']} m²)")
            print(f"  - Lot Coverage Ratio: {env['snapped_envelope_16in']['lot_coverage_pct']}%")
            print()


if __name__ == "__main__":
    main()
