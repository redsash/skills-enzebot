# Canonical Floorplan Spec Schema (`schema_version: 1`)

Single unified JSON specification consumed by `scripts/audit_spatial_ux.py`, `scripts/estimate_construction_cost.py`, and `scripts/render_floorplan_svg.py`.

---

## Minimal Unified Skeleton

```json
{
  "schema_version": 1,
  "project": "Resilient Coastal Hillside Villa",
  "level_name": "Level 1 - Main Floor Plan",
  "gross_footprint_sqft": 1800,
  "story_height_ft": 10.0,
  "cistern_gallons": 1000,
  "solar_kw": 8.0,
  "battery_kwh": 20.0,
  "grid_x": [0, 16, 32, 48],
  "grid_y": [0, 16, 32, 44],
  "rooms": [
    {
      "id": "bed_master",
      "name": "Primary Suite",
      "zone": "private",
      "x": 0,
      "y": 0,
      "w": 16,
      "h": 16,
      "area_sqft": 256,
      "ffl": "+0.00' FFL",
      "is_exterior_wall": true,
      "is_sleeping_room": true,
      "furniture": ["king_bed"],
      "windows": [
        {
          "width_ft": 6.0,
          "height_ft": 4.0,
          "clear_width_in": 28,
          "clear_height_in": 40,
          "sill_height_in": 36,
          "operable_pct": 50
        }
      ]
    }
  ],
  "connections": [
    {
      "from": "entry",
      "to": "living",
      "type": "arterial_corridor",
      "width_in": 48,
      "traffic": "high",
      "swing_into_room": true
    }
  ],
  "doors": [
    {"x": 8, "y": 16, "width_ft": 3.0, "orientation": "horizontal"}
  ],
  "shared_walls": [
    {"room_a": "mech", "room_b": "bed_master", "acoustic_decoupled": true, "wall_type": "8in CMU"}
  ]
}
```

---

## Field Semantics & Backward-Compatible Fallbacks

| Field | Required | Consumer Scripts | Fallback / Normalization |
| :--- | :--- | :--- | :--- |
| `project` | Yes | All 3 | Also accepts legacy alias `project_name`. |
| `rooms[].id`, `name`, `zone` | Yes | All 3 | `zone` values: `public`, `private`, `circulation`, `service`, `exterior`. |
| `rooms[].x`, `y`, `w`, `h` | Recommended | `audit`, `cost`, `render` | Feet from `(0, 0)` origin; `area_sqft` auto-computes as `w * h` if omitted. |
| `rooms[].windows[]` | For sleeping/habitable | `audit`, `cost` | Checked for IRC R310 egress, R303 8% glazing, and cost takeoffs. |
| `connections[]` | Recommended | `audit`, `render` | `render_floorplan_svg.py` auto-derives `circulation_paths` between room centers from `connections[]` when explicit `circulation_paths` are omitted. |
| `grid_x`, `grid_y` | Optional | `render` | Auto-derived from unique sorted room edge coordinates when omitted. |
| `doors[]`, `windows[]` | Optional | `render` | Top-level SVG placement coordinates; omitted safely if not supplied. |
| `shared_walls[]` | Optional | `audit` | Audits acoustic decoupling between `private` and `service`/`public` wings. |
