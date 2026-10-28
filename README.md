# skills-enzebot

A curated collection of agent skills designed, authored, and maintained according to the [Open Skills specification](https://agentskills.io/specification.md) and [Antigravity](https://antigravity.google/docs/skills.md) guidelines.

```bash
npx skills add redsash/skills-enzebot
```

---

## Skills Taxonomy & Classification Matrix

To prevent repository bloat, tag fatigue, and context exhaustion in large agent environments, skills in this repository are cataloged using a **Faceted Classification System** across three orthogonal coordinates (plus an optional interaction mode):

1. **Cognitive Phase (`phase`)**: Rather than a rigid state machine, **Phase is a Cognitive Stance**. At any given turn, what is the agent's posture?
   * *Am I opening the aperture?* &rarr; `explore` (discovery, research, mapping unknowns)
   * *Am I eliminating rival hypotheses?* &rarr; `deliberate` (decision analysis, trade-off evaluation, planning)
   * *Am I putting ink on paper?* &rarr; `author` (generative creation, synthesis, scaffolding)
   * *Am I holding a red pen?* &rarr; `critique` (quality review, principle auditing, anti-slop editing)
   * *Am I recording the trail?* &rarr; `maintain` (remediation, drift prevention, logging, cleanup)
   * *Am I observing or tooling the system itself?* &rarr; `meta` (agent behavior, self-governance, skill engineering)
2. **Operational Modality (`modality`)**: How the skill enforces its instructions:
   * `lens`: Epistemic model or cognitive framework that shifts reasoning style.
   * `spec`: Hard rules, invariants, and domain constraints.
   * `runbook`: Sequential protocol, ordered checklist, or procedure.
   * `harness`: Executable script, deterministic CLI utility, or validator.
3. **Domain Vertical (`domain`)**: Subject matter boundary (`architecture-strategy`, `software-engineering`, `operations-reliability`, `editorial-communication`, `physical-spatial-design`, `agent-meta`).

For detailed specifications, see the [Taxonomy & Classification Guide](skill-architect/references/taxonomy-guide.md).

---

## Skills Index

| Skill | Phase | Modality | Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| [cad-floorplan-designer](./cad-floorplan-designer/SKILL.md) | `author` | `spec`, `harness` | `physical-spatial-design` | Designs buildable 2D architectural CAD floor plans and spatial layouts adhering to CMU modularity. |
| [competing-hypothesis](./competing-hypothesis/SKILL.md) | `deliberate` | `lens` | `architecture-strategy`, `operations-reliability` | Evaluates ambiguous or contradictory evidence against rival hypotheses using Richards Heuer's ACH. |
| [deeply-investigate](./deeply-investigate/SKILL.md) | `explore` | `runbook` | `software-engineering`, `architecture-strategy` | Investigates nascent architectures, APIs, or documents against primary sources into a progressive-disclosure dossier. |
| [discord-webhook-script-writer](./discord-webhook-script-writer/SKILL.md) | `author` | `runbook`, `harness` | `software-engineering`, `operations-reliability` | Interactively crafts and generates robust, ShellCheck-compliant Bash scripts for Discord webhooks. |
| [human-readable](./human-readable/SKILL.md) | `critique` | `lens`, `spec` | `editorial-communication` | Eliminates AI cliches, robotic mannerisms, and throat-clearing from written drafts so they read naturally. |
| [perspectives](./perspectives/SKILL.md) | `deliberate` | `lens` | `architecture-strategy` | Stress-tests decisions and architectural forks by simulating a multi-expert advisory panel and cross-debate. |
| [programming-fundamentals](./programming-fundamentals/SKILL.md) | `critique`, `author` | `spec` | `software-engineering` | Applies timeless engineering principles (DRY, KISS, YAGNI, SRP, Demeter, POLA, SoC) to review and simplify code. |
| [research-journaler](./research-journaler/SKILL.md) | `maintain` | `runbook`, `harness` | `operations-reliability`, `software-engineering` | Initializes, structures, and logs reproducible research sessions into chronological journal entries. |
| [skill-architect](./skill-architect/SKILL.md) | `meta` | `runbook`, `harness` | `agent-meta` | Designs, scaffolds, evaluates, and validates agent skills according to Open Skills and taxonomy standards. |
| [strategic-thinking-5d](./strategic-thinking-5d/SKILL.md) | `deliberate` | `lens` | `architecture-strategy` | Applies 5D Thinking (AQAL, Kegan stages, holarchies) to diagnose bottlenecks, stress-test POCs, and eliminate slop. |

---

## Skills Wishlist & Brainstorming

Candidate skills planned for development, pre-classified into the taxonomy matrix:

| Candidate Skill | Planned Phase | Planned Modality | Planned Domain | Proposed Description |
| :--- | :--- | :--- | :--- | :--- |
| `adr-synthesizer` | `author` | `runbook` | `architecture-strategy`, `software-engineering` | Synthesizes scattered design threads, PR reviews, and RFC notes into structured Architecture Decision Records. |
| `blast-radius-audit` | `critique` | `runbook`, `harness` | `operations-reliability`, `software-engineering` | Audits proposed code and infrastructure changes before execution to map dependency knock-on effects and rollback steps. |
| `dead-code-pruner` | `maintain` | `harness` | `software-engineering` | Identifies and verifies unused exports, obsolete feature flags, and abandoned routes for safe deletion. |
| `flaky-test-hunter` | `explore`, `maintain` | `runbook`, `harness` | `software-engineering`, `operations-reliability` | Isolates and reproduces non-deterministic test failures caused by race conditions, state leaks, and timing sensitivities. |
| `incident-postmortem` | `maintain` | `runbook` | `operations-reliability` | Assembles incident timelines, isolates contributing system factors, and drafts blameless postmortems with remediation items. |

---

## Creating & Validating Skills

To scaffold a new skill with taxonomy metadata using `skill-architect`:

```bash
python3 skill-architect/scripts/scaffold_skill.py <skill-name> \
  --description "<one-line imperative description>" \
  --phase <explore|deliberate|author|critique|maintain|meta> \
  --modality <lens|spec|runbook|harness> \
  --domain <domain-slug>
```

To validate an existing skill (verifying frontmatter, taxonomy, line budget, links, and Mermaid syntax):

```bash
python3 skill-architect/scripts/validate_skill.py <path-to-skill>
```
