# Skill Authoring Best Practices

Grounded in [Agent Skills Best Practices](https://agentskills.io/skill-creation/best-practices.md) and real-world execution heuristics.

---

## 1. Grounding in Real Expertise

The most common failure in skill creation is asking an LLM to generate a skill from thin air. This produces vague, generic advice ("follow error handling best practices", "ensure inputs are sanitized") that bloats token context without improving execution.

### Proven Sources of Skill Content:
- **Transcript Extraction**: Perform a task interactively with an agent. Note the exact corrections you had to make, command flags you needed, and traps encountered.
- **Incident Reports & Runbooks**: Schema quirks, edge cases, recovery steps, and production gotchas.
- **VCS & Review History**: Recurring PR review comments, past bug fixes, and non-obvious repository requirements.
- **API Specs & Schemas**: Explicit expected parameter names, payload examples, and response formats.

---

## 2. Spending the Context Budget Wisely

When a skill activates, its full `SKILL.md` body enters the context window alongside the conversation history, system prompt, and other tools.

### What to Keep vs. What to Cut
- **CUT**: Explanations of standard concepts (what JSON is, how HTTP works, basic git commands). If the model already does it right without instruction, omit it.
- **KEEP**: Repository-specific conventions, non-standard flags, environment quirks, exact file paths, domain-specific sequence requirements, and failure modes.

### The Litmus Test
For every paragraph or bullet point, ask:
> *"Would an intelligent agent make a mistake here if this instruction were absent?"*
If the answer is **no**, delete or condense it.

---

## 3. Calibrating Prescriptiveness

Match the rigidity of your instructions to the fragility of the workflow.

| Fragility Level | Approach | Style | Example |
| :--- | :--- | :--- | :--- |
| **High** (Destructive operations, strict schemas, sensitive migrations) | **Prescriptive** | Exact commands, locked flags, strict sequence. Explain why variation is forbidden. | `Run python3 scripts/migrate.py --verify --backup. Do not omit flags or change order.` |
| **Moderate** (Standard workflows, code generation, linting) | **Default with Escape Hatch** | Single opinionated default first; alternative noted briefly for specific exceptions. | `Use pdfplumber for text extraction. If scanned images require OCR, fall back to pytesseract.` |
| **Low** (Exploratory review, ideation, stylistic critique) | **Guiding Principles** | Goal-oriented checklists, qualitative criteria, explain the *why*. | `Verify authentication on all endpoints and check for race conditions in concurrent blocks.` |

### Anti-Pattern: The Endless Menu
Do not list 5 different equivalent tools or libraries as equal options (e.g. `You can use A, B, C, D, or E`). Present a single proven default.

---

## 4. Architectural Patterns for SKILL.md

### A. The "Gotchas" Section
Gotchas are high-value, environment-specific corrections that contradict reasonable assumptions:
```markdown
## Gotchas & Edge Cases
- Soft deletes are active: queries must include `WHERE deleted_at IS NULL`.
- Port 8080 is reserved for mock auth; use port 8081 for local API tests.
- IDs in the billing API are camelCase (`accountId`), but snake_case (`account_id`) in DB.
```

### B. Output Format Templates
Rather than describing desired output in prose, provide a concrete Markdown or JSON skeleton. Models pattern-match significantly better on concrete templates.

### C. Validation Loops (Plan-Validate-Execute)
For batch or multi-stage operations, enforce a self-correcting loop:
1. **Plan**: Generate an intermediate manifest (e.g. `mapping.json` or dry-run log).
2. **Validate**: Run a deterministic validation script or checklist.
3. **Correct**: If validation outputs errors, adjust the plan and re-validate.
4. **Execute**: Only execute real actions after validation succeeds.
