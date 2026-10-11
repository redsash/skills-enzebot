#!/usr/bin/env python3
"""
estimate_construction_cost.py

Parametric construction cost estimation engine for architectural floor plans.
Generates an AACE Class 4/5 schematic cost estimate range (-15% to +25%)
factoring in:
- Program-differentiated square footage (conditioned living vs. covered terrace vs. utility).
- Exterior 8" CMU masonry takeoffs (wall surface area, block counts).
- Impact-rated hurricane glazing & sliding assemblies.
- Site topography & hillside slope multipliers (foundation & retaining walls).
- Island resilience core (cistern, booster pump/UV, solar array, lithium battery bank, septic).
- Location logistics index & finish specification tiers.
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional, Tuple


LOCATION_MULTIPLIERS = {
    "mainland": 1.00,
    "coastal": 1.15,
    "island": 1.35,
}

TIER_MULTIPLIERS = {
    "economy": 0.80,
    "standard": 1.00,
    "luxury": 1.55,
}

BASE_COST_PER_SQFT = {
    "living_dining": 230.0,
    "kitchen_pantry": 340.0,
    "bedroom_suite": 240.0,
    "bathroom_powder": 310.0,
    "circulation_hall": 160.0,
    "covered_terrace": 110.0,
    "utility_mechanical": 130.0,
    "exterior_hardscape": 65.0,
}


def get_slope_factor(slope_pct: float) -> Tuple[float, str]:
    if slope_pct <= 5.0:
        return 1.00, "Flat (0%–5%): Standard shallow strip footings"
    elif slope_pct <= 12.0:
        return 1.15, "Gentle (6%–12%): Stepped footings & cut/fill"
    elif slope_pct <= 20.0:
        return 1.30, "Moderate (13%–20%): Engineered concrete retaining walls (4'–8')"
    else:
        return 1.55, "Steep Hillside (>20%): Tall retaining walls (>8'), grade beams & pump access"


def estimate_floorplan_cost(
    layout: Dict[str, Any],
    location: str = "island",
    tier: str = "standard",
    slope_pct: float = 12.0,
) -> Dict[str, Any]:
    loc_mult = LOCATION_MULTIPLIERS.get(location.lower(), 1.35)
    tier_mult = TIER_MULTIPLIERS.get(tier.lower(), 1.00)
    slope_mult, slope_desc = get_slope_factor(slope_pct)

    rooms = layout.get("rooms", [])

    # 1. Program Area Breakdown
    area_conditioned = 0.0
    area_covered_terrace = 0.0
    area_utility = 0.0
    area_circulation = 0.0

    program_direct_cost = 0.0

    for r in rooms:
        r_id = r.get("id", "")
        r_name = r.get("name", r_id).lower()
        zone = r.get("zone", "")
        area = float(r.get("area_sqft", 0))

        if zone == "exterior" or "terrace" in r_id or "lanai" in r_name:
            area_covered_terrace += area
            rate = BASE_COST_PER_SQFT["covered_terrace"]
        elif zone == "service" or "mech" in r_id or "cistern" in r_id:
            area_utility += area
            rate = BASE_COST_PER_SQFT["utility_mechanical"]
        elif zone == "circulation" or "hall" in r_id:
            area_circulation += area
            rate = BASE_COST_PER_SQFT["circulation_hall"]
        elif "kitchen" in r_name:
            area_conditioned += area
            rate = BASE_COST_PER_SQFT["kitchen_pantry"]
        elif "powder" in r_name or "bath" in r_name:
            area_conditioned += area
            rate = BASE_COST_PER_SQFT["bathroom_powder"]
        elif "bed" in r_name or "suite" in r_name:
            area_conditioned += area
            rate = BASE_COST_PER_SQFT["bedroom_suite"]
        else:
            area_conditioned += area
            rate = BASE_COST_PER_SQFT["living_dining"]

        # Apply tier and location
        unit_rate = rate * tier_mult * loc_mult
        program_direct_cost += area * unit_rate

    gross_enclosed_area = area_conditioned + area_utility + area_circulation
    total_constructed_area = gross_enclosed_area + area_covered_terrace

    # 2. Structural Masonry Takeoff (Exterior 8" CMU Shell)
    # Estimate perimeter from room bounding boxes or default ratio
    positioned = [r for r in rooms if all(k in r for k in ("x", "y", "w", "h"))]
    if positioned:
        min_x = min(r["x"] for r in positioned)
        max_x = max(r["x"] + r["w"] for r in positioned)
        min_y = min(r["y"] for r in positioned)
        max_y = max(r["y"] + r["h"] for r in positioned)
        exterior_perimeter_ft = 2.0 * ((max_x - min_x) + (max_y - min_y))
    else:
        # Approximation from gross area: rectangular 1:1.5 footprint
        side_a = math.sqrt(gross_enclosed_area / 1.5) if gross_enclosed_area > 0 else 30.0
        exterior_perimeter_ft = 2.0 * (side_a + (side_a * 1.5))

    story_height_ft = float(layout.get("story_height_ft", 10.0))
    gross_wall_area_sqft = exterior_perimeter_ft * story_height_ft

    # Window & door opening deductions
    total_glazing_sqft = 0.0
    for r in rooms:
        for w in r.get("windows", []):
            total_glazing_sqft += float(w.get("width_ft", 4.0)) * float(w.get("height_ft", 4.0))

    if total_glazing_sqft == 0:
        total_glazing_sqft = gross_enclosed_area * 0.12  # default 12% glazing ratio

    net_cmu_wall_sqft = max(0.0, gross_wall_area_sqft - total_glazing_sqft)
    total_cmu_blocks = math.ceil(net_cmu_wall_sqft * 1.125)

    cmu_sqft_cost = 36.0 * loc_mult
    structural_masonry_cost = net_cmu_wall_sqft * cmu_sqft_cost

    # 3. Foundation & Slope Impact Cost
    foundation_base_cost = gross_enclosed_area * (22.0 * loc_mult)
    foundation_with_slope_cost = foundation_base_cost * slope_mult
    slope_premium_cost = foundation_with_slope_cost - foundation_base_cost

    # 4. Hurricane Glazing & Enclosure Package
    impact_glazing_rate = 110.0 * loc_mult * tier_mult  # $/sq ft of impact-rated glazing
    glazing_package_cost = total_glazing_sqft * impact_glazing_rate

    # 5. Island Resilience Core Package
    cistern_gal = float(layout.get("cistern_gallons", 1000))
    cistern_cost = cistern_gal * (2.75 * loc_mult)
    booster_uv_pump_cost = 6200.0 * loc_mult

    solar_kw = float(layout.get("solar_kw", 8.0))
    solar_pv_cost = solar_kw * 1000.0 * (1.85 * loc_mult)
    inverter_ats_cost = 5800.0 * loc_mult

    battery_kwh = float(layout.get("battery_kwh", 20.0))
    battery_cost = battery_kwh * (820.0 * loc_mult)

    septic_cost = 9500.0 * loc_mult

    resilience_core_total = (
        cistern_cost
        + booster_uv_pump_cost
        + solar_pv_cost
        + inverter_ats_cost
        + battery_cost
        + septic_cost
    )

    # 6. Hard Construction Subtotal
    hard_construction_subtotal = (
        program_direct_cost
        + slope_premium_cost
        + (glazing_package_cost * 0.35)  # premium portion over standard openings
        + resilience_core_total
    )

    # 7. Markups: Contractor O&P, Contingency & Soft Costs
    contractor_op_pct = 12.0
    contractor_op_cost = hard_construction_subtotal * (contractor_op_pct / 100.0)

    contingency_pct = 15.0  # AACE Class 4 Schematic Design Contingency
    contingency_cost = (hard_construction_subtotal + contractor_op_cost) * (contingency_pct / 100.0)

    soft_costs_pct = 8.0  # Architectural, engineering, permitting, surveying
    soft_costs = hard_construction_subtotal * (soft_costs_pct / 100.0)

    total_project_expected = hard_construction_subtotal + contractor_op_cost + contingency_cost + soft_costs

    # 8. Confidence Range (AACE Class 4/5: -15% to +25%)
    low_bound_cost = total_project_expected * 0.85
    high_bound_cost = total_project_expected * 1.25

    cost_per_sqft_conditioned = total_project_expected / area_conditioned if area_conditioned > 0 else 0
    cost_per_sqft_total = total_project_expected / total_constructed_area if total_constructed_area > 0 else 0

    return {
        "project": layout.get("project", "Resilient Building Layout"),
        "parameters": {
            "location": location,
            "location_multiplier": loc_mult,
            "finish_tier": tier,
            "tier_multiplier": tier_mult,
            "slope_percent": slope_pct,
            "slope_multiplier": slope_mult,
            "slope_description": slope_desc,
        },
        "areas": {
            "conditioned_sqft": round(area_conditioned, 1),
            "covered_terrace_sqft": round(area_covered_terrace, 1),
            "utility_sqft": round(area_utility, 1),
            "circulation_sqft": round(area_circulation, 1),
            "gross_enclosed_sqft": round(gross_enclosed_area, 1),
            "total_constructed_sqft": round(total_constructed_area, 1),
        },
        "takeoffs": {
            "exterior_perimeter_ft": round(exterior_perimeter_ft, 1),
            "net_cmu_wall_sqft": round(net_cmu_wall_sqft, 1),
            "cmu_block_count": total_cmu_blocks,
            "impact_glazing_sqft": round(total_glazing_sqft, 1),
            "cistern_capacity_gal": cistern_gal,
            "solar_array_kw": solar_kw,
            "battery_storage_kwh": battery_kwh,
        },
        "itemized_budgets": {
            "program_finishes_and_mep": round(program_direct_cost, 2),
            "foundation_and_slope_premium": round(slope_premium_cost, 2),
            "hurricane_impact_glazing_premium": round(glazing_package_cost * 0.35, 2),
            "resilience_core": {
                "cistern_and_water_security": round(cistern_cost + booster_uv_pump_cost, 2),
                "solar_battery_and_ats": round(solar_pv_cost + inverter_ats_cost + battery_cost, 2),
                "septic_and_drainage": round(septic_cost, 2),
                "total": round(resilience_core_total, 2),
            },
            "hard_construction_subtotal": round(hard_construction_subtotal, 2),
            "contractor_op_12pct": round(contractor_op_cost, 2),
            "design_contingency_15pct": round(contingency_cost, 2),
            "soft_costs_ae_permits_8pct": round(soft_costs, 2),
        },
        "confidence_range": {
            "aace_class": "Class 4 (Schematic Design)",
            "accuracy_band": "-15% to +25%",
            "low_bound_usd": round(low_bound_cost, 0),
            "expected_median_usd": round(total_project_expected, 0),
            "high_bound_usd": round(high_bound_cost, 0),
        },
        "unit_rates": {
            "cost_per_sqft_conditioned": round(cost_per_sqft_conditioned, 1),
            "cost_per_sqft_total_constructed": round(cost_per_sqft_total, 1),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parametric construction cost estimation with AACE Class 4 confidence intervals (-15% to +25%)."
    )
    parser.add_argument("--spec", help="Path to floor plan specification JSON file")
    parser.add_argument("--demo", action="store_true", help="Run estimate on built-in resilient villa reference specification")
    parser.add_argument(
        "--location",
        choices=["mainland", "coastal", "island"],
        default="island",
        help="Location & logistics multiplier (default: island, 1.35x)",
    )
    parser.add_argument(
        "--tier",
        choices=["economy", "standard", "luxury"],
        default="standard",
        help="Finish quality tier (default: standard)",
    )
    parser.add_argument(
        "--slope",
        type=float,
        default=12.0,
        help="Site topography slope gradient percentage (default: 12.0%%)",
    )
    parser.add_argument("--json", action="store_true", help="Output cost estimate in JSON format")

    args = parser.parse_args()

    # Import DEMO_LAYOUT from audit_spatial_ux if available
    try:
        from audit_spatial_ux import DEMO_LAYOUT
    except ImportError:
        # Fallback minimal spec
        DEMO_LAYOUT = {
            "project": "Resilient Coastal Villa",
            "rooms": [
                {"id": "living", "name": "Great Room", "zone": "public", "area_sqft": 384, "w": 24, "h": 16},
                {"id": "kitchen", "name": "Kitchen", "zone": "public", "area_sqft": 256, "w": 16, "h": 16},
                {"id": "bed_m", "name": "Primary Suite", "zone": "private", "area_sqft": 240, "w": 20, "h": 12},
                {"id": "bed_g", "name": "Guest Suite", "zone": "private", "area_sqft": 160, "w": 16, "h": 10},
                {"id": "powder", "name": "Powder Room", "zone": "public", "area_sqft": 48, "w": 8, "h": 6},
                {"id": "terrace", "name": "Lanai", "zone": "exterior", "area_sqft": 240, "w": 24, "h": 10},
                {"id": "utility", "name": "Laundry & Power", "zone": "service", "area_sqft": 160, "w": 16, "h": 10},
            ],
            "cistern_gallons": 1000,
            "solar_kw": 8.0,
            "battery_kwh": 20.0,
        }

    if args.demo:
        spec = DEMO_LAYOUT
    elif args.spec:
        try:
            with open(args.spec, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Error reading spec '{args.spec}': {e}\n")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    est = estimate_floorplan_cost(
        spec,
        location=args.location,
        tier=args.tier,
        slope_pct=args.slope,
    )

    if args.json:
        json.dump(est, sys.stdout, indent=2)
        print()
        return

    # Formatted Markdown Cost Schedule
    cr = est["confidence_range"]
    ar = est["areas"]
    ib = est["itemized_budgets"]
    rc = ib["resilience_core"]
    tk = est["takeoffs"]
    ur = est["unit_rates"]
    pm = est["parameters"]

    print(f"### Parametric Construction Cost Estimate: {est['project']}")
    print(f"**Classification:** {cr['aace_class']} ({cr['accuracy_band']})")
    print(f"**Site Parameters:** Location: {pm['location'].capitalize()} ({pm['location_multiplier']}x) | Finish Tier: {pm['finish_tier'].capitalize()} | Slope: {pm['slope_percent']}% ({pm['slope_description']})\n")

    print("#### 📊 Executive Budget Summary")
    print(f"- **Low Confidence Bound (-15%):** **${cr['low_bound_usd']:,.0f}**")
    print(f"- **Expected Baseline (Median):**   **${cr['expected_median_usd']:,.0f}**")
    print(f"- **High Confidence Bound (+25%):**  **${cr['high_bound_usd']:,.0f}**")
    print(f"- **Unit Rate (Conditioned Area):** ${ur['cost_per_sqft_conditioned']:,.1f} / sq ft ({ar['conditioned_sqft']} sq ft)")
    print(f"- **Unit Rate (Total Constructed):** ${ur['cost_per_sqft_total_constructed']:,.1f} / sq ft ({ar['total_constructed_sqft']} sq ft)\n")

    print("#### 📐 Program Area & Material Takeoffs")
    print("| Takeoff Element | Quantity | Unit | Notes |")
    print("| :--- | :--- | :--- | :--- |")
    print(f"| Conditioned Living Space | {ar['conditioned_sqft']:,.0f} | sq ft | Finished interior HVAC areas |")
    print(f"| Covered Lanai / Terrace | {ar['covered_terrace_sqft']:,.0f} | sq ft | Outdoor covered slab & rafters |")
    print(f"| Utility / Mechanical Core | {ar['utility_sqft']:,.0f} | sq ft | Dedicated power & water plant |")
    print(f"| Exterior 8\" CMU Net Wall | {tk['net_cmu_wall_sqft']:,.0f} | sq ft | Shell wall surface area |")
    print(f"| CMU Masonry Units | {tk['cmu_block_count']:,} | blocks | Modular 8\"x8\"x16\" stretcher units |")
    print(f"| Impact Hurricane Glazing | {tk['impact_glazing_sqft']:,.0f} | sq ft | DP >= 50-70 psf rated windows/sliders |")
    print(f"| Concrete Cistern Capacity | {tk['cistern_capacity_gal']:,.0f} | gal | Sub-slab potable water vault |")
    print(f"| Solar PV Array | {tk['solar_array_kw']:.1f} | kW DC | Roof-mounted microgrid array |")
    print(f"| Lithium Battery Storage | {tk['battery_storage_kwh']:.1f} | kWh | LiFePO4 resilient energy bank |")
    print()

    print("#### 💰 Itemized CSI Budget Breakdown")
    print("| Budget Category | Cost (USD) | % of Total |")
    print("| :--- | :--- | :--- |")
    print(f"| Program Finishes & Interior MEP | ${ib['program_finishes_and_mep']:,.0f} | {(ib['program_finishes_and_mep'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| Foundation & Slope Premium ({pm['slope_percent']}%) | ${ib['foundation_and_slope_premium']:,.0f} | {(ib['foundation_and_slope_premium'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| Hurricane Impact Glazing Premium | ${ib['hurricane_impact_glazing_premium']:,.0f} | {(ib['hurricane_impact_glazing_premium'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| Resilience Core (Cistern, Solar/Battery, Septic) | ${rc['total']:,.0f} | {(rc['total'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| *— Cistern & Booster/UV Station* | *${rc['cistern_and_water_security']:,.0f}* | *—* |")
    print(f"| *— Solar PV, Hybrid Inverter & Batteries* | *${rc['solar_battery_and_ats']:,.0f}* | *—* |")
    print(f"| *— Septic & Percolation Leach Field* | *${rc['septic_and_drainage']:,.0f}* | *—* |")
    print(f"| **Hard Construction Subtotal** | **${ib['hard_construction_subtotal']:,.0f}** | **{(ib['hard_construction_subtotal'] / cr['expected_median_usd'])*100:.1f}%** |")
    print(f"| Contractor Overhead & Profit (12%) | ${ib['contractor_op_12pct']:,.0f} | {(ib['contractor_op_12pct'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| Design & Estimating Contingency (15%) | ${ib['design_contingency_15pct']:,.0f} | {(ib['design_contingency_15pct'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| A&E Design, Engineering & Permits (8%) | ${ib['soft_costs_ae_permits_8pct']:,.0f} | {(ib['soft_costs_ae_permits_8pct'] / cr['expected_median_usd'])*100:.1f}% |")
    print(f"| **Total Project Expected (Median)** | **${cr['expected_median_usd']:,.0f}** | **100.0%** |")
    print()


if __name__ == "__main__":
    main()
