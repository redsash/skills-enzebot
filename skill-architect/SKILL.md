---
name: skill-architect
description: >-
  Designs, scaffolds, audits, evaluates, and validates agent skills adhering to the Open Skills specification, Antigravity layering rules, and repo taxonomy standards. Use on /skill-architect or whenever creating a new skill, auditing or refactoring an existing SKILL.md, checking cross-skill trigger collisions, engineering black-box skill scripts, or running skill evals. Do not use for writing always-on repo rules in AGENTS.md, one-off native workflows (/plan, /swarm, /goal), or standalone CLI scripts outside a skill.
taxonomy:
  phase: [meta]
  modality: [runbook, harness]
  domain: [agent-meta]
  interaction: interactive
metadata:
  model-tier: "deep"
  effort: "high"
  invocation: "hybrid"
---

# Skill Architect

Meta-skill for designing, scaffolding, auditing, and validating durable agent skills across Antigravity CLI (Gemini 4 / Claude 5.5) and Gemini CLI (Flash 3.8).

---

## Quick Reference & Bundled Tools

- **Core References** (load on demand):
  - [Harness Layering, Invocation & Model Tiers](references/harness-layering.md) — Gate 0 rubric (Skill vs. Rule vs. Native Workflow vs. Subagent vs. Hook vs. CLI), invocation modes, model tiers.
  - [Open Skills Specification & Antigravity Conventions](references/open-skills-spec.md) — Manifest schema, `.agents/skills/` discovery, progressive disclosure budgets.
  - [AI Agent Skills Taxonomy & Classification Guide](references/taxonomy-guide.md) — Faceted `phase` / `modality` / `domain` / `interaction` coordinates.
  - [Skill Authoring Best Practices](references/best-practices.md) — Guardrail-debt pruning vs. durable leverage, fragility calibration, Plan → Verify → Iterate.
  - [Description Optimization & Trigger Accuracy](references/description-optimization.md) — Third-person precision, non-triggers, collision checks, trigger evals.
  - [Script Engineering for Skills](references/script-patterns.md) — Black-box `--help` contract, stream segregation, PEP 723, resilience.
  - [Mermaid Diagram Clean Syntax & Linting Guide](references/mermaid-linting.md) — Strict syntax rules and `@probelabs/maid` validation.
  - [Evaluation & Quality Benchmarking](references/eval-methodology.md) — Comparative `with_skill` vs. `without_skill` grading.
- **Templates**:
  - [SKILL.md Starter Template](assets/skill_template.md)
  - [Evals JSON Starter Template](assets/evals_template.json)
- **Bundled Scripts (Black-Box Contract)**:
  Treat scripts in `scripts/` as black boxes: run `--help` first to inspect flags and execute them directly rather than reading script source into context (unless debugging or modifying the scripts themselves).
  - `python3 scripts/validate_skill.py --help` — Audits frontmatter, metadata tiers, taxonomy, body-line budget, black-box script contracts, orphan files, links, Mermaid syntax, and cross-skill collisions (`--all .` for repo-wide audit).
  - `python3 scripts/scaffold_skill.py --help` — Scaffolds a spec-compliant skill (supports `--dry-run`, taxonomy, metadata tiers, `--with-scripts`, `--with-references`, `--with-examples`, `--with-evals`).
  - `python3 scripts/lint_mermaid.py --help` — Lints and auto-fixes Mermaid diagrams (`--fix`).

---

## Hard Invariants

1. **Gate 0 First**: Never scaffold a skill when an Antigravity native workflow, persistent rule (`AGENTS.md` / `.agents/rules/`), subagent persona, hook, or standalone CLI script is the right layer.
2. **Durable Leverage Over Micromanagement**: Encode **goal states, hard invariants, decision trees, domain gotchas, and deterministic verification criteria**—not step-by-step reasoning scripts or mandatory scratchpad checklists.
3. **Progressive Disclosure & Context Economy**: Target ≤ 250 body lines (hard ceiling 500 lines / 5,000 tokens). Offload schemas, large templates (>40 lines), and worked examples into `references/`, `examples/`, or `assets/` linked 1 level deep.
4. **Black-Box Script Discipline**: Every bundled script must be non-interactive, document all flags via `--help`, separate `stdout` (data) from `stderr` (logs), and be invoked as a black box from `SKILL.md`.
5. **Dual-Harness Portability**: Use `.agents/skills/<name>/` and relative internal paths; keep hard exit criteria and deterministic validators intact so skills excel on both Antigravity (Gemini 4 / Claude 5.5) and Gemini CLI (Flash 3.8).

---

## Workflow 1: Creating a New Skill

### Gate 0: Should This Be a Skill?
Check the layering decision table (full rubric in [Harness Layering](references/harness-layering.md)):
- **Always-on repo standards or forbidden commands** → Persistent Rule (`AGENTS.md`, `GEMINI.md`, `.agents/rules/*.md`).
- **Generic planning, deep interview, persistence loop, multi-agent fan-out, or memory** → Native Antigravity workflow (`/plan`, `/grill-me`, `/goal`, `/boost`, `/swarm`, `/teamwork`, `run_workflow`, `/learn`, `/schedule`).
- **Context isolation or read-only sandboxing** → Subagent Persona (`invoke_subagent` / `define_subagent`); pair with a skill only if domain expertise is also needed.
- **Zero-LLM lifecycle automation** → Hook (`hooks.json`).
- **Pure deterministic transform/API wrapper needing no judgment** → Standalone CLI script or MCP server.
- **Reusable on-demand domain procedure, epistemic lens, invariant spec, or validated tool workflow** → Proceed as a **Skill**.

### Stage 1: Grounding & Boundaries
1. Extract real domain expertise from runbooks, transcripts, schemas, incident history, or concrete tool flags—never generate generic LLM advice.
2. Enforce single-purpose scope (prefer 1 `phase`; 3+ phases indicates a megaskill to decompose).
3. Decide **Invocation Posture** (`auto` vs. `manual` `/skill-name` vs. `hybrid`) and **Model/Effort Tier** (`fast|standard|deep|orchestrator`, `low|medium|high`).

### Stage 2: Scaffold & Draft Manifest
Preview with `--dry-run`, then scaffold:
```bash
python3 scripts/scaffold_skill.py <skill-name> \
  --description "<third-person capability + Use when... + Do not use for...>" \
  --phase <explore|deliberate|author|critique|maintain|meta> \
  --modality <lens|spec|runbook|harness> \
  --domain <domain-slug> \
  --model-tier <fast|standard|deep|orchestrator> \
  --effort <low|medium|high> \
  --invocation <auto|manual|hybrid> \
  --with-scripts --with-references --with-examples --with-evals --dry-run
```
- **`name`**: 1–64 chars, lowercase `a-z`, `0-9`, `-`, matching directory name.
- **`description`**: ≤ 1024 chars (target 200–550), **third-person**, states **what** it does, **when** to trigger (including `/skill-name` if `manual`/`hybrid`), and **when NOT to trigger** (`Do not use for...`) to prevent sibling collisions.
- **`metadata`**: Portable Open Skills string-to-string hints (`model-tier`, `effort`, `invocation`).

### Stage 3: Author Concise Body (`SKILL.md`)
Structure around **Plan → Discover/Use/Build Tools to Verify → Iterate**:
- **Goal & Hard Invariants**: Non-negotiable constraints and opinionated defaults with escape hatches.
- **Decision Tree / Execution Protocol**: Branch/stop conditions and concrete black-box script invocations (`run --help first`). Only use linear `- [ ]` checklists for fragile, strictly ordered destructive sequences.
- **Verification & Exit Criteria**: Deterministic checks (`--dry-run`, validators, schema checks, tests) that must pass before reporting completion.
- **Gotchas & Failure Modes**: Domain truths that contradict reasonable assumptions.
- **Output Contract**: Compact schema/template (offload >40-line examples to `examples/` or `references/`).
- **Mermaid Hygiene**: Follow [Mermaid Linting Guide](references/mermaid-linting.md) (no bare `"` in edge labels, standard arrows `<-->`/`==>`, no trailing `;` on `classDef`, quote labels with parens `Node["Label (Info)"]`).

### Stage 4: Verification Gate (Mandatory Exit Criteria)
Run the validator (including cross-skill collision checks against sibling skills) and resolve all errors and actionable warnings:
```bash
python3 scripts/validate_skill.py <path-to-skill>
# Optional: audit entire repo collision matrix
python3 scripts/validate_skill.py --all .
# Auto-fix Mermaid syntax if needed
python3 scripts/lint_mermaid.py <path-to-skill> --fix
```

---

## Workflow 2: Auditing & Upgrading an Existing Skill

1. **Automated Structural & Collision Gate**: Run `validate_skill.py <skill-dir>` (and `--all .` when touching triggers). Resolve broken links, orphan files, Mermaid errors, and sibling collisions.
2. **Guardrail-Debt Pruning**: Apply the Litmus Test (*"Would a frontier agent get this wrong without this?"*). Cut reasoning micromanagement, generic advice, and bloated inline templates; keep invariants, gotchas, decision trees, and hard exit gates.
3. **Context & Black-Box Audit**: If body > 250 lines, offload schemas/examples to `references/` or `examples/`. Ensure bundled scripts are invoked as black boxes (`--help` first) and extract recurring ad-hoc boilerplate into tested scripts.
4. **Trace-Driven Hardening**: Review failed transcripts and convert recurring mistakes into concrete `Gotchas` or deterministic script checks.

---

## Workflow 3: Optimizing Descriptions, Collisions & Invocation

1. **Collision Scan**: Run `validate_skill.py --all .` to spot taxonomy neighbors (`phase` + `domain` overlap) and high description lexical similarity. Disambiguate colliding siblings explicitly with `Do not use for...` clauses.
2. **Invocation Calibration**: Move heavy cognitive lenses, destructive workflows, or session-end tools to `invocation: "manual"` (`/skill-name`) if ambient routing causes false positives.
3. **Trigger Evals (`evals/trigger_queries.json`)**: Author ~20 realistic queries (8–10 positives + 8–10 sibling near-misses), split 60/40 Train/Validation, measure trigger rate across 3 trials, refine on Train failures only, and confirm generalization on Validation (see [Description Optimization](references/description-optimization.md)).

---

## Workflow 4: Script Engineering & Output Quality Benchmarking

- **Bundled Scripts (`scripts/`)**: Must be non-interactive (CLI flags/stdin only), expose concise `--help` with examples, separate `stdout` (machine data) from `stderr` (diagnostics), use stdlib or PEP 723 dependencies, support `--dry-run` for mutations, and be documented as **black boxes** in `SKILL.md` (see [Script Patterns](references/script-patterns.md)).
- **Quality Evals (`evals/evals.json`)**: Define 2–5 realistic test cases with objective assertions; compare `with_skill/` vs. `without_skill/` (or `old_skill/`) in an isolated workspace, grade with evidence in `grading.json`, and verify pass-rate gain justifies token cost in `benchmark.json` (see [Eval Methodology](references/eval-methodology.md)).
