# Research Journal Architecture & Multi-Agent Reference

This reference outlines the repository standards, multi-agent integration patterns, and lifecycle conventions for research journal workspaces.

---

## 1. Multi-Agent Installation & Setup

To make the `research-journaler` and companion skills (like `deeply-investigate`) available across different local agent harnesses:

### A. Antigravity CLI (Workspace-Level)
In your research repository root:
```bash
mkdir -p .agents/skills
# Copy or symlink the skill directory
cp -r /path/to/skills-enzebot/research-journaler .agents/skills/
cp -r /path/to/skills-enzebot/deeply-investigate .agents/skills/
```
Antigravity automatically discovers skills inside `.agents/skills/` without manual configuration.

### B. Gemini CLI (Global or User Configuration)
To make the skill globally available across all Gemini CLI invocations:
```bash
mkdir -p ~/.gemini/config/skills
cp -r /path/to/skills-enzebot/research-journaler ~/.gemini/config/skills/
```

### C. Gemini Spark & Interactive IDE Sessions
For environments that read project rules, reference the journal commands in `AGENTS.md` or `GEMINI.md` at the project root:
```markdown
## Research Journal Protocol
- At the start of a research topic: Run `python3 .agents/skills/research-journaler/scripts/log_research.py new-entry --topic <slug> --category <cat>`
- Record key prompts and hypotheses to `prompts.json` and `logs.md`.
```

---

## 2. Directory Lifecycle & Clean Boundaries

```text
entries/
├── 2026-09/
│   └── 2026-09-26_ebpf-tracing/
│       ├── logs.md          # Human-readable synthesis, hypotheses, iterations
│       ├── prompts.json     # Structural execution catalog (flags, models, prompts)
│       ├── outputs/         # Generated charts, parsed JSON, extracted CSVs
│       └── sources/         # Base papers, raw whitepapers, RFC markdown
└── archives/
    └── 2026-Q3-networking/ # Consolidated historical milestones
```

### Storage Boundaries
- **`logs.md`**: Kept clean and high-signal. Contains analysis, core questions, observations, and takeaways. Avoid pasting 500-line JSON dumps here.
- **`outputs/`**: Store artifacts generated during the session (e.g. `outputs/benchmark.json`, `outputs/flamegraph.svg`).
- **`sources/`**: Store immutable source material consulted (e.g. `sources/rfc9000.txt`, `sources/whitepaper.pdf`).
- **`.gitignore`**: By default ignores heavy binary/data payloads in `outputs/` and `sources/` while preserving the research narrative in version control.

---

## 3. Environment Context & Secret Scrubbing

When `log_research.py` captures environment metadata:
- Git branch and short commit hash are recorded.
- Python and runtime versions are saved.
- **Secret Scrubbing**: Never write `.env` variables, API keys, bearer tokens, or password strings into `prompts.json` or `logs.md`. The helper script explicitly avoids dumping `os.environ` to preserve credential security.
