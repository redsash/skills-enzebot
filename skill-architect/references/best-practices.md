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
> *"Would a frontier agent make a mistake here if this instruction were absent?"*
If the answer is **no**, delete or condense it.

### Small-Model Guardrail Debt vs. Durable Leverage
Skills written for earlier small models often accumulate procedural micromanagement that wastes tokens and degrades reasoning on Gemini 4 / Claude 5.5. Prune guardrail debt while keeping durable leverage intact (which helps **both** frontier models and Gemini 3.8 Flash):

| Prune (Guardrail Debt) | Keep (Durable Leverage) |
| :--- | :--- |
| Mandatory `- [ ] Step N` scratchpad narration on simple tasks | **Hard invariants** and domain rules that cannot be violated |
| Telling the model *how to think* or restating standard engineering hygiene | **Decision trees** (when to branch, escalate, or stop) |
| "Pushy" trigger padding to force activation | **Crisp trigger keywords + explicit non-triggers** (`Do not use for...`) |
| Inline 60-line boilerplate templates or full API docs inside `SKILL.md` | **Offloaded `references/` & `examples/`** linked 1 level deep |
| Asking the agent to read script source to figure out flags | **Black-box `scripts/`** invoked via `--help` + deterministic exit codes |
| Vague prose quality wishes ("be thorough", "double check") | **Falsifiable exit criteria** (validators, schema checks, tests, `--dry-run`) |

---

## 3. Core Agentic Workflow & Calibrating Prescriptiveness

Design skills around the durable execution loop:
1. **Plan**: Identify target invariants, inputs, and verification criteria before editing or executing.
2. **Use / Adapt / Build Tools to Verify**: Run bundled black-box scripts (`--help` first) or existing repo tools to ground decisions; if no deterministic check exists for a recurring failure mode, build a lightweight verifier script.
3. **Iterate**: Inspect validator/test output, fix all reported defects, and re-verify until hard exit criteria pass.

Match instruction rigidity to the fragility of the workflow:

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

### B. Output Format Contracts
Rather than describing desired output in prose, provide a concrete Markdown or JSON skeleton. Models pattern-match significantly better on concrete schemas. Keep skeletons concise (under ~30–40 lines) in `SKILL.md`; move larger schemas or multi-variant examples into `references/` or `examples/`.

### C. Black-Box Script Invocation
When a skill bundles executables in `scripts/`, explicitly instruct the agent to run `scripts/<tool> --help` first and execute it directly rather than reading script source code into context (unless debugging or modifying the script).

### D. Validation Loops (Plan-Validate-Execute)
For batch, stateful, or destructive operations, enforce a self-correcting exit gate:
1. **Plan**: Generate an intermediate manifest (e.g. `mapping.json` or dry-run log).
2. **Validate**: Run a deterministic validation script or invariant check.
3. **Correct**: If validation outputs errors, fix all defects and re-validate.
4. **Execute**: Only execute real actions after validation succeeds.
