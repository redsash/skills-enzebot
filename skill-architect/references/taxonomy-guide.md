# AI Agent Skills Taxonomy & Classification Guide

A formal, faceted classification system for cataloging, discovering, and dynamically routing AI Agent Skills.

---

## 1. Why Flat Categories and Tags Fail

As agent skill ecosystems grow beyond small collections, flat classification systems break down in two ways:

1. **Human Cognitive Overload**: Forcing a skill into a single top-level category creates false trade-offs. For example, is `blast-radius-audit` a "review" skill, a "planning" skill, or a "DevOps" skill? 
2. **Agent Context Starvation**: Dumping hundreds of skill triggers into an agent's initial prompt wastes token budgets and causes trigger interference.
3. **Folksonomic Rot**: Freeform tags rapidly degrade into messy synonyms (`test`, `testing`, `qa`, `unit-tests`, `flaky-tests`).

To solve this, Agent Skills adopt **Faceted Classification** (inspired by library science colon classification). Instead of a single rigid folder hierarchy, each skill is positioned along **three orthogonal coordinates**:

```
                       ┌─────────────────────────┐
                       │    AGENT SKILL COORDS   │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    1. Phase (When)        2. Modality (How)       3. Domain (What)
   Cognitive lifecycle     Mechanics & contents    Knowledge vertical
```

---

## 2. The Three Core Facets

### Facet 1: Cognitive Phase (`phase`)
*Where in the agent's cognition or task execution lifecycle does this skill fire?*

| Phase | Purpose | Agent Cognitive Action | Examples |
| :--- | :--- | :--- | :--- |
| **`explore`** | Problem discovery & landscape mapping | Investigating unknowns, reading docs, tracing architectures | `deeply-investigate` |
| **`deliberate`** | Decision-making & stress-testing | Evaluating trade-offs, weighing hypotheses, debate, planning | `perspectives`, `competing-hypothesis`, `strategic-thinking-5d` |
| **`author`** | Generative creation & synthesis | Synthesizing code, CAD diagrams, documentation, scaffolding | `cad-floorplan-designer`, `adr-synthesizer` |
| **`critique`** | Review, audit, & verification | Auditing safety, checking principles, removing slop, linting | `human-readable`, `programming-fundamentals`, `blast-radius-audit` |
| **`maintain`** | Remediation, capture, & cleanup | Fixing flakes, logging journals, postmortems, pruning | `research-journaler`, `dead-code-pruner`, `incident-postmortem` |
| **`meta`** | Orchestration & self-governance | Authoring skills, configuring agents, benchmarking | `skill-architect` |

#### Cardinality Rule: 1..n (Single-Phase Strongly Recommended)
While the schema permits multiple phases (`1..n`) to accommodate hybrid transition workflows (e.g., `flaky-test-hunter` traversing `explore` $\rightarrow$ `maintain`), **single-phase assignment is the gold standard**. If a skill spans 3+ phases, it is likely a "megaskill" that should be decomposed into composable sub-skills.

---

### Facet 2: Operational Modality (`modality`)
*What is the skill made of, and how does it execute its instructions?*

| Modality | Nature | Mechanics | Examples |
| :--- | :--- | :--- | :--- |
| **`lens`** | Epistemic / Cognitive Model | Prompts that reshape *how* the agent reasons (eliminating biases, adopting personas, lateral thinking). | `competing-hypothesis` (ACH), `strategic-thinking-5d` |
| **`spec`** | Rule / Invariant / Grammar | Hard constraints, design rules, and schema definitions the agent must uphold. | `programming-fundamentals`, CMU modular grids |
| **`runbook`** | Procedural Protocol | Ordered checklists, investigative workflows, and step-by-step procedures. | `deeply-investigate`, `research-journaler` |
| **`harness`** | Scripted Automation | Bundled executable code (`scripts/`), deterministic CLI tools, AST analyzers, or linters. | `skill-architect` (`validate_skill.py`), SVG generators |

#### Cardinality Rule: 1..n (Compound Modalities Encouraged)
Skills frequently pair modalities—for example, a `spec` enforced by a `harness` (e.g. architectural rules paired with an AST validator), or a `runbook` that applies a cognitive `lens`.

---

### Facet 3: Domain Vertical (`domain`)
*What subject matter or operational context does the skill target?*

Canonical domains include:
* **`architecture-strategy`**: High-level systems design, strategic planning, decision analysis.
* **`software-engineering`**: Code authoring, refactoring, API integration, debugging.
* **`operations-reliability`**: SRE, incident response, CI/CD, deployment verification, logging.
* **`editorial-communication`**: Technical writing, documentation, prose humanization, release notes.
* **`physical-spatial-design`**: CAD, architectural layout, hardware engineering, physical specifications.
* **`agent-meta`**: Agent behavior, skill authoring, tool development, prompt optimization.

*Note: New domains can be introduced as ecosystems expand without altering `phase` or `modality`.*

---

### Optional Attribute: Interaction Mode (`interaction`)
*Does the skill require human dialogue or execute autonomously?*

* **`interactive`**: Multi-turn dialogue, interview questions, or human decision gates (e.g. advisory panels).
* **`autonomous`**: Fire-and-forget; runs end-to-end without requiring human intervention unless blocked.

---

## 3. Manifest Declaration (`SKILL.md`)

Declare taxonomy in the YAML frontmatter:

```yaml
---
name: competing-hypothesis
description: >-
  Evaluates complex, ambiguous, or contradictory evidence against multiple mutually exclusive explanations using Richards Heuer's Analysis of Competing Hypotheses (ACH) methodology.
taxonomy:
  phase: [deliberate]
  modality: [lens]
  domain: [architecture-strategy, operations-reliability]
  interaction: interactive
---
```

*(Inline lists like `[deliberate]` or single scalar strings `deliberate` are both accepted).*

---

## 4. Hierarchical Agent Dispatch (Why This Matters)

In a large repository (500+ skills), an orchestrator should not inject all skill prompts at once. The taxonomy enables **coarse-to-fine dispatching**:

```
[User Request] 
      │
      ▼
1. Phase & Domain Filter: "Phase: deliberate, Domain: architecture-strategy"
      │
      ▼ (Reduces 500 skills to 3 candidates)
2. Fine-grained Trigger Matching: Compare query against remaining 3 descriptions
      │
      ▼
3. Execute Skill: Inject chosen skill into execution context
```
