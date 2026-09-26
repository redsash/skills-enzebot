# Open Skills Specification & Antigravity Conventions

This reference summarizes the format requirements, structural rules, and platform conventions for Agent Skills based on the [Open Skills Specification](https://agentskills.io/specification.md) and [Antigravity Documentation](https://antigravity.google/docs/skills.md).

---

## 1. Directory Structure

A skill is a self-contained directory containing at minimum a `SKILL.md` file:

```text
<skill-name>/
├── SKILL.md          # Required: Manifest & procedural instructions
├── scripts/          # Optional: Executable code and automation tools
├── references/       # Optional: Detailed domain documentation & deep-dive guides
├── assets/           # Optional: Static resources, templates, and schemas
└── evals/            # Optional: Evaluation suites and test cases (evals.json)
```

### Antigravity Discovery Locations
Antigravity automatically resolves skills according to precedence:
1. **Workspace Root**: `.agents/skills/<skill-name>/` (or `.agent/skills/<skill-name>/`)
2. **Declared Config**: Explicitly registered in `skills.json`
3. **User Global**: `~/.gemini/config/skills/<skill-name>/`
4. **Built-in Bundled**: System-provided skills mounted by application runtime

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
| `metadata` | map[str, str] | No | String key-value mapping. | Custom extensions, author info, versioning. |
| `allowed-tools` | string | No | Space-separated list of approved tool patterns (e.g. `Bash(git:*) Read`). | Tool sandboxing hints (experimental). |

### Frontmatter Validation Checklist
- [ ] `name` is identical to folder name (e.g. folder `data-cleaner` -> `name: data-cleaner`).
- [ ] `name` has no uppercase letters, underscores, or spaces.
- [ ] `description` is under 1024 characters.
- [ ] `description` uses third-person or imperative phrasing ("Use this skill when...", "Scaffolds and audits...").

---

## 3. Progressive Disclosure Architecture

Skills must be authored for progressive disclosure to preserve the model's context budget:

1. **Discovery Tier (~100 tokens)**: At startup, only `name` and `description` are loaded into agent context.
2. **Execution Tier (<5,000 tokens / <500 lines)**: When triggered, the agent loads `SKILL.md`. This should contain immediate, step-by-step procedures, defaults, checklists, and gotchas.
3. **On-Demand Tier**: Detailed manuals, large reference tables, or bulky templates reside in `references/` or `assets/` and are fetched only when specific criteria are met.

### Relative Linking Rules
- Reference bundled files using paths relative to the skill root:
  - `[API Guide](references/api-guide.md)`
  - `python3 scripts/validate.py`
  - `cat assets/template.json`
- Keep reference chains shallow (1 level deep from `SKILL.md`). Do not create deeply nested link trees.
