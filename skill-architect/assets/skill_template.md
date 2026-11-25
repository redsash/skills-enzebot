---
name: [skill-name]
description: >-
  [Third-person summary of what this skill accomplishes. Use when <specific user intent,
  artifacts, keywords, or /skill-name>. Do not use for <explicit near-miss boundaries or
  native workflows handled elsewhere>. Target 200-550 chars; max 1024.]
taxonomy:
  phase: [author]
  modality: [runbook]
  domain: [software-engineering]
  interaction: autonomous
metadata:
  model-tier: "standard"
  effort: "medium"
  invocation: "auto"
---

# [Skill Title]

[1-2 sentence orientation: exact goal state and operational scope.]

---

## Quick Reference & Bundled Resources

- **References** *(read on demand)*: [Deep-Dive Guide](references/REFERENCE.md)
- **Examples** *(read on demand)*: [Worked Example](examples/example.md)
- **Bundled Scripts (Black-Box)**: Treat `scripts/` as black boxes—run `--help` first to inspect flags and execute directly rather than reading script source into context unless debugging or modifying the script.
  - `python3 scripts/run.py --help`

---

## Goal & Hard Invariants

- **Goal**: [Observable end-state that defines success.]
- **Invariant 1**: [Non-negotiable domain rule or constraint.]
- **Invariant 2**: [Opinionated default + explicit escape hatch.]
- **Scope Boundary**: Do not use this skill for [near-miss task]; use [sibling skill / `AGENTS.md` / native `/plan` or `/swarm`] instead.

---

## Decision Tree & Execution Protocol

Follow **Plan → Use/Verify with Tools → Iterate**:

1. **Inspect & Plan**: Gather concrete inputs/ground truth and determine whether existing constraints or edge cases apply.
   - *If [branch condition A]* → [take path A / consult `references/REFERENCE.md`].
   - *If [branch condition B]* → [stop and ask user / fall back to alternative].
2. **Execute**: Invoke bundled black-box scripts or domain procedures:
   ```bash
   python3 scripts/run.py --dry-run --input "$INPUT_FILE"
   ```
3. **Iterate**: If validation reports errors, fix all reported defects and re-run until clean.

---

## Verification & Exit Criteria

Do not report completion until every gate passes:
- [ ] Deterministic check / validator exits `0` (`python3 scripts/run.py --verify ...`).
- [ ] All hard invariants above are satisfied with concrete evidence.
- [ ] Output conforms strictly to the Output Contract below.

---

## Gotchas & Failure Modes

- **[Gotcha 1]**: [Non-obvious environment, API, or data quirk that contradicts reasonable assumptions.]
- **[Gotcha 2]**: [Common failure signature and exact remediation.]

---

## Output Contract

*(Keep inline schemas under ~40 lines; offload larger templates to `examples/` or `references/`.)*

```markdown
# [Compact output skeleton]
```
