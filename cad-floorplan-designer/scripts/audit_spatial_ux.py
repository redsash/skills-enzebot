#!/usr/bin/env python3
"""
audit_spatial_ux.py

Audits architectural floor plan spatial programs and circulation networks for:
- Corridor & doorway clear widths (Arterial vs. Secondary vs. Service).
- Acoustic zoning and privacy buffers (sleeping vs. entertaining vs. mechanical).
- Sightline privacy (visual baffles to bathrooms and private suites).
- Transit ergonomics (groceries transit from entry to pantry; wet-to-dry beach transit).
- Exports Mermaid circulation graphs for interactive visualization.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Set, Tuple


DEMO_LAYOUT = {
    "project": "Villa Resiliente",
    "rooms": [
        {"id": "entry", "name": "Main Foyer", "zone": "public", "area_sqft": 80},
        {"id": "living", "name": "Great Room & Dining", "zone": "public", "area_sqft": 420},
        {"id": "kitchen", "name": "Kitchen & Pantry", "zone": "public", "area_sqft": 180},
        {"id": "terrace", "name": "Covered Lanai / Pool", "zone": "exterior", "area_sqft": 320},
        {"id": "hall_bed", "name": "Bedroom Hall Baffle", "zone": "circulation", "area_sqft": 60},
        {"id": "bed_master", "name": "Primary Suite", "zone": "private", "area_sqft": 240},
        {"id": "bed_guest", "name": "Guest Bedroom", "zone": "private", "area_sqft": 160},
        {"id": "powder", "name": "Guest Powder Room", "zone": "public", "area_sqft": 35},
        {"id": "laundry", "name": "Laundry & Beach Wash", "zone": "service", "area_sqft": 75},
        {"id": "mech", "name": "Inverter, Battery & ATS Room", "zone": "service", "area_sqft": 65},
        {"id": "cistern", "name": "Cistern & Booster Pump", "zone": "service", "area_sqft": 80},
    ],
    "connections": [
        {"from": "entry", "to": "living", "type": "arterial_corridor", "width_in": 48, "traffic": "high"},
        {"from": "living", "to": "kitchen", "type": "open_threshold", "width_in": 72, "traffic": "high"},
        {"from": "living", "to": "terrace", "type": "exterior_slider", "width_in": 96, "traffic": "high", "step_down_in": 2.0},
        {"from": "entry", "to": "powder", "type": "doorway", "width_in": 32, "traffic": "medium", "direct_sightline": False},
        {"from": "entry", "to": "hall_bed", "type": "secondary_hall", "width_in": 42, "traffic": "medium"},
        {"from": "hall_bed", "to": "bed_master", "type": "doorway", "width_in": 36, "traffic": "medium", "swing_into_room": True},
        {"from": "hall_bed", "to": "bed_guest", "type": "doorway", "width_in": 32, "traffic": "low", "swing_into_room": True},
        {"from": "kitchen", "to": "laundry", "type": "doorway", "width_in": 36, "traffic": "medium", "swing_into_room": True},
        {"from": "terrace", "to": "laundry", "type": "exterior_door", "width_in": 36, "traffic": "medium", "wet_route": True},
        {"from": "laundry", "to": "mech", "type": "fire_door", "width_in": 36, "traffic": "low", "fire_rated_min": 60},
        {"from": "mech", "to": "cistern", "type": "access_door", "width_in": 36, "traffic": "low"},
    ],
    "shared_walls": [
        {"room_a": "mech", "room_b": "bed_guest", "acoustic_decoupled": True, "wall_type": "8in CMU with resilient channel"},
        {"room_a": "powder", "room_b": "living", "acoustic_decoupled": True, "wall_type": "Insulated drywall"},
    ],
}


def audit_spatial_program(layout: Dict[str, Any]) -> Dict[str, Any]:
    rooms = {r["id"]: r for r in layout.get("rooms", [])}
    connections = layout.get("connections", [])
    shared_walls = layout.get("shared_walls", [])

    issues: List[Dict[str, str]] = []
    passes: List[Dict[str, str]] = []

    # 1. Clear Width & Clearance Audit
    for conn in connections:
        c_from = rooms.get(conn["from"], {"name": conn["from"]})["name"]
        c_to = rooms.get(conn["to"], {"name": conn["to"]})["name"]
        c_type = conn.get("type", "doorway")
        width = conn.get("width_in", 32)
        traffic = conn.get("traffic", "medium")

        if traffic == "high" or c_type == "arterial_corridor":
            if width < 42:
                issues.append({
                    "level": "FAIL",
                    "category": "Circulation Bottleneck",
                    "message": f"Arterial path between '{c_from}' and '{c_to}' is {width}\" wide (minimum 42\", recommended 48\").",
                })
            elif width < 48:
                issues.append({
                    "level": "WARN",
                    "category": "Circulation Bottleneck",
                    "message": f"High-traffic path between '{c_from}' and '{c_to}' is {width}\" wide (48\" recommended for simultaneous passing).",
                })
            else:
                passes.append({
                    "category": "Clearance",
                    "message": f"Arterial spine between '{c_from}' and '{c_to}' meets 48\" clear passage standard ({width}\").",
                })
        elif traffic == "medium" or c_type == "secondary_hall":
            if width < 36:
                issues.append({
                    "level": "FAIL",
                    "category": "Corridor Clearance",
                    "message": f"Secondary hall/connection between '{c_from}' and '{c_to}' is {width}\" wide (minimum 36\" required).",
                })
            else:
                passes.append({
                    "category": "Clearance",
                    "message": f"Secondary connection between '{c_from}' and '{c_to}' complies with 36\" clearance ({width}\").",
                })

        # Door swing direction check
        if c_type in ["doorway", "fire_door"] and not conn.get("swing_into_room", True):
            issues.append({
                "level": "WARN",
                "category": "Door Swing Hazard",
                "message": f"Door between '{c_from}' and '{c_to}' swings outward into traffic corridor instead of into room.",
            })

        # Weather step-down check
        if c_type in ["exterior_slider", "exterior_door"]:
            step = conn.get("step_down_in", 0)
            if step < 1.5:
                issues.append({
                    "level": "WARN",
                    "category": "Weather Infiltration Risk",
                    "message": f"Exterior transition from '{c_from}' to '{c_to}' has {step}\" step-down (minimum 1.5\"–2.0\" required to prevent wind-driven rain penetration).",
                })
            else:
                passes.append({
                    "category": "Weather Defense",
                    "message": f"Exterior threshold between '{c_from}' and '{c_to}' has protective {step}\" step-down.",
                })

    # 2. Sightline Privacy Audit
    for conn in connections:
        if conn.get("direct_sightline", False):
            r_from = rooms.get(conn["from"], {})
            r_to = rooms.get(conn["to"], {})
            if r_to.get("id") in ["powder", "bath"] or r_to.get("zone") == "private":
                issues.append({
                    "level": "WARN",
                    "category": "Visual Privacy Breach",
                    "message": f"Direct sightline exists from '{r_from.get('name')}' into private '{r_to.get('name')}'. Introduce an offset baffle or privacy vestibule.",
                })

    # 3. Acoustic Buffering Audit
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
                    "category": "Acoustic Conflict",
                    "message": f"Sleeping zone '{ra.get('name')}' shares un-decoupled partition with noisy zone '{rb.get('name')}'. Introduce an acoustic chase, closet buffer, or decoupled double-stud assembly.",
                })
            else:
                passes.append({
                    "category": "Acoustic Decoupling",
                    "message": f"Acoustic separation maintained between '{ra.get('name')}' and '{rb.get('name')}' via {wall.get('wall_type', 'insulated wall')}.",
                })

    # 4. Grocery & Beach Transit Flow Audit
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

    # Check Grocery Route: Entry -> Kitchen
    grocery_path = bfs_shortest_path("entry", "kitchen")
    if grocery_path:
        hops = len(grocery_path) - 1
        path_names = " -> ".join([rooms.get(nid, {}).get("name", nid) for nid in grocery_path])
        if hops <= 2:
            passes.append({
                "category": "Transit Ergonomics",
                "message": f"Grocery supply transit is efficient ({hops} hops: {path_names}).",
            })
        else:
            issues.append({
                "level": "WARN",
                "category": "Transit Inefficiency",
                "message": f"Grocery supply transit is extended ({hops} hops: {path_names}). Consider a direct pantry service entrance.",
            })

    # Check Wet Route: Terrace/Exterior -> Laundry
    wet_path = bfs_shortest_path("terrace", "laundry")
    if wet_path:
        path_names = " -> ".join([rooms.get(nid, {}).get("name", nid) for nid in wet_path])
        if "living" in wet_path and len(wet_path) > 2:
            issues.append({
                "level": "WARN",
                "category": "Wet-to-Dry Circulation Trap",
                "message": f"Wet beach/pool traffic traverses main living area ({path_names}). Add direct exterior wash entrance.",
            })
        else:
            passes.append({
                "category": "Wet-to-Dry Circulation",
                "message": f"Wet traffic route isolates living spaces from moisture/sand ({path_names}).",
            })

    return {
        "project": layout.get("project", "Floorplan Program"),
        "total_rooms": len(rooms),
        "total_connections": len(connections),
        "issues": issues,
        "passes": passes,
    }


def generate_mermaid_circulation(layout: Dict[str, Any]) -> str:
    lines = [
        "graph TD",
        "    classDef public fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;",
        "    classDef private fill:#ede7f6,stroke:#7e57c2,stroke-width:2px;",
        "    classDef service fill:#fff3e0,stroke:#f57c00,stroke-width:2px;",
        "    classDef circulation fill:#f1f5f9,stroke:#64748b,stroke-width:2px;",
        "    classDef exterior fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;",
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
        c_type = c.get("type", "door")

        edge_label = f"{traffic.capitalize()} ({width})"
        if traffic == "high":
            lines.append(f"    {f_id} ==>|{edge_label}| {t_id}")
        elif traffic == "low":
            lines.append(f"    {f_id} -.->|{edge_label}| {t_id}")
        else:
            lines.append(f"    {f_id} -->|{edge_label}| {t_id}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Audit floor plan spatial UX, corridor clearances, acoustic buffers, and circulation hierarchy."
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

    results = audit_spatial_program(spec)

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
        return

    # Formatted Markdown Output
    print(f"### Spatial UX & Circulation Audit: {results['project']}")
    print(f"- **Rooms Monitored:** {results['total_rooms']}")
    print(f"- **Circulation Edges:** {results['total_connections']}")
    print()

    fails = [i for i in results["issues"] if i["level"] == "FAIL"]
    warns = [i for i in results["issues"] if i["level"] == "WARN"]

    if fails:
        print("#### ❌ Critical Spatial & Clearance Failures")
        for f in fails:
            print(f"- **[{f['category']}]** {f['message']}")
        print()

    if warns:
        print("#### ⚠️ Ergonomics & Privacy Warnings")
        for w in warns:
            print(f"- **[{w['category']}]** {w['message']}")
        print()

    if results["passes"]:
        print("#### ✅ Verified Clearances & Spatial Standards")
        for p in results["passes"]:
            print(f"- **[{p['category']}]** {p['message']}")
        print()


if __name__ == "__main__":
    main()
