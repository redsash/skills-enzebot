# Construction Cost Estimation Guide for Schematic Floor Plans

A parametric, quantity-surveying-based framework for generating construction cost estimate ranges with defined confidence intervals for modular masonry (CMU), hillside, and hurricane-resilient construction.

---

## 1. AACE Estimate Classification & Confidence Calibration

At the schematic floor plan stage (1%–15% project definition), construction cost estimates fall under **AACE International Class 4 / Class 5**:
- **Purpose**: Concept screening, program feasibility, and preliminary budget authorization.
- **Expected Accuracy Band**: **$-15\%$ to $+25\%$** (or $-20\%$ to $+30\%$ in high-volatility island markets).
- **Golden Rule**: Never provide a single "point estimate" at schematic stage. Always present a **Confidence Range**:
  $$\text{Low Bound} = \text{Expected} \times 0.85 \quad (-15\%)$$
  $$\text{High Bound} = \text{Expected} \times 1.25 \quad (+25\%)$$

---

## 2. Program-Differentiated Square Footage Rates

Applying a single flat square-foot rate across an entire building leads to severe distortion. Covered terraces, utility vaults, and conditioned living spaces have radically different material and MEP intensities.

### Baseline Space Categories (Standard Resilient Specification)

| Program Zone | Finish & MEP Intensity | Mainland Baseline ($/sq ft) | Island / Coastal Baseline ($/sq ft) |
| :--- | :--- | :--- | :--- |
| **Conditioned Living & Dining** | High: HVAC, architectural finishes, recessed lighting, tile | $200 – $260 | $280 – $360 |
| **Conditioned Bedrooms & Suites** | High: HVAC, closets, ensuite baths, impact windows | $210 – $280 | $290 – $380 |
| **Kitchen & Pantry Core** | Premium: Cabinetry, stone counters, plumbing, appliances | $300 – $420 | $400 – $550 |
| **Covered Terraces / Lanais** | Medium: Concrete slab, exposed rafters, soffit, outdoor tile | $90 – $130 | $130 – $180 |
| **Enclosed Utility / Mechanical** | Low: Sealed concrete, fire-rated drywall/CMU, louvered vent | $110 – $150 | $150 – $210 |
| **Uncovered Decks / Hardscape** | Low: Graded pavers, exterior slab, pool surround | $45 – $75 | $65 – $110 |

### Specification Finish Tiers
- **Economy**: Basic ceramic tile, standard vinyl sliders, laminate counters, split ACs ($0.80\times$ baseline).
- **Standard Resilient (Default)**: Porcelain tile, impact-rated aluminum glazing, quartz counters, multi-zone inverter mini-splits, 8" CMU ($1.00\times$ baseline).
- **Luxury Coastal**: Large-format imported tile, motorized concealed pocket sliders, custom hardwood millwork, VRF ducted HVAC ($1.45\times–1.75\times$ baseline).

---

## 3. Structural Masonry & Concrete Takeoffs

Rather than estimating structure purely from floor area, calculate physical quantities directly from the CAD grid:

### 3.1 Exterior 8" CMU Wall Shell
$$\text{Gross Wall Area} = \text{Perimeter (ft)} \times \text{Story Height (ft)}$$
$$\text{Net Wall Area} = \text{Gross Wall Area} - \sum \text{Window/Door Opening Areas}$$
- **Block Quantity**: Net Wall Area ($\text{sq ft}$) $\times 1.125 \text{ blocks/sq ft}$.
- **Grout & Rebar Fill**: Vertical reinforced grouted cells every 32"–48" oc, plus all corners, jambs, and horizontal bond beams (approx. $0.35\text{ cu ft}$ grout per sq ft of wall).
- **Installed Cost**: $22–$34 per sq ft of net wall area (mainland); $32–$48 per sq ft (island/Caribbean).

### 3.2 Floor & Roof Slabs
- **Ground Floor Slab-on-Grade**: 4"–6" reinforced concrete over vapor barrier and compacted fill ($12–$18/sq ft).
- **Elevated Suspended Slab**: 6"–8" cast-in-place concrete deck over shoring (inverted living upper level) ($28–$42/sq ft).

---

## 4. Topography & Site Slope Multipliers

Hillside conditions represent the largest variable in structural foundation cost. As slope steepens, foundation footings transform into engineered reinforced concrete retaining walls.

| Slope Category | Gradient (%) | Excavation & Foundation Impact | Slope Multiplier |
| :--- | :--- | :--- | :--- |
| **Flat** | 0% – 5% | Standard shallow strip footings, minimal cut/fill | **1.00×** |
| **Gentle** | 6% – 12% | Stepped footings, moderate cut/fill, short pony walls | **1.15×** |
| **Moderate** | 13% – 20% | Engineered retaining wall (4'–8' tall), benching, swales | **1.30×** |
| **Steep Hillside** | > 20% – 30% | Tall retaining wall (>8'), soil nails/tiebacks, pump truck access | **1.55×** |

*Note: For slopes $>15\%$, add an allowance for upslope perimeter interceptor drains and foundation waterproofing ($45–$75 per linear foot).*

---

## 5. Envelope & Hurricane Glazing Schedule

Glazing costs in hurricane/tropical coastal zones are heavily driven by impact rating requirements:

- **Impact-Rated Glazing (DP $\ge 50–70\text{ psf}$)**: Laminated tempered glass in heavy aluminum frames ($90–$140/sq ft of rough opening).
- **Multi-Slide Pocketing Terrace Doors**: Hurricane-rated 8'–10' tall sliding systems ($1,200–$2,000 per linear foot installed).
- **Standard Overhang Eaves**: Cantilevered 3'–4' soffit construction with hurricane hurricane clips and aluminum fascia ($35–$55/lf).

---

## 6. Resilience Core & Off-Grid Utility Budget

Itemize the resilient utility infrastructure as dedicated capital cost elements:

### 6.1 Domestic Cistern & Water Security
- **Cast-in-Place Concrete Cistern**: Sized at 800 to 1,500 gallons ($2.00–$3.50 per gallon of storage).
- **Filtration & Booster Station**: Variable-speed booster pump, dual 5-micron sediment filters, and UV disinfection lamp ($4,500–$7,500 complete).

### 6.2 Solar, Battery Storage & Generator Tie-In
- **Solar PV Array**: $1.60–$2.20 per Watt DC installed (e.g., 8 kW array $\approx \$13,000–\$17,500$).
- **Hybrid Inverter & ATS**: $4,500–$7,000.
- **Lithium Iron Phosphate ($LiFePO_4$) Battery Storage**: $700–$950 per kWh installed (e.g., 20 kWh bank $\approx \$14,000–\$19,000$).
- **Generator Readiness**: Manual or automatic generator transfer switch and weather-rated exterior receptacle ($1,800–$3,200).

### 6.3 Sanitary Waste & Drainage
- **Septic System**: Two-compartment concrete septic bio-digester tank and absorption percolation leach field ($7,500–$14,000 depending on soil percolation).

---

## 7. Soft Costs, Contingency & Contractor Fees

To derive the total estimated project cost, apply standardized project markups to the hard construction subtotal:

$$\text{Hard Construction Cost} = \sum (\text{Direct Program Costs} \times \text{Slope Factor}) + \text{Resilience Core}$$
$$\text{Contractor General Conditions, Overhead & Profit (O&P)} = \text{Hard Cost} \times 12\%$$
$$\text{Design & Estimating Contingency (Schematic Class 4)} = (\text{Hard Cost} + \text{O&P}) \times 15\%$$
$$\text{Architectural, Engineering & Permitting Soft Costs} = \text{Hard Cost} \times 8\%$$
