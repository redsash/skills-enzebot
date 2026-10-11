# Floor Plan AI Validation Framework

An architectural, geometric, and regulatory validation framework for evaluating generative AI floor plans and spatial layouts.

---

## 1. Geometric & Structural Validity (Automated)

Before evaluating whether a layout is functional or aesthetic, it must be verified as physically possible and geometrically coherent.

### 1.1 Watertight Perimeter Boundaries
- **Rule**: Exterior load-bearing walls must form a single, contiguous, closed polygon with zero accidental gaps or non-coincident vertices.
- **Verification**: Compute the boundary exterior cycle; verify that Euler characteristics and polygon closure conditions hold ($\text{Start Vertex} == \text{End Vertex}$ and no unclosed exterior endpoints).

### 1.2 Non-Overlapping Elements
- **Rule**: Distinct rooms, interior partitions, and structural columns must be mutually disjoint in interior 2D space.
- **Verification**: For every pair of rooms $(R_i, R_j)$ where $i \neq j$:
  $$\text{Area}(R_i \cap R_j) = 0$$
  Rooms may share boundary 1D edges (representing shared partitions or open thresholds), but 2D surface intersection area must strictly equal zero.

### 1.3 Wall Thickness & Orthogonal Alignment
- **Rule**: Structural CMU walls must maintain consistent, realistic thicknesses (8" exterior CMU, 4" or 6" interior partitions).
- **Verification**: Wall segment normals must snap to orthogonal grid angles ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) or explicitly declared site-specific angles (e.g., $45^\circ$ splay).

### 1.4 Dimensional Conservation
- **Rule**: Total gross building footprint must equal the sum of net interior room areas plus the physical area occupied by exterior and interior walls:
  $$\text{Gross Footprint} = \sum \text{Net Room Areas} + \text{Wall Footprints} \quad (\pm 1\% \text{ tolerance})$$
  Prevent hallucinated interior dimensions where interior room areas exceed the building footprint.

---

## 2. Architectural & Building Code Compliance (Rule-Based)

Enforce minimum life safety, health, and residential building standards based on the International Residential Code (IRC) and International Building Code (IBC).

### 2.1 Emergency Escape & Rescue Openings (IRC R310)
- **Requirement**: Every sleeping room (bedroom) must have at least one operable emergency escape and rescue opening directly to the exterior or yard.
- **Dimensional Minimums**:
  - Minimum net clear opening area: **$5.7\text{ sq ft}$** ($0.53\text{ m}^2$) at ground/upper floors ($5.0\text{ sq ft}$ for grade floor).
  - Minimum net clear opening height: **$24\text{ inches}$** ($610\text{ mm}$).
  - Minimum net clear opening width: **$20\text{ inches}$** ($508\text{ mm}$).
  - Maximum sill height above finished floor level: **$44\text{ inches}$** ($1118\text{ mm}$).

### 2.2 Minimum Room Areas & Dimensions (IRC R304)
- **Habitable Rooms**: At least one habitable room in every dwelling must have $\ge 120\text{ sq ft}$ of gross floor area.
- **Other Habitable Rooms**: Bedrooms, dining, and study rooms must have a floor area of not less than **$70\text{ sq ft}$** ($6.5\text{ m}^2$).
- **Minimum Horizontal Dimension**: Habitable rooms must not be less than **$7\text{ feet}$** ($2.13\text{ m}$) in any horizontal dimension (excluding kitchens).
- **Ceiling Height**: Minimum clear ceiling height of **$7\text{ ft} - 0\text{ in}$** ($2134\text{ mm}$) across required spaces.

### 2.3 Natural Light & Ventilation (IRC R303)
- **Glazing Ratio**: Minimum glazed area for all habitable rooms must be $\ge 8\%$ of the floor area of that room.
- **Ventilation Ratio**: Minimum openable ventilation area to the outdoors must be $\ge 4\%$ of the floor area being ventilated.

### 2.4 Sanitary Clearances & Privacy (IRC R307)
- **Water Closet Clearances**: Minimum **$21\text{ inches}$** ($533\text{ mm}$) of clear space in front of the water closet, bidet, or lavatory.
- **Centerline Clearance**: Minimum **$15\text{ inches}$** ($381\text{ mm}$) from the centerline of the water closet to any side wall, partition, or vanity.
- **Kitchen-Bathroom Separation**: Water closets must not open directly into a kitchen or food-preparation area without an intervening ventilated vestibule, hallway, or baffling wall.

---

## 3. Functional Design & Spatial Heuristics (Heuristic)

Evaluate the ergonomic flow and livability of the design using spatial syntax and graph theory.

### 3.1 Topological Depth & Zoning
- **Public vs. Private Gradient**: Invert and tier rooms by privacy level. Private bedrooms must be topologically deeper in the graph (depth $\ge 2$ from main entry) than public foyer, living, and dining zones.
- **Service Segregation**: Mechanical plant, battery banks, and cistern booster pumps must be physically and acoustically isolated from sleeping quarters.

### 3.2 Furniture Clearance Envelopes
To verify real-world room utility, test each room against standard furniture bounding boxes plus a continuous **36" (914 mm) circulation buffer**:

| Room Type | Required Minimum Furniture Set | Minimum Footprint ($W \times L$) | Minimum Clearance Lane |
| :--- | :--- | :--- | :--- |
| **Primary Bedroom** | King Bed + 2 Nightstands + Dresser | $11' \times 12'$ | $36"$ walking lane around bed |
| **Secondary Bedroom** | Queen Bed + 1 Nightstand + Desk | $10' \times 10'$ | $36"$ access lane |
| **Dining Room** | 6-Person Table + Chairs Outward | $10' \times 12'$ | $36"$ behind seated diners to walls |
| **Living Room** | Sofa + Coffee Table + Media Credenza | $12' \times 14'$ | $36"$ arterial through-traffic lane |

### 3.3 Grocery & Beach Logistics Routing
- **Grocery Transit Hop Count**: Path from parking/entry to pantry must be $\le 2$ topological hops with no narrow choke points ($< 36"$).
- **Wet-to-Dry Beach Loop**: Direct path from exterior pool/beach to outdoor shower or laundry wash without crossing dry living room floor surfaces.

---

## 4. Quantitative & Benchmarking Metrics (Data-Driven)

Measure generative fidelity and constraint adherence:

### 4.1 Setback & Envelope Intersection over Union (IoU)
$$\text{Envelope Compliance} = \frac{\text{Area}(\text{Building Footprint} \cap \text{Buildable Envelope})}{\text{Area}(\text{Building Footprint})} == 1.0$$
Any non-zero protrusion into required front, rear, or side setbacks represents a critical constraint violation ($\text{Violation Area} == 0$).

### 4.2 Program Precision & Recall
- **Prompt Recall ($R$)**:
  $$R = \frac{\text{Count of Requested Spaces Successfully Provided}}{\text{Count of User-Requested Spaces}}$$
  Must equal $1.0$ (e.g., if user asks for 3 bedrooms and 2 bathrooms, layout must generate all 5 spaces).
- **Extraneous Precision ($P$)**:
  $$P = \frac{\text{Count of Requested Spaces}}{\text{Total Spaces Generated}}$$

---

## 5. Expert Review & Stress Testing (Human-in-the-Loop)

### 5.1 Blind Architectural AB Testing
- Compare candidate AI layouts against human architect baseline plans under identical site and zoning constraints.
- Evaluate on:
  1. Efficiency of square footage (ratio of net usable living area to circulation hallway area; target: circulation $\le 12\text{--}15\%$ of gross area).
  2. Passive solar and wind defense (breeze harvesting vs. storm protection).
  3. Visual appeal and spatial drama (sightlines from entry to views).

### 5.2 Adversarial Site Stress Tests
Stress-test generative layout engines with extreme boundary conditions:
- **Test Case 1: Ultra-Narrow Infill**: $22\text{ ft}$ lot width with zero side lot lines (row-house / townhouse typology).
- **Test Case 2: Steep Hillside Retaining Constraint**: 30% gradient requiring split-level walk-out retaining structure.
- **Test Case 3: Coastal High-Wind Flank**: $160\text{ mph}$ exposure requiring blind windward masonry shear walls and recessed leeward sliding tracks.
