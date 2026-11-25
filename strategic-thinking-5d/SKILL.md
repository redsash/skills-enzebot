---
name: strategic-thinking-5d
description: >-
  Applies Dan Koe's 5D Thinking framework (Wilber's AQAL, Kegan stages, holarchies) to diagnose systemic bottlenecks and stress-test POCs or architectures. Use only on /strategic-thinking-5d or when explicitly invoking 5D thinking, AQAL, Kegan stages, or integral holarchy diagnostics. Do not use for multi-persona debates (perspectives), forensic root-cause falsification (competing-hypothesis), or editorial prose de-slopping (human-readable).
taxonomy:
  phase: [deliberate]
  modality: [lens]
  domain: [architecture-strategy]
  interaction: interactive
metadata:
  model-tier: "deep"
  effort: "high"
  invocation: "manual"
---

# 5D Strategic Thinking

A cognitive framework and decision engine designed to elevate reasoning beyond one-dimensional, reductionist traps. Grounded in Dan Koe's 5D Thinking and synthesized with Ken Wilber's Integral Theory (AQAL), Robert Kegan's constructive-developmental psychology, and holarchical systems evolution.

---

## When to Use This Skill
- **POC & Product Stress-Testing**: Evaluating nascent architecture, prototypes, or venture hypotheses to uncover hidden blockers outside the primary technical domain.
- **Architectural & Business Trade-offs**: Resolving thorny dilemmas where adding more technical features (horizontal knowing) fails to resolve the underlying friction (vertical understanding).
- **Root-Cause Bottleneck Diagnosis**: Pinpointing which adjacent skill-tree deficiency (Altitude) is silently choking a project or team.
- **Do not use for**: Trivial syntax lookups, routine bug fixes, multi-persona debates (`perspectives`), or editorial prose de-slopping (`human-readable`).

> **References & Examples**: See [Theoretical Lineages & Prompt Template](references/REFERENCE.md) and [Worked Example: POC Diagnostic](examples/poc-diagnostic-example.md).
> **Composition**: Use `/strategic-thinking-5d` for structural AQAL/Kegan/holarchy diagnostics; compose with `human-readable` afterward when polishing prose for external publication.

---

## The 5 Dimensions at a Glance

```
                         5D: TIME & EVOLUTION
                  (Transcend & Include / Holarchies)
                                  ▲
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    │   4D: THE FOUR QUADRANTS OF REALITY (Wilber's AQAL)       │
    │   UL: Subjective (Psychology)  │ UR: Objective (Behavior) │
    │   LL: Culture (Shared Norms)   │ LR: Systems (Infra/Econ) │
    └─────────────────────────────┼─────────────────────────────┘
                                  │
           3D: LEVELS OF COGNITIVE EVOLUTION (Stages)
    [L0: Instinctual] → [L1: Conformist] → [L2: Individualist]
                → [L3: Synthesist] → [L4: Generative]
                                  │
        2D: LINES, LEVELS & ALTITUDE (The Skill Tree)
      (Lines = Domain Width, Level = Depth, Altitude = Weighted Avg)
                                  │
         1D: HORIZONTAL VS. VERTICAL DEVELOPMENT
              (Knowing Facts vs. Upgrading the OS)
```

---

## 5D Diagnostic Protocol

### Step 1: 1D Diagnostic (Knowing vs. Understanding)
- Disentangle **horizontal facts** (adding more features, code libraries, data, or marketing channels) from **vertical structure** (the mental model and framing of the problem).
- Ask: *"Are we attempting to solve an operating system problem with an application update?"*
- Identify what unexamined assumption is being treated as an absolute law.

#### Step 2: 2D Audit (Lines, Levels & Altitudes)
- **Lateral Collisions (Lines)**: Identify 3 distinct domains outside the immediate field (e.g., biological immune systems, municipal zoning, game theory, distributed consensus) that intersect this problem. Extract the least intuitive insight.
- **Skill-Tree Altitude Bottleneck**: Pinpoint the adjacent, uninspected capability where underdevelopment is actively capping progress. (e.g., *"The technical architecture is Level 3, but the governance/incentive model is Level 1, causing organizational rejection."*)

#### Step 3: 3D Evolution (Tier-1 to Tier-2 Shift)
- **Level 1 (Conformist / Consensus)**: State the default industry dogma or standard playbook.
- **Level 2 (Individualist / Contrarian)**: State the sharp technical or critical pushback that contrarians cite.
- **Level 3 (Synthesist)**: Reconcile both into a higher-order model where the paradox is resolved contextually.
- **Level 4 (Generative)**: Articulate the novel, unmapped paradigm that creates a new category or advantage.

#### Step 4: 4D Integral Mapping (AQAL)
Audit the POC or decision across all four quadrants:
1. **Upper-Left (Subjective / Psychology)**: What emotional resistance, cognitive load, or identity threats does this trigger in users/stakeholders?
2. **Upper-Right (Objective / Behavior & Mechanics)**: What are the exact physical actions, UI steps, telemetry metrics, and verifiable behaviors required?
3. **Lower-Left (Intersubjective / Culture & Tribe)**: What tribal values, social status markers, or cultural norms support or resist this change?
4. **Lower-Right (Interobjective / Systems & Economics)**: How does this fit into existing economic incentives, legal frameworks, and technical infrastructure?

#### Step 5: 5D Evolutionary Holarchy (Time & Holons)
- **Transcend and Include**: Identify the foundational components that must be preserved. A higher-order innovation must never destroy the lower-order baseline it depends on (e.g., radical UI changes cannot destroy baseline data integrity).
- **1-Year vs. 10-Year Horizon**: What is the trajectory if this decision is made vs. if the status quo remains?
- **Techno-Economic Wave**: What inevitable paradigm shift (e.g., local sovereign AI, agentic compute, privacy-first infrastructure) does this position itself for?

### Step 6: Output Contract

Keep diagnostics compact and structured (see [Worked Example](examples/poc-diagnostic-example.md)):

```markdown
# 5D Strategic Diagnostic: [Topic / POC Name]
1. **1D Shift (Horizontal vs. Vertical)**: [Surface symptom] vs. [Underlying framing constraint]
2. **2D Cross-Pollination & Altitude**: [Orthogonal domain insight] | **Bottleneck**: [Lagging line]
3. **3D Evolution**: L1 Consensus -> L2 Contrarian -> L3 Synthesist -> L4 Generative
4. **4D AQAL Audit**: UL (Mindset) | UR (Mechanics) | LL (Culture) | LR (Systems/Econ)
5. **5D Trajectory**: [Foundational holon preserved] | [1-yr vs. 10-yr divergence]
6. **Go / No-Go & 72h Experiment**: [Threshold] | [Concrete test]
```

---

## Anti-Patterns & Common Traps

| Trap | Failure Mode | Corrective Action |
| :--- | :--- | :--- |
| **Quadrant Reductionism** | Viewing everything strictly through code/systems (LR) or strictly through mindset (UL). | Force explicit analysis of all 4 quadrants before making a recommendation. |
| **The "Smart-but-Stuck" Loop** | Gathering more books, benchmarks, or articles when stuck. | Stop horizontal information collection. Audit adjacent skill lines (Altitude) to locate the prerequisite block. |
| **Premature Dogma Defense** | Feeling threatened by an opposing perspective and reacting with pre-programmed talking points. | Notice ego-friction. Re-center in Level 3 (Synthesist): *"What context makes the opposing view valid?"* |
| **Transcend-without-Include** | Chasing a radical new abstraction while breaking foundational reliability or unit economics. | Verify that foundational holons (lower levels) remain healthy and intact. |
