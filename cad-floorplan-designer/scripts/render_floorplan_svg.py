#!/usr/bin/env python3
"""
render_floorplan_svg.py

Renders clean, structurally sound 2D architectural CAD floor plans and
spatial circulation overlays as standalone SVG markup.

Features:
- Alphanumeric structural grid lines and bubbles (A, B, C... / 1, 2, 3...).
- Heavy structural walls (8" CMU) and medium partition walls.
- Architectural door swing arcs (90-degree SVG circular arcs) and double-line window tracks.
- Spatial UX circulation path overlay (arterial spines & secondary routes).
- Title block with project metadata, scale, and north arrow indicator.
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional


def render_svg(layout: Dict[str, Any], show_circulation: bool = True) -> str:
    vb_w = layout.get("viewbox_width", 1400)
    vb_h = layout.get("viewbox_height", 950)
    scale = layout.get("scale_px_per_foot", 14.0)
    origin_x = layout.get("origin_x", 180)
    origin_y = layout.get("origin_y", 160)

    project_name = layout.get("project_name", "Resilient Architectural Layout")
    level_name = layout.get("level_name", "Level 1 - Main Floor Plan")

    grid_x = layout.get("grid_x", [0, 16, 32, 48])  # in feet from origin
    grid_y = layout.get("grid_y", [0, 16, 32, 44])

    rooms = layout.get("rooms", [])
    doors = layout.get("doors", [])
    windows = layout.get("windows", [])
    circulation_paths = layout.get("circulation_paths", [])

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" width="100%" height="100%">')
    
    # Styles & Defs
    svg_parts.append("""  <defs>
    <style>
      .cad-bg { fill: #0b1120; }
      .grid-line { stroke: #334155; stroke-dasharray: 4,4; stroke-width: 1; }
      .grid-bubble { fill: #1e293b; stroke: #64748b; stroke-width: 1.5; }
      .grid-text { font-family: 'Courier New', monospace; font-size: 13px; font-weight: bold; fill: #94a3b8; text-anchor: middle; dominant-baseline: central; }
      .ext-wall { fill: #1e293b; stroke: #38bdf8; stroke-width: 3.5; stroke-linejoin: miter; }
      .int-wall { fill: none; stroke: #94a3b8; stroke-width: 2.0; stroke-linejoin: round; }
      .window-line { stroke: #38bdf8; stroke-width: 1.5; }
      .door-frame { stroke: #e2e8f0; stroke-width: 2.0; }
      .door-arc { fill: none; stroke: #fbbf24; stroke-dasharray: 3,3; stroke-width: 1.5; }
      .circ-arterial { fill: none; stroke: #f59e0b; stroke-width: 3.0; stroke-dasharray: 8,5; stroke-linecap: round; }
      .circ-secondary { fill: none; stroke: #06b6d4; stroke-width: 2.0; stroke-dasharray: 6,4; stroke-linecap: round; }
      .room-title { font-family: system-ui, -apple-system, sans-serif; font-size: 15px; font-weight: 700; fill: #f8fafc; text-anchor: middle; }
      .room-dim { font-family: 'Courier New', monospace; font-size: 12px; fill: #94a3b8; text-anchor: middle; }
      .room-ffl { font-family: 'Courier New', monospace; font-size: 11px; fill: #38bdf8; text-anchor: middle; }
      .title-head { font-family: system-ui, -apple-system, sans-serif; font-size: 18px; font-weight: bold; fill: #f1f5f9; }
      .title-sub { font-family: system-ui, -apple-system, sans-serif; font-size: 13px; fill: #94a3b8; }
      .north-sym { stroke: #f8fafc; stroke-width: 2; fill: #f8fafc; }
    </style>
  </defs>""")

    # Background
    svg_parts.append(f'  <rect width="{vb_w}" height="{vb_h}" class="cad-bg" />')

    # 1. Structural Grid Lines & Bubbles
    svg_parts.append('  <!-- Structural Grid -->')
    svg_parts.append('  <g id="structural-grid">')
    
    # Vertical grid lines (1, 2, 3...)
    y_top = origin_y - 45
    y_bottom = origin_y + (max(grid_y) * scale) + 45
    for idx, gx_ft in enumerate(grid_x):
        px = origin_x + (gx_ft * scale)
        label = str(idx + 1)
        svg_parts.append(f'    <line x1="{px}" y1="{y_top}" x2="{px}" y2="{y_bottom}" class="grid-line" />')
        # Top bubble
        svg_parts.append(f'    <circle cx="{px}" cy="{y_top}" r="15" class="grid-bubble" />')
        svg_parts.append(f'    <text x="{px}" y="{y_top}" class="grid-text">{label}</text>')
        # Bottom bubble
        svg_parts.append(f'    <circle cx="{px}" cy="{y_bottom}" r="15" class="grid-bubble" />')
        svg_parts.append(f'    <text x="{px}" y="{y_bottom}" class="grid-text">{label}</text>')

    # Horizontal grid lines (A, B, C...)
    x_left = origin_x - 45
    x_right = origin_x + (max(grid_x) * scale) + 45
    for idx, gy_ft in enumerate(grid_y):
        py = origin_y + (gy_ft * scale)
        label = chr(65 + idx)
        svg_parts.append(f'    <line x1="{x_left}" y1="{py}" x2="{x_right}" y2="{py}" class="grid-line" />')
        # Left bubble
        svg_parts.append(f'    <circle cx="{x_left}" cy="{py}" r="15" class="grid-bubble" />')
        svg_parts.append(f'    <text x="{x_left}" y="{py}" class="grid-text">{label}</text>')
        # Right bubble
        svg_parts.append(f'    <circle cx="{x_right}" cy="{py}" r="15" class="grid-bubble" />')
        svg_parts.append(f'    <text x="{x_right}" y="{py}" class="grid-text">{label}</text>')
    svg_parts.append('  </g>')

    # 2. Rooms & Partitions
    svg_parts.append('  <!-- Rooms & Footprints -->')
    svg_parts.append('  <g id="rooms">')
    for r in rooms:
        rx = origin_x + (r["x"] * scale)
        ry = origin_y + (r["y"] * scale)
        rw = r["w"] * scale
        rh = r["h"] * scale
        is_ext = r.get("is_exterior_wall", True)
        wall_class = "ext-wall" if is_ext else "int-wall"

        # Room rectangle
        svg_parts.append(f'    <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" class="{wall_class}" />')

        # Labels
        cx = rx + (rw / 2.0)
        cy = ry + (rh / 2.0)
        dim_str = f"{r['w']}'-0\" x {r['h']}'-0\""
        ffl = r.get("ffl", "+0.00' FFL")

        svg_parts.append(f'    <text x="{cx}" y="{cy - 12}" class="room-title">{r["name"]}</text>')
        svg_parts.append(f'    <text x="{cx}" y="{cy + 8}" class="room-dim">{dim_str}</text>')
        svg_parts.append(f'    <text x="{cx}" y="{cy + 25}" class="room-ffl">{ffl}</text>')
    svg_parts.append('  </g>')

    # 3. Doors & Swings
    svg_parts.append('  <!-- Doors & Architectural Swings -->')
    svg_parts.append('  <g id="doors">')
    for d in doors:
        dx = origin_x + (d["x"] * scale)
        dy = origin_y + (d["y"] * scale)
        dw = d.get("width_ft", 3.0) * scale
        orient = d.get("orientation", "horizontal")
        # Draw 90-degree door swing arc
        if orient == "horizontal":
            # Hinge at dx, dy; leaf extends along X, swings along Y
            svg_parts.append(f'    <line x1="{dx}" y1="{dy}" x2="{dx + dw}" y2="{dy}" class="door-frame" />')
            svg_parts.append(f'    <path d="M {dx + dw} {dy} A {dw} {dw} 0 0 1 {dx} {dy + dw}" class="door-arc" />')
        else:
            svg_parts.append(f'    <line x1="{dx}" y1="{dy}" x2="{dx}" y2="{dy + dw}" class="door-frame" />')
            svg_parts.append(f'    <path d="M {dx} {dy + dw} A {dw} {dw} 0 0 1 {dx + dw} {dy}" class="door-arc" />')
    svg_parts.append('  </g>')

    # 4. Windows
    svg_parts.append('  <!-- Window Openings -->')
    svg_parts.append('  <g id="windows">')
    for w in windows:
        wx = origin_x + (w["x"] * scale)
        wy = origin_y + (w["y"] * scale)
        ww = w.get("width_ft", 4.0) * scale
        orient = w.get("orientation", "horizontal")
        if orient == "horizontal":
            svg_parts.append(f'    <line x1="{wx}" y1="{wy - 2}" x2="{wx + ww}" y2="{wy - 2}" class="window-line" />')
            svg_parts.append(f'    <line x1="{wx}" y1="{wy + 2}" x2="{wx + ww}" y2="{wy + 2}" class="window-line" />')
        else:
            svg_parts.append(f'    <line x1="{wx - 2}" y1="{wy}" x2="{wx - 2}" y2="{wy + ww}" class="window-line" />')
            svg_parts.append(f'    <line x1="{wx + 2}" y1="{wy}" x2="{wx + 2}" y2="{wy + ww}" class="window-line" />')
    svg_parts.append('  </g>')

    # 5. Spatial UX & Circulation Paths Overlay
    if show_circulation and circulation_paths:
        svg_parts.append('  <!-- Spatial UX & Circulation Flows -->')
        svg_parts.append('  <g id="circulation-paths">')
        for cp in circulation_paths:
            cls = "circ-arterial" if cp.get("tier") == "arterial" else "circ-secondary"
            pts = cp.get("points_ft", [])
            if len(pts) >= 2:
                d_str = " ".join([
                    f"{'M' if i == 0 else 'L'} {origin_x + (pt[0] * scale)} {origin_y + (pt[1] * scale)}"
                    for i, pt in enumerate(pts)
                ])
                svg_parts.append(f'    <path d="{d_str}" class="{cls}" />')
        svg_parts.append('  </g>')

    # 6. Title Block & North Indicator
    svg_parts.append('  <!-- Title Block & North Arrow -->')
    svg_parts.append('  <g id="title-block">')
    tb_x = origin_x
    tb_y = vb_h - 75
    svg_parts.append(f'    <text x="{tb_x}" y="{tb_y}" class="title-head">{project_name}</text>')
    svg_parts.append(f'    <text x="{tb_x}" y="{tb_y + 22}" class="title-sub">{level_name} | Modular CMU 8"/16" Alignment | Resilience Core</text>')
    
    # Legend
    leg_x = vb_w - 420
    leg_y = tb_y - 10
    svg_parts.append(f'    <rect x="{leg_x - 15}" y="{leg_y - 20}" width="380" height="75" fill="#1e293b" stroke="#475569" rx="6" />')
    svg_parts.append(f'    <line x1="{leg_x}" y1="{leg_y}" x2="{leg_x + 35}" y2="{leg_y}" class="circ-arterial" />')
    svg_parts.append(f'    <text x="{leg_x + 45}" y="{leg_y + 4}" class="title-sub" fill="#e2e8f0">Arterial Spine (48" Clear)</text>')
    svg_parts.append(f'    <line x1="{leg_x}" y1="{leg_y + 25}" x2="{leg_x + 35}" y2="{leg_y + 25}" class="circ-secondary" />')
    svg_parts.append(f'    <text x="{leg_x + 45}" y="{leg_y + 29}" class="title-sub" fill="#e2e8f0">Secondary Corridor (36" Clear)</text>')

    # North Arrow
    na_x = vb_w - 90
    na_y = 75
    svg_parts.append(f'    <polygon points="{na_x},{na_y - 30} {na_x - 12},{na_y + 10} {na_x},{na_y} {na_x + 12},{na_y + 10}" class="north-sym" />')
    svg_parts.append(f'    <text x="{na_x}" y="{na_y + 28}" class="title-head" text-anchor="middle">N</text>')
    svg_parts.append('  </g>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


DEFAULT_LAYOUT_SPEC = {
    "project_name": "Resilient Coastal Hillside Villa",
    "level_name": "Level 1 - Main Floor Plan",
    "scale_px_per_foot": 15.0,
    "origin_x": 160,
    "origin_y": 140,
    "grid_x": [0, 16, 32, 48, 64],
    "grid_y": [0, 16, 32, 44],
    "rooms": [
        {"name": "Main Foyer", "x": 0, "y": 16, "w": 16, "h": 16, "is_exterior_wall": True, "ffl": "+0.00' FFL"},
        {"name": "Great Room & Dining", "x": 16, "y": 0, "w": 32, "h": 32, "is_exterior_wall": True, "ffl": "+0.00' FFL"},
        {"name": "Kitchen & Pantry", "x": 48, "y": 0, "w": 16, "h": 16, "is_exterior_wall": True, "ffl": "+0.00' FFL"},
        {"name": "Primary Suite", "x": 0, "y": 0, "w": 16, "h": 16, "is_exterior_wall": True, "ffl": "+0.00' FFL"},
        {"name": "Covered Lanai / Terrace", "x": 16, "y": 32, "w": 32, "h": 12, "is_exterior_wall": True, "ffl": "-0.15' FFL (-2\" step)"},
        {"name": "Resilience Core (Power/Cistern)", "x": 48, "y": 16, "w": 16, "h": 16, "is_exterior_wall": True, "ffl": "+0.00' FFL"},
    ],
    "doors": [
        {"x": 8, "y": 16, "width_ft": 3.0, "orientation": "horizontal"},
        {"x": 16, "y": 20, "width_ft": 3.5, "orientation": "vertical"},
        {"x": 48, "y": 8, "width_ft": 3.0, "orientation": "vertical"},
        {"x": 30, "y": 32, "width_ft": 6.0, "orientation": "horizontal"},
    ],
    "windows": [
        {"x": 20, "y": 0, "width_ft": 6.0, "orientation": "horizontal"},
        {"x": 36, "y": 0, "width_ft": 6.0, "orientation": "horizontal"},
        {"x": 64, "y": 6, "width_ft": 4.0, "orientation": "vertical"},
    ],
    "circulation_paths": [
        {"tier": "arterial", "points_ft": [[8, 24], [16, 20], [32, 16], [48, 8]]},
        {"tier": "arterial", "points_ft": [[32, 16], [32, 32], [32, 38]]},
        {"tier": "secondary", "points_ft": [[8, 20], [8, 8]]},
        {"tier": "secondary", "points_ft": [[48, 12], [54, 20]]},
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Render clean 2D CAD architectural SVG floor plans with circulation overlays.")
    parser.add_argument("--spec", help="Path to layout spec JSON file")
    parser.add_argument("--demo", action="store_true", help="Generate SVG using default resilient villa template")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("--no-circulation", action="store_true", help="Omit circulation flow paths overlay")

    args = parser.parse_args()

    if args.demo:
        spec = DEFAULT_LAYOUT_SPEC
    elif args.spec:
        try:
            with open(args.spec, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Error loading spec '{args.spec}': {e}\n")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    svg_content = render_svg(spec, show_circulation=not args.no_circulation)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(svg_content)
            sys.stderr.write(f"Rendered floorplan SVG to '{args.output}'.\n")
        except Exception as e:
            sys.stderr.write(f"Error writing to '{args.output}': {e}\n")
            sys.exit(1)
    else:
        print(svg_content)


if __name__ == "__main__":
    main()
