#!/usr/bin/env python3
"""
audit_spatial_ux.py

Multi-pillar validation engine for architectural floor plans and spatial layouts:
1. Geometric & Structural Validity (non-overlapping rooms, dimensional conservation).
2. Building Code & Life Safety Compliance (IRC R310 egress, IRC R304 minimums, IRC R303 light/vent).
3. Ergonomics & Furniture Clearance Envelopes (36" circulation walking lanes around furniture).
4. Spatial UX & Circulation Flow (corridor widths, door collisions, acoustic/visual privacy, transit).
5. Exports clean, spec-compliant Mermaid circulation graphs.
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


DEMO_LAYOUT = {
    "project": "Villa Resiliente",
    "gross_footprint_sqft": 1800,
    "rooms": [
        {
            "id": "entry",
            "name": "Main Foyer",
            "zone": "public",
            "area_sqft": 80,
            "x": 0, "y": 14, "w": 8, "h": 10,
            "windows": [{"width_ft": 3.0, "height_ft": 3.0, "operable_pct": 50}],
        },
        {
            "id": "living",
            "name": "Great Room & Dining",
            "zone": "public",
            "area_sqft": 336,
            "x": 8, "y": 12, "w": 24, "h": 14,
            "windows": [{"width_ft": 10.0, "height_ft": 5.0, "operable_pct": 50}],
            "furniture": ["sofa_group", "dining_table_6p"],
        },
        {
            "id": "kitchen",
            "name": "Kitchen & Pantry",
            "zone": "public",
            "area_sqft": 256,
            "x": 32, "y": 10, "w": 16, "h": 16,
            "windows": [{"width_ft": 6.0, "height_ft": 4.0, "operable_pct": 100}],
        },
        {
            "id": "terrace",
            "name": "Covered Lanai / Pool",
            "zone": "exterior",
            "area_sqft": 240,
            "x": 8, "y": 26, "w": 24, "h": 10,
        },
        {
            "id": "hall_bed",
            "name": "Bedroom Hall Baffle",
            "zone": "circulation",
            "area_sqft": 64,
            "x": 0, "y": 6, "w": 8, "h": 8,
        },
        {
            "id": "powder",
            "name": "Guest Powder Room",
            "zone": "public",
            "area_sqft": 48,
            "x": 0, "y": 0, "w": 8, "h": 6,
            "wc_front_clearance_in": 24,
            "wc_centerline_clearance_in": 16,
        },
        {
            "id": "bed_master",
            "name": "Primary Suite",
            "zone": "private",
            "area_sqft": 240,
            "x": 8, "y": 0, "w": 20, "h": 12,
            "is_sleeping_room": True,
            "windows": [
                {
                    "width_ft": 6.0,
                    "height_ft": 4.0,
                    "clear_width_in": 28,
                    "clear_height_in": 40,
                    "sill_height_in": 36,
                    "operable_pct": 50,
                }
            ],
            "furniture": ["king_bed"],
        },
        {
            "id": "bed_guest",
            "name": "Guest Bedroom",
            "zone": "private",
            "area_sqft": 160,
            "x": 32, "y": 0, "w": 16, "h": 10,
            "is_sleeping_room": True,
            "windows": [
                {
                    "width_ft": 5.0,
                    "height_ft": 4.0,
                    "clear_width_in": 24,
                    "clear_height_in": 36,
                    "sill_height_in": 36,
                    "operable_pct": 50,
                }
            ],
            "furniture": ["queen_bed"],
        },
        {
            "id": "laundry",
            "name": "Laundry & Beach Wash",
            "zone": "service",
            "area_sqft": 80,
            "x": 32, "y": 26, "w": 8, "h": 10,
        },
        {
            "id": "mech",
            "name": "Inverter, Battery & ATS Room",
            "zone": "service",
            "area_sqft": 80,
            "x": 40, "y": 26, "w": 8, "h": 10,
        },
        {
            "id": "cistern",
            "name": "Cistern & Booster Pump",
            "zone": "service",
            "area_sqft": 80,
            "x": 40, "y": 36, "w": 8, "h": 10,
        },
    ],
    "connections": [
        {"from": "entry", "to": "living", "type": "arterial_corridor", "width_in": 48, "traffic": "high"},
        {"from": "living", "to": "kitchen", "type": "open_threshold", "width_in": 72, "traffic": "high"},
        {"from": "living", "to": "terrace", "type": "exterior_slider", "width_in": 96, "traffic": "high", "step_down_in": 2.0},
        {"from": "entry", "to": "powder", "type": "doorway", "width_in": 36, "traffic": "medium", "direct_sightline": False},
        {"from": "entry", "to": "hall_bed", "type": "secondary_hall", "width_in": 42, "traffic": "medium"},
        {"from": "hall_bed", "to": "bed_master", "type": "doorway", "width_in": 36, "traffic": "medium", "swing_into_room": True},
        {"from": "hall_bed", "to": "bed_guest", "type": "doorway", "width_in": 36, "traffic": "low", "swing_into_room": True},
        {"from": "kitchen", "to": "laundry", "type": "doorway", "width_in": 36, "traffic": "medium", "swing_into_room": True},
        {"from": "terrace", "to": "laundry", "type": "exterior_door", "width_in": 36, "traffic": "medium", "step_down_in": 2.0, "wet_route": True},
        {"from": "laundry", "to": "mech", "type": "fire_door", "width_in": 36, "traffic": "low", "fire_rated_min": 60},
        {"from": "mech", "to": "cistern", "type": "access_door", "width_in": 36, "traffic": "low"},
    ],
    "shared_walls": [
        {"room_a": "mech", "room_b": "bed_guest", "acoustic_decoupled": True, "wall_type": "8in CMU with resilient channel"},
        {"room_a": "powder", "room_b": "living", "acoustic_decoupled": True, "wall_type": "Insulated drywall"},
    ],
}


STANDARD_FURNITURE_ENVELOPES = {
    "king_bed": {"min_w_ft": 11.0, "min_h_ft": 12.0, "desc": "King Bed (76\"x80\") with nightstands and 36\" walking perimeter"},
    "queen_bed": {"min_w_ft": 10.0, "min_h_ft": 10.0, "desc": "Queen Bed (60\"x80\") with nightstand and 36\" walking lane"},
    "dining_table_6p": {"min_w_ft": 10.0, "min_h_ft": 11.0, "desc": "6-Seat Dining Table (36\"x72\") with 36\" chair pushback"},
    "sofa_group": {"min_w_ft": 11.0, "min_h_ft": 12.0, "desc": "Living Sofa Group with coffee table and 36\" circulation lanes"},
}


def audit_geometry(layout: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Audit Pillar 1: Geometric & Structural Validity (non-overlapping rooms, dimensional sums)."""
    issues = []
    passes = []
    rooms = layout.get("rooms", [])

    # 1. 2D Bounding Box Collision Check
    positioned_rooms = [r for r in rooms if all(k in r for k in ("x", "y", "w", "h"))]
    for i in range(len(positioned_rooms)):
        for j in range(i + 1, len(positioned_rooms)):
            r1 = positioned_rooms[i]
            r2 = positioned_rooms[j]

            # Compute overlap rectangle
            x_overlap = max(0.0, min(r1["x"] + r1["w"], r2["x"] + r2["w"]) - max(r1["x"], r2["x"]))
            y_overlap = max(0.0, min(r1["y"] + r1["h"], r2["y"] + r2["h"]) - max(r1["y"], r2["y"]))
            overlap_area = x_overlap * y_overlap

            # If overlap area > 0.1 sq ft, flag illegal spatial collision
            if overlap_area > 0.1:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Geometric Validity",
                    "category": "Room Polygon Overlap",
                    "message": f"Illegal overlap between '{r1['name']}' and '{r2['name']}': {overlap_area:.1f} sq ft area intersection.",
                })

    if positioned_rooms and not any(i["category"] == "Room Polygon Overlap" for i in issues):
        passes.append({
            "pillar": "Geometric Validity",
            "category": "Non-Overlapping Elements",
            "message": f"All {len(positioned_rooms)} positioned rooms are mutually disjoint with zero interior area collisions.",
        })

    # 2. Dimensional Conservation Check
    net_interior_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("zone") != "exterior")
    gross_footprint = layout.get("gross_footprint_sqft", 0)
    if gross_footprint > 0:
        wall_and_circ_buffer = gross_footprint - net_interior_area
        wall_pct = (wall_and_circ_buffer / gross_footprint) * 100.0

        if net_interior_area > gross_footprint:
            issues.append({
                "level": "FAIL",
                "pillar": "Geometric Validity",
                "category": "Dimensional Hallucination",
                "message": f"Net interior room area ({net_interior_area} sq ft) exceeds gross footprint ({gross_footprint} sq ft) by {abs(wall_and_circ_buffer):.1f} sq ft.",
            })
        elif wall_pct < 8.0:
            issues.append({
                "level": "WARN",
                "pillar": "Geometric Validity",
                "category": "Wall Footprint Budget",
                "message": f"Wall structure budget is only {wall_pct:.1f}% ({wall_and_circ_buffer:.1f} sq ft); standard CMU construction requires 10%–15% for structural walls.",
            })
        else:
            passes.append({
                "pillar": "Geometric Validity",
                "category": "Dimensional Conservation",
                "message": f"Interior net area ({net_interior_area} sq ft) fits realistically within gross footprint ({gross_footprint} sq ft) with {wall_pct:.1f}% wall/structure allowance.",
            })

    return issues, passes


def audit_building_codes(layout: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Audit Pillar 2: Architectural & Building Code Compliance (IRC R310, R304, R303, R307)."""
    issues = []
    passes = []
    rooms = layout.get("rooms", [])

    for r in rooms:
        r_name = r.get("name", r.get("id"))
        zone = r.get("zone", "")
        area = r.get("area_sqft", 0)
        is_sleeping = r.get("is_sleeping_room", False) or (zone == "private" and ("bed" in r_name.lower() or "suite" in r_name.lower()))
        is_habitable = zone in ["public", "private"] and r.get("id") not in ["powder", "bath", "laundry", "mech", "cistern"]

        # 1. IRC R310: Emergency Escape & Rescue Openings (Egress Windows)
        if is_sleeping:
            windows = r.get("windows", [])
            has_valid_egress = False
            for w in windows:
                cw = w.get("clear_width_in", 0)
                ch = w.get("clear_height_in", 0)
                sill = w.get("sill_height_in", 48)
                clear_area_sqft = (cw * ch) / 144.0

                if cw >= 20 and ch >= 24 and clear_area_sqft >= 5.7 and sill <= 44:
                    has_valid_egress = True
                    break

            if not windows:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R310 Egress Opening",
                    "message": f"Sleeping room '{r_name}' has no exterior windows designated for emergency egress.",
                })
            elif not has_valid_egress:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R310 Egress Violation",
                    "message": f"Sleeping room '{r_name}' windows fail IRC R310 egress standards (requires: net clear area >= 5.7 sq ft, width >= 20\", height >= 24\", sill height <= 44\").",
                })
            else:
                passes.append({
                    "pillar": "Building Code",
                    "category": "IRC R310 Egress",
                    "message": f"Sleeping room '{r_name}' meets IRC emergency escape opening compliance.",
                })

        # 2. IRC R304: Minimum Habitable Room Area & Dimensions
        if is_habitable and area > 0:
            if area < 70:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R304 Minimum Room Area",
                    "message": f"Habitable space '{r_name}' is {area} sq ft (minimum 70 sq ft required by code).",
                })
            else:
                passes.append({
                    "pillar": "Building Code",
                    "category": "IRC R304 Room Size",
                    "message": f"Habitable room '{r_name}' meets minimum 70 sq ft code standard ({area} sq ft).",
                })

            w_dim = r.get("w", 0)
            h_dim = r.get("h", 0)
            if w_dim > 0 and h_dim > 0 and min(w_dim, h_dim) < 7.0:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R304 Minimum Dimension",
                    "message": f"Habitable space '{r_name}' has horizontal dimension {min(w_dim, h_dim)} ft (minimum 7 ft required).",
                })

        # 3. IRC R303: Natural Light (8%) and Ventilation (4%)
        if is_habitable and area > 0:
            windows = r.get("windows", [])
            total_glazing_sqft = sum(w.get("width_ft", 0) * w.get("height_ft", 0) for w in windows)
            glazing_ratio = (total_glazing_sqft / area) * 100.0 if area > 0 else 0

            if total_glazing_sqft == 0:
                issues.append({
                    "level": "WARN",
                    "pillar": "Building Code",
                    "category": "IRC R303 Natural Light",
                    "message": f"Habitable space '{r_name}' has no natural daylight glazing specified.",
                })
            elif glazing_ratio < 8.0:
                issues.append({
                    "level": "WARN",
                    "pillar": "Building Code",
                    "category": "IRC R303 Glazing Deficit",
                    "message": f"Habitable room '{r_name}' glazed area is {glazing_ratio:.1f}% of floor area (minimum 8% required).",
                })
            else:
                passes.append({
                    "pillar": "Building Code",
                    "category": "IRC R303 Light & Air",
                    "message": f"Room '{r_name}' glazed window area complies with code ({glazing_ratio:.1f}% >= 8%).",
                })

        # 4. IRC R307: Sanitary Clearances
        if "powder" in r.get("id", "") or "bath" in r.get("id", ""):
            front_clear = r.get("wc_front_clearance_in", 21)
            center_clear = r.get("wc_centerline_clearance_in", 15)
            if front_clear < 21:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R307 Fixture Clearance",
                    "message": f"Water closet front clearance in '{r_name}' is {front_clear}\" (minimum 21\" required).",
                })
            if center_clear < 15:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Building Code",
                    "category": "IRC R307 Fixture Centerline",
                    "message": f"Water closet centerline clearance in '{r_name}' is {center_clear}\" (minimum 15\" to side partition required).",
                })

    return issues, passes


def audit_furniture_clearances(layout: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Audit Pillar 3: Furniture Clearance Envelopes & Ergonomic Walkability."""
    issues = []
    passes = []
    rooms = layout.get("rooms", [])

    for r in rooms:
        furniture_list = r.get("furniture", [])
        rw = r.get("w", 0)
        rh = r.get("h", 0)
        r_name = r.get("name", r.get("id"))

        if rw == 0 or rh == 0:
            continue

        for furn_key in furniture_list:
            spec = STANDARD_FURNITURE_ENVELOPES.get(furn_key)
            if not spec:
                continue

            min_w = spec["min_w_ft"]
            min_h = spec["min_h_ft"]

            fits_normal = rw >= min_w and rh >= min_h
            fits_rotated = rw >= min_h and rh >= min_w

            if not fits_normal and not fits_rotated:
                issues.append({
                    "level": "WARN",
                    "pillar": "Ergonomics & Furniture",
                    "category": "Furniture Clearance Pinch",
                    "message": f"Room '{r_name}' ({rw}' x {rh}') cannot comfortably accommodate {spec['desc']} without violating 36\" walking lanes.",
                })
            else:
                passes.append({
                    "pillar": "Ergonomics & Furniture",
                    "category": "Furniture Fit",
                    "message": f"Room '{r_name}' provides full 36\" walking perimeter for {spec['desc']}.",
                })

    return issues, passes


def audit_circulation_and_ux(layout: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Audit Pillar 4: Spatial UX, Corridor Clearances, Acoustics, Sightlines, and Transit."""
    issues = []
    passes = []
    rooms = {r["id"]: r for r in layout.get("rooms", [])}
    connections = layout.get("connections", [])
    shared_walls = layout.get("shared_walls", [])

    for conn in connections:
        c_from = rooms.get(conn["from"], {"name": conn["from"]})["name"]
        c_to = rooms.get(conn["to"], {"name": conn["to"]})["name"]
        c_type = conn.get("type", "doorway")
        width = conn.get("width_in", 36)
        traffic = conn.get("traffic", "medium")

        if traffic == "high" or c_type == "arterial_corridor":
            if width < 42:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Spatial UX",
                    "category": "Circulation Bottleneck",
                    "message": f"Arterial path between '{c_from}' and '{c_to}' is {width}\" wide (minimum 42\", recommended 48\").",
                })
            elif width < 48:
                issues.append({
                    "level": "WARN",
                    "pillar": "Spatial UX",
                    "category": "Circulation Bottleneck",
                    "message": f"High-traffic path between '{c_from}' and '{c_to}' is {width}\" wide (48\" recommended for simultaneous passing).",
                })
            else:
                passes.append({
                    "pillar": "Spatial UX",
                    "category": "Clearance",
                    "message": f"Arterial spine between '{c_from}' and '{c_to}' meets 48\" clear passage standard ({width}\").",
                })
        elif traffic == "medium" or c_type == "secondary_hall":
            if width < 36:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Spatial UX",
                    "category": "Corridor Clearance",
                    "message": f"Secondary hall/connection between '{c_from}' and '{c_to}' is {width}\" wide (minimum 36\" required).",
                })
            else:
                passes.append({
                    "pillar": "Spatial UX",
                    "category": "Clearance",
                    "message": f"Secondary connection between '{c_from}' and '{c_to}' complies with 36\" clearance ({width}\").",
                })

        if c_type in ["doorway", "fire_door"] and not conn.get("swing_into_room", True):
            issues.append({
                "level": "WARN",
                "pillar": "Spatial UX",
                "category": "Door Swing Hazard",
                "message": f"Door between '{c_from}' and '{c_to}' swings outward into traffic corridor instead of into room.",
            })

        if c_type in ["exterior_slider", "exterior_door"]:
            step = conn.get("step_down_in", 0)
            if step < 1.5:
                issues.append({
                    "level": "WARN",
                    "pillar": "Spatial UX",
                    "category": "Weather Infiltration Risk",
                    "message": f"Exterior transition from '{c_from}' to '{c_to}' has {step}\" step-down (minimum 1.5\"–2.0\" required to prevent wind-driven rain penetration).",
                })
            else:
                passes.append({
                    "pillar": "Spatial UX",
                    "category": "Weather Defense",
                    "message": f"Exterior threshold between '{c_from}' and '{c_to}' has protective {step}\" step-down.",
                })

    for conn in connections:
        if conn.get("direct_sightline", False):
            r_from = rooms.get(conn["from"], {})
            r_to = rooms.get(conn["to"], {})
            if r_to.get("id") in ["powder", "bath"] or r_to.get("zone") == "private":
                issues.append({
                    "level": "WARN",
                    "pillar": "Spatial UX",
                    "category": "Visual Privacy Breach",
                    "message": f"Direct sightline exists from '{r_from.get('name')}' into private '{r_to.get('name')}'. Introduce an offset baffle or privacy vestibule.",
                })

    for wall in shared_walls:
        ra = rooms.get(wall["room_a"], {})
        rb = rooms.get(wall["room_b"], {})
        za = ra.get("zone", "")
        zb = rb.get("zone", "")
        decoupled = wall.get("acoustic_decoupled", False)

        is_conflict = (za == "private" and zb in ["service", "public"]) or (zb == "private" and za in ["service", "public"])
        if is_conflict:
            if not decoupled:
                issues.append({
                    "level": "FAIL",
                    "pillar": "Spatial UX",
                    "category": "Acoustic Conflict",
                    "message": f"Sleeping zone '{ra.get('name')}' shares un-decoupled partition with noisy zone '{rb.get('name')}'. Introduce an acoustic chase, closet buffer, or decoupled assembly.",
                })
            else:
                passes.append({
                    "pillar": "Spatial UX",
                    "category": "Acoustic Decoupling",
                    "message": f"Acoustic separation maintained between '{ra.get('name')}' and '{rb.get('name')}' via {wall.get('wall_type', 'insulated wall')}.",
                })

    graph: Dict[str, List[str]] = {r_id: [] for r_id in rooms}
    for c in connections:
        graph.setdefault(c["from"], []).append(c["to"])
        graph.setdefault(c["to"], []).append(c["from"])

    def bfs_shortest_path(start: str, goal: str) -> Optional[List[str]]:
        if start not in graph or goal not in graph:
            return None
        visited: Set[str] = {start}
        queue: List[Tuple[str, List[str]]] = [(start, [start])]
        while queue:
            curr, path = queue.pop(0)
            if curr == goal:
                return path
            for neighbor in graph.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    grocery_path = bfs_shortest_path("entry", "kitchen")
    if grocery_path:
        hops = len(grocery_path) - 1
        path_names = " -> ".join([rooms.get(nid, {}).get("name", nid) for nid in grocery_path])
        if hops <= 2:
            passes.append({
                "pillar": "Spatial UX",
                "category": "Transit Ergonomics",
                "message": f"Grocery supply transit is efficient ({hops} hops: {path_names}).",
            })
        else:
            issues.append({
                "level": "WARN",
                "pillar": "Spatial UX",
                "category": "Transit Inefficiency",
                "message": f"Grocery supply transit is extended ({hops} hops: {path_names}). Consider direct pantry service entrance.",
            })

    wet_path = bfs_shortest_path("terrace", "laundry")
    if wet_path:
        path_names = " -> ".join([rooms.get(nid, {}).get("name", nid) for nid in wet_path])
        if "living" in wet_path and len(wet_path) > 2:
            issues.append({
                "level": "WARN",
                "pillar": "Spatial UX",
                "category": "Wet-to-Dry Circulation Trap",
                "message": f"Wet beach/pool traffic traverses main living area ({path_names}). Add direct exterior wash entrance.",
            })
        else:
            passes.append({
                "pillar": "Spatial UX",
                "category": "Wet-to-Dry Circulation",
                "message": f"Wet traffic route isolates living spaces from moisture/sand ({path_names}).",
            })

    return issues, passes


def generate_mermaid_circulation(layout: Dict[str, Any]) -> str:
    lines = [
        "graph TD",
        "    classDef public fill:#e1f5fe,stroke:#0288d1,stroke-width:2px",
        "    classDef private fill:#ede7f6,stroke:#7e57c2,stroke-width:2px",
        "    classDef service fill:#fff3e0,stroke:#f57c00,stroke-width:2px",
        "    classDef circulation fill:#f1f5f9,stroke:#64748b,stroke-width:2px",
        "    classDef exterior fill:#e8f5e9,stroke:#388e3c,stroke-width:2px",
        "",
    ]

    rooms = {r["id"]: r for r in layout.get("rooms", [])}
    for r in layout.get("rooms", []):
        r_id = r["id"]
        name = r.get("name", r_id)
        zone = r.get("zone", "public")
        area = f" ({r['area_sqft']} sq ft)" if "area_sqft" in r else ""
        lines.append(f'    {r_id}["{name}{area}"]:::{zone}')

    lines.append("")
    for c in layout.get("connections", []):
        f_id = c["from"]
        t_id = c["to"]
        width = f"{c.get('width_in', 36)} in"
        traffic = c.get("traffic", "medium")

        edge_label = f"{traffic.capitalize()} ({width})"
        if traffic == "high":
            lines.append(f"    {f_id} ==>|{edge_label}| {t_id}")
        elif traffic == "low":
            lines.append(f"    {f_id} -.->|{edge_label}| {t_id}")
        else:
            lines.append(f"    {f_id} -->|{edge_label}| {t_id}")

    return "\n".join(lines)


def run_full_validation_suite(layout: Dict[str, Any]) -> Dict[str, Any]:
    all_issues = []
    all_passes = []

    # Pillar 1: Geometry
    i1, p1 = audit_geometry(layout)
    all_issues.extend(i1)
    all_passes.extend(p1)

    # Pillar 2: Building Codes
    i2, p2 = audit_building_codes(layout)
    all_issues.extend(i2)
    all_passes.extend(p2)

    # Pillar 3: Furniture & Ergonomics
    i3, p3 = audit_furniture_clearances(layout)
    all_issues.extend(i3)
    all_passes.extend(p3)

    # Pillar 4: Spatial UX & Circulation
    i4, p4 = audit_circulation_and_ux(layout)
    all_issues.extend(i4)
    all_passes.extend(p4)

    fails = [i for i in all_issues if i["level"] == "FAIL"]
    warns = [i for i in all_issues if i["level"] == "WARN"]

    return {
        "project": layout.get("project", "Floorplan Program"),
        "total_rooms": len(layout.get("rooms", [])),
        "total_connections": len(layout.get("connections", [])),
        "is_valid": len(fails) == 0,
        "fails_count": len(fails),
        "warns_count": len(warns),
        "passes_count": len(all_passes),
        "issues": all_issues,
        "passes": all_passes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive floor plan validation: Geometry, Building Codes (IRC/IBC), Furniture Envelopes & Spatial UX."
    )
    parser.add_argument("--spec", help="Path to floor plan specification JSON file")
    parser.add_argument("--demo", action="store_true", help="Run audit on built-in resilient villa reference specification")
    parser.add_argument("--mermaid", action="store_true", help="Output circulation network as Mermaid diagram")
    parser.add_argument("--json", action="store_true", help="Output audit results in JSON format")

    args = parser.parse_args()

    if args.demo:
        spec = DEMO_LAYOUT
    elif args.spec:
        try:
            with open(args.spec, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Error reading spec file '{args.spec}': {e}\n")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    if args.mermaid:
        print(generate_mermaid_circulation(spec))
        print()
        if not args.json:
            return

    res = run_full_validation_suite(spec)

    if args.json:
        json.dump(res, sys.stdout, indent=2)
        print()
        sys.exit(0 if res["is_valid"] else 1)

    # Formatted Multi-Pillar Scorecard
    status = "PASSED" if res["is_valid"] else "FAILED"
    print(f"=== Architectural Floor Plan Validation Scorecard: {res['project']} ===")
    print(f"Status:            {status}")
    print(f"Rooms Monitored:   {res['total_rooms']}")
    print(f"Circulation Edges: {res['total_connections']}")
    print(f"Score Summary:     {res['passes_count']} Passed | {res['warns_count']} Warnings | {res['fails_count']} Failures\n")

    fails = [i for i in res["issues"] if i["level"] == "FAIL"]
    warns = [i for i in res["issues"] if i["level"] == "WARN"]

    if fails:
        print("❌ Critical Architectural & Code Failures:")
        for f in fails:
            print(f"  • [{f['pillar']} - {f['category']}] {f['message']}")
        print()

    if warns:
        print("⚠️  Ergonomics, Glazing & Layout Warnings:")
        for w in warns:
            print(f"  • [{w['pillar']} - {w['category']}] {w['message']}")
        print()

    if res["passes"]:
        print("✅ Verified Standards:")
        by_pillar = {}
        for p in res["passes"]:
            by_pillar.setdefault(p["pillar"], []).append(p)
        for pillar, items in by_pillar.items():
            print(f"  [{pillar}] ({len(items)} checks passed)")
            for item in items[:4]:
                print(f"    ✓ {item['category']}: {item['message']}")
            if len(items) > 4:
                print(f"    ... and {len(items) - 4} more {pillar} checks passed.")
        print()

    sys.exit(0 if res["is_valid"] else 1)


if __name__ == "__main__":
    main()
