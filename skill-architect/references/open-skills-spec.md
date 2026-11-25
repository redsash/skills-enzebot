# Open Skills Specification & Antigravity Conventions

This reference summarizes the format requirements, structural rules, and platform conventions for Agent Skills based on the [Open Skills Specification](https://agentskills.io/specification.md) and [Antigravity Documentation](https://antigravity.google/docs/skills.md).

---

## 1. Directory Structure

A skill is a self-contained directory containing at minimum a `SKILL.md` file:

```text
<skill-name>/
├── SKILL.md          # Required: Manifest & concise operational guide
├── scripts/          # Optional: Black-box executable code & validators (--help)
├── references/       # Optional: Detailed domain docs, schemas & deep-dive guides
├── examples/         # Optional: Concrete worked examples & sample inputs/outputs
├── assets/           # Optional: Static resources & reusable starter templates
└── evals/            # Optional: Evaluation suites (evals.json, trigger_queries.json)
```

### Antigravity & Dual-Harness Discovery Locations
Antigravity resolves skills in precedence order (highest to lowest):
1. **Workspace Hierarchical Walk-Up**: Walks from CWD up to the repo root (`.git`) loading `.agents/skills/<skill-name>/SKILL.md` (and `.agent/`, `_agents/`, `_agent/`), plus `.agents/skills.json`.
2. **Declared Workspace Config**: Explicitly registered in `skills.json` / `plugins.json`.
3. **User Global**: `~/.gemini/config/skills/<skill-name>/`
4. **Built-in Bundled**: System-provided skills mounted by the application runtime.

*Dual-compatibility note*: Authoring workspace skills under `.agents/skills/<skill-name>/` with relative internal paths (`scripts/...`, `references/...`, `examples/...`) ensures portable discovery across both Antigravity CLI and Gemini CLI.

---

## 2. Manifest (`SKILL.md`) Format

The `SKILL.md` file must start with valid YAML frontmatter between `---` delimiters, followed by markdown instructions.

### Frontmatter Schema

| Field | Type | Required | Constraints | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `name` | string | **Yes** | 1–64 chars; lowercase `a-z`, `0-9`, and `-`. No leading/trailing hyphen. No consecutive hyphens (`--`). **Must match the parent directory name**. | Unique identifier used for invocation and indexing. |
| `description` | string | **Yes** | 1–1024 chars; non-empty. Plain text or folded block scalar (`>-`). | Explains what the skill does and when the agent should activate it. Primary trigger mechanism. |
| `license` | string | No | Short identifier (e.g. `Apache-2.0`, `MIT`, `Proprietary`) or pointer to bundled license. | Licensing terms. |
| `compatibility` | string | No | Max 500 characters. | Runtime/system prerequisites (e.g. `Requires Python 3.10+, docker, jq`). |
| `taxonomy` | map | Recommended | Contains `phase`, `modality`, `domain` (and optional `interaction`). See [Taxonomy Guide](taxonomy-guide.md). | Multi-dimensional faceted classification for routing and cataloging. |
| `metadata` | map[str, str] | No | String-to-string key-value mapping. Recommended optional keys: `model-tier` (`fast\|standard\|deep\|orchestrator`), `effort` (`low\|medium\|high`), `invocation` (`auto\|manual\|hybrid`). | Portable execution hints, invocation posture, and custom extensions without breaking strict Open Skills parsers. |
| `allowed-tools` | string | No | Space-separated list of approved tool patterns (e.g. `Bash(git:*) Read`). | Tool sandboxing hints (experimental). |

### Frontmatter Validation Checklist
- [ ] `name` is identical to folder name (e.g. folder `data-cleaner` → `name: data-cleaner`).
- [ ] `name` has no uppercase letters, underscores, or spaces.
- [ ] `description` is ≤ 1024 characters (aim for 200–550 characters for startup context economy).
- [ ] `description` uses crisp **third-person** phrasing (`"Designs..."`, `"Audits..."`), states explicit trigger conditions (`"Use when..."`), and includes explicit non-triggers (`"Do not use for..."`) whenever near-miss skills exist.
- [ ] Optional `metadata` execution hints (`model-tier`, `effort`, `invocation`) use valid enum values as strings.

---

## 3. Progressive Disclosure Architecture

Skills must be authored for progressive disclosure to preserve the model's context budget:

1. **Discovery Tier (~60–120 tokens)**: At startup, only `name` and `description` are loaded into agent context.
2. **Execution Tier (Target ≤ 250 body lines; hard ceiling 500 lines / 5,000 tokens)**: When triggered, the agent loads `SKILL.md`. Keep it focused on goals, invariants, decision trees, black-box script entrypoints, gotchas, and exit criteria.
3. **On-Demand Tier**: Detailed manuals, large tables, schemas, and worked examples (>40 lines) reside in `references/`, `examples/`, or `assets/` and are read only when needed.

### Relative Linking Rules & Portability
- Reference bundled files using paths relative to the skill root:
  - `[API Guide](references/api-guide.md)`
  - `[Worked Example](examples/sample-report.md)`
  - `python3 scripts/validate.py --help`
  - `cat assets/template.json`
- Keep reference chains shallow (1 level deep from `SKILL.md`). Do not leave orphaned files in `references/`, `examples/`, `assets/`, or `scripts/` unlinked from `SKILL.md`.
- **Portability & Eval Integrity**: Never embed user-specific absolute home paths in skill docs or scripts (use `~/` or environment variables), and always reference bundled scripts via relative `scripts/...` paths rather than repo-root prefixes. Keep `evals/trigger_queries.json` as a top-level JSON array of `{"query": ..., "should_trigger": ...}` objects and ensure every path listed in `evals/evals.json` `files[]` exists inside the skill directory.
