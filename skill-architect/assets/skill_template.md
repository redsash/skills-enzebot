---
name: [skill-name]
description: >-
  [Imperative description of what the skill does and exact conditions when the agent should activate it.
  State user intent, keywords, file formats, and boundary conditions. Max 1024 characters.]
---

# [Skill Title]

[Brief 1-2 sentence orientation describing the core purpose and expected end-state.]

## When to Use This Skill
- [Trigger condition 1 / user task]
- [Trigger condition 2 / input file types]
- **Do not use for**: [Explicit near-miss boundaries handled elsewhere]

---

## Workflow / Procedure

Progress:
- [ ] Step 1: [Analyze / Prepare input]
- [ ] Step 2: [Execute main operation / Run script]
- [ ] Step 3: [Validate output against constraints]

### Step 1: [Preparation / Inspection]
[Concise instructions. Specify defaults, not open menus.]

### Step 2: [Execution]
[Clear commands or scripts. Reference relative paths e.g. `scripts/run.py`.]

```bash
python3 scripts/run.py --input "$INPUT_FILE"
```

### Step 3: [Validation]
[Validation loop instructions: how the agent verifies its work before proceeding.]

---

## Gotchas & Failure Modes
- **[Gotcha 1]**: [Non-obvious environment, API, or data quirk that defies reasonable assumptions.]
- **[Gotcha 2]**: [Common edge case or required flag.]

---

## Output Template / Standard Format
[Provide concrete markdown or JSON skeleton to enforce output structure.]
