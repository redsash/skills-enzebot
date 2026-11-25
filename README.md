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

| Skill | Phase | Modality | Domain | Invocation | Tier | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [cad-floorplan-designer](./cad-floorplan-designer/SKILL.md) | `author` | `spec`, `harness` | `physical-spatial-design` | `auto` | `deep` | Designs buildable 2D architectural CAD floor plans and spatial layouts adhering to CMU modularity. |
| [competing-hypothesis](./competing-hypothesis/SKILL.md) | `deliberate` | `lens` | `architecture-strategy`, `operations-reliability` | `hybrid` | `deep` | Evaluates ambiguous or contradictory evidence against rival hypotheses using Richards Heuer's ACH. |
| [deeply-investigate](./deeply-investigate/SKILL.md) | `explore` | `runbook` | `software-engineering`, `architecture-strategy` | `hybrid` | `orchestrator` | Investigates nascent architectures, APIs, or documents against primary sources into a progressive-disclosure dossier. |
| [discord-webhook-script-writer](./discord-webhook-script-writer/SKILL.md) | `author` | `runbook`, `harness` | `software-engineering`, `operations-reliability` | `auto` | `standard` | Interactively crafts and generates robust, ShellCheck-compliant Bash scripts for Discord webhooks. |
| [engineering-log](./engineering-log/SKILL.md) | `maintain` | `lens`, `spec`, `harness` | `software-engineering`, `operations-reliability`, `agent-meta` | `manual` | `fast` | Captures cross-project epistemic deltas, dead-end signatures, typed graph links, and human-agent loop telemetry into sharded ML-ready JSONL ledgers. |
| [human-readable](./human-readable/SKILL.md) | `critique` | `lens`, `spec` | `editorial-communication` | `auto` | `fast` | Eliminates AI cliches, robotic mannerisms, and throat-clearing from written drafts so they read naturally. |
| [perspectives](./perspectives/SKILL.md) | `deliberate` | `lens` | `architecture-strategy` | `manual` | `deep` | Stress-tests decisions and architectural forks by simulating a multi-expert advisory panel and cross-debate. |
| [quant-edge-auditor](./quant-edge-auditor/SKILL.md) | `critique` | `harness` | `data-science` | `hybrid` | `orchestrator` | Audits sports betting and predictive quantitative models for statistical edge, leakage, calibration, and market efficiency. |
| [research-journaler](./research-journaler/SKILL.md) | `maintain` | `runbook`, `harness` | `operations-reliability`, `software-engineering` | `manual` | `fast` | Initializes, structures, and logs reproducible repo-local research sessions into chronological journal entries. |
| [skill-architect](./skill-architect/SKILL.md) | `meta` | `runbook`, `harness` | `agent-meta` | `hybrid` | `deep` | Designs, scaffolds, evaluates, and validates agent skills according to Open Skills, layering, and taxonomy standards. |
| [strategic-thinking-5d](./strategic-thinking-5d/SKILL.md) | `deliberate` | `lens` | `architecture-strategy` | `manual` | `deep` | Applies 5D Thinking (AQAL, Kegan stages, holarchies) to diagnose systemic bottlenecks and stress-test POCs or architectures. |

---

## Persistent Rules

Always-on coding standards and cross-cutting design heuristics belong in `.agents/rules/` rather than triggerable on-demand skills (per [Gate 0 harness layering](skill-architect/references/harness-layering.md)):

- [Code Design Principles](.agents/rules/code-design-principles.md): Tie-breaker heuristics (Rule of Three/AHA, Functional Core/Imperative Shell, Immutability by Default, Locality of Behavior, Law of Demeter vs. pipelines) and anti-pattern guards distilled from the retired `programming-fundamentals` skill.

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

To scaffold a new skill with taxonomy and execution hints using `skill-architect`:

```bash
python3 skill-architect/scripts/scaffold_skill.py <skill-name> \
  --description "<third-person capability + Use when... + Do not use for...>" \
  --phase <explore|deliberate|author|critique|maintain|meta> \
  --modality <lens|spec|runbook|harness> \
  --domain <domain-slug> \
  --model-tier <fast|standard|deep|orchestrator> \
  --effort <low|medium|high> \
  --invocation <auto|manual|hybrid> \
  --dry-run
```

To validate an existing skill or audit the entire repository collision matrix:

```bash
python3 skill-architect/scripts/validate_skill.py <path-to-skill>
python3 skill-architect/scripts/validate_skill.py --all .
```
