---
name: skill-architect
description: >-
  Designs, scaffolds, evaluates, and refines agent skills according to the Open Skills specification and Antigravity guidelines. Use this skill whenever creating a new skill, updating or auditing an existing SKILL.md, optimizing trigger descriptions, engineering bundled scripts, or running evals and benchmarks.
---

# Skill Architect

The meta-skill for creating, auditing, optimizing, and evaluating agent skills in this workspace and across Antigravity ecosystems.

---

## Quick Reference & Bundled Tools

- **Core References**:
  - [Open Skills Specification & Antigravity Conventions](references/open-skills-spec.md)
  - [Skill Authoring Best Practices](references/best-practices.md)
  - [Description Optimization & Trigger Accuracy](references/description-optimization.md)
  - [Script Engineering for Skills](references/script-patterns.md)
  - [Evaluation & Quality Benchmarking](references/eval-methodology.md)
- **Bundled Utilities**:
  - `python3 skill-architect/scripts/validate_skill.py <path-to-skill>`: Audits frontmatter, directory naming, line counts, and relative link validity.
  - `python3 skill-architect/scripts/scaffold_skill.py <skill-name>`: Scaffolds a spec-compliant skill structure with optional scripts, references, and evals.
- **Templates**:
  - [SKILL.md Starter Template](assets/skill_template.md)
  - [Evals JSON Starter Template](assets/evals_template.json)
- **Upstream Standards**:
  - [Agent Skills Specification](https://agentskills.io/specification.md)
  - [Antigravity Skills Documentation](https://antigravity.google/docs/skills.md)

---

## Workflow 1: Scaffolding a New Skill

When asked to create a new skill from scratch, follow this 5-stage procedure:

### Phase 1: Context Gathering & Grounding
1. **Extract Domain Expertise**:
   - Identify the real runbooks, incident reports, code conventions, or tool workflows the skill must encode.
   - Do not ask an LLM to generate generic advice; ground instructions in exact commands, API schemas, flags, and repository paths.
2. **Define Boundaries**:
   - Determine what the skill handles vs. what is out of scope.
   - Ensure the skill addresses a single, coherent unit of work.

### Phase 2: Directory Scaffolding & Naming
1. Determine the canonical `skill-name`:
   - Must be 1–64 characters, lowercase `a-z`, `0-9`, and `-`. No leading/trailing hyphens, no `--`.
2. Run the scaffolding utility:
   ```bash
   python3 skill-architect/scripts/scaffold_skill.py <skill-name> \
     --description "<imperative description under 1024 chars>" \
     --with-scripts --with-references --with-evals
   ```
   *(Omit `--with-scripts` or `--with-references` if the skill is purely procedural and fits within a concise SKILL.md).*

### Phase 3: Drafting the Frontmatter
- **`name`**: Must strictly match the directory name.
- **`description`**: Imperative, pushy, focused on user intent:
  - Must state **what** the skill accomplishes and **when** the agent should activate it.
  - Include synonyms, file extensions, and edge situations (e.g. *"even if the user does not explicitly say 'CSV'"*).
  - Must be strictly $\le 1024$ characters.
- **Optional fields**: Specify `compatibility` only if external packages/tools are required (max 500 chars).

### Phase 4: Authoring the Body (`SKILL.md`)
Keep the body under 500 lines / 5,000 tokens by adhering to progressive disclosure:
1. **Progress Checklist**: Use markdown task lists `- [ ] Step N` for multi-step workflows.
2. **Actionable Procedures over General Declarations**:
   - Provide concrete commands and exact script invocations with relative paths (`scripts/my_script.py`).
   - Specify opinionated defaults with escape hatches rather than open menus.
3. **The "Gotchas" Section**:
   - Detail domain-specific facts that contradict reasonable assumptions (soft deletes, port collisions, casing mismatches).
4. **Validation Loops (Plan-Validate-Execute)**:
   - For stateful or destructive actions, instruct the agent to generate a plan, run a validator, and fix errors before execution.
5. **Output Format**:
   - Provide concrete structural markdown or JSON templates.

### Phase 5: Verification
Run the validation script and resolve any errors or warnings:
```bash
python3 skill-architect/scripts/validate_skill.py <path-to-skill>
```

---

## Workflow 2: Auditing & Refining an Existing Skill

When improving an existing skill or troubleshooting performance:

1. **Context Budget Audit**:
   - Run `validate_skill.py`. If `SKILL.md` exceeds 500 lines, extract detailed tables or manual documentation into `references/*.md`.
   - Apply the Litmus Test: *"Would the agent get this wrong without this instruction?"* Cut generic programming advice the model already knows.
2. **Trace Analysis & Failure Review**:
   - Inspect execution transcripts from previous runs. Identify where the agent wasted steps, pursued incorrect approaches, or misinterpreted instructions.
   - Clarify ambiguous steps; explain the *why* rather than just adding rigid prohibitions.
3. **Extract Bundled Scripts**:
   - If the agent repeatedly re-writes the same parsing or formatting helper on every run, extract that logic into a tested script in `scripts/`.
4. **Harden Gotchas**:
   - Every time an agent makes a real error that required human steering, document the exact failure mode in the skill's `Gotchas` section.

---

## Workflow 3: Optimizing Triggers & Descriptions

When a skill either fails to activate or activates on irrelevant prompts:

1. **Create Trigger Eval Queries**:
   - Author ~20 realistic queries (8–10 positives, 8–10 negative near-misses) in `evals/trigger_queries.json`.
   - Include casual prompts, abbreviations, typos, and requests where the skill's domain is not explicitly named.
   - Include near-misses (e.g., CSV ETL vs CSV analysis).
2. **Split Train & Validation Sets**:
   - 60% Train, 40% Validation with equal positive/negative distribution.
3. **Execute & Calculate Trigger Rates**:
   - Run each query 3 times across your agent harness to measure `trigger_rate`.
4. **Iterative Refinement**:
   - Diagnose Train set failures.
   - For false negatives: broaden trigger terms and emphasize user intent.
   - For false positives: add explicit boundary constraints ("Do not use when...").
   - Test against the Validation set to confirm generalization without overfitting.

---

## Workflow 4: Script Engineering for Skills

When writing scripts in `scripts/`:

1. **Non-Interactive by Design**:
   - Never use interactive prompts (`input()`, confirmation prompts).
   - Require arguments via CLI flags or stdin.
2. **Document via `--help`**:
   - Ensure the script outputs clean, concise usage information with examples on `--help`.
3. **Stream Separation**:
   - `stdout`: Pure structured data (JSON, CSV, markdown tables).
   - `stderr`: Progress messages, warnings, and diagnostic traces.
4. **Self-Contained Dependencies**:
   - For Python: use standard library where possible, or declare PEP 723 inline dependencies.
   - For Shell: use portable bash commands and set `-euo pipefail`.
5. **Idempotence & Safety**:
   - Support `--dry-run` for state-modifying actions.

---

## Workflow 5: Output Quality Evaluation & Benchmarking

When testing whether a skill reliably achieves task goals:

1. **Define Test Cases (`evals/evals.json`)**:
   - Write 2–3 representative prompts with sample input files and expected outputs.
2. **Run Comparative Baselines**:
   - Run test cases under `iteration-1/` in an isolated eval workspace:
     - `with_skill/`: Agent equipped with candidate skill.
     - `without_skill/` (or `old_skill/`): Baseline comparison.
3. **Grade Objective Assertions**:
   - Verify assertions (e.g. file exists, valid schema, no NaN values).
   - Record pass/fail with concrete evidence in `grading.json`.
4. **Aggregate & Compare**:
   - Compute pass rate delta, runtime delta, and token usage delta in `benchmark.json`.
   - Verify that quality gains justify the token cost.
