---
name: perspectives
description: >-
  Stress-tests decisions, strategic dilemmas, and complex architectural forks by simulating a multi-expert advisory panel and adversarial cross-debate. Use only on /perspectives or when explicitly asked for a multi-expert advisory panel or adversarial persona cross-debate. Do not use for routine factual lookups, forensic root-cause falsification (competing-hypothesis), or AQAL/5D strategic framing (strategic-thinking-5d).
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

# Perspectives (Expert Advisory Panel)

Stress-tests decisions, resolves strategic dilemmas, and evaluates architectural or business trade-offs by facilitating a dynamic cross-debate among elite, contextually tailored personas. Rather than outputting flat, isolated lists of pros and cons, this skill simulates adversarial friction to uncover hidden blind spots and deliver high-conviction executive synthesis.

---

## When to Use This Skill
- High-stakes architectural or technology forks (e.g., monolith vs. microservices, build vs. buy, cloud vs. on-prem).
- Strategic business or product dilemmas (e.g., pricing model shifts, open-core vs. proprietary, pivot directions).
- Red-teaming plans before committing budget, engineering headcount, or public announcements.
- **Do not use for**: Routine factual lookups, single-answer syntax questions, or procedural debugging tasks.

---

## Workflow / Procedure

### Step 1: Frame the Dilemma & Extract Constraints
Analyze the user's situation to isolate:
1. **The Core Tension**: What are the competing values (e.g., speed vs. stability, autonomy vs. compliance)?
2. **Hard Constraints**: Budget, timeline, team skills, existing commitments, or regulatory requirements.
3. **The Reversible vs. Irreversible Stakes**: Is this a Type-1 (one-way door) or Type-2 (two-way door) decision?

### Step 2: Dynamic Panel Seeding
Curate a panel of **4–5 hyper-specific expert archetypes** tailored to the problem domain. Never use generic titles like "The Tech Guy" or "The Business Leader".

**Mandatory Composition**:
- **The Aggressive Skeptic / Red Teamer**: Dedicated to stress-testing assumptions, simulating worst-case failure modes, edge-case collapses, and market risks.
- **The Visionary / Opportunity Maximizer**: Dedicated to preserving core ambition, upside potential, and long-term leverage.
- **The Pragmatic Operator / Execution Specialist**: Focuses on logistics, staffing reality, rollout sequencing, and migration pain.
- **Domain Specialists (1–2)**: Deep domain practitioners relevant to the exact context (e.g., FinTech Compliance Auditor, High-Throughput DB Internals Engineer, Enterprise Procurement Veteran).

### Step 3: Adversarial Cross-Debate & Friction Simulation
Do not present disconnected essays or parallel bullet points. Format this phase as an **interactive, back-and-forth dialogue** where personas actively challenge, rebut, and build on each other's points:
- The Skeptic attacks the central assumption.
- The Operator counters with logistical mitigations or exposes hidden maintenance costs.
- The Visionary pushes back when caution threatens to eliminate competitive advantage.
- Personas must directly address each other by name (e.g., *"Sarah is overlooking the cold-start latency..."*).

### Step 4: Executive Synthesis & Decision Matrix
Close the debate with a unified, actionable synthesis:
1. **Uncovered Blind Spots**: What assumptions were dismantled during the friction?
2. **Consensus vs. Unresolved Disagreements**: Where did the panel align, and what remains an active risk?
3. **Go / No-Go Decision Framework**: Clear condition-based thresholds for proceeding.
4. **Immediate 72-Hour Next Steps**: Concrete actions to de-risk the path forward.

---

## Output Contract

Force genuine cross-talk and an actionable Go/No-Go synthesis (see [Worked Example: Architecture Debate](examples/architecture-debate-example.md)):

```markdown
## Expert Panel Lineup
| Expert | Hyper-Specific Archetype | Primary Angle |
| :--- | :--- | :--- |

## Live Adversarial Cross-Debate
**[Name 1]**: "[Opening thesis...]"
**[Name 2 (Skeptic)]**: "[Direct rebuttal naming Name 1...]"
*(2–3 high-density rounds of direct back-and-forth challenge)*

## Executive Synthesis
- **Critical Blind Spots Surfaced**: [Dismantled assumptions]
- **Go / No-Go Criteria**: PROCEED IF [...] | HALT IF [...]
- **Immediate 72-Hour Next Steps**: [1..2 concrete de-risking actions]
```

---

## Gotchas & Failure Modes

- **The Polite Consensus Trap**: LLMs naturally default to consensus and harmony. Force real tension—experts should represent fundamentally conflicting priorities and risk profiles.
- **The Parallel Monologues Anti-Pattern**: Personas delivering isolated speeches without engaging with previous arguments. Enforce conversational rebuttals.
- **Generic Personas**: Avoid vague titles ("Senior Developer"). Use precise anchors ("Staff Reliability Engineer specializing in Distributed State Machines").
- **Hollow "Pros & Cons" Summaries**: Avoid ending with *"both options have merits"*. Force an opinionated decision framework with actionable criteria.
