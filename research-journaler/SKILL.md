---
name: research-journaler
description: >-
  Initializes, structures, and logs reproducible research sessions into chronological journal entries (entries/YYYY-MM/YYYY-MM-DD_topic-slug/). Use when starting a research inquiry, logging experimental findings, recording prompt iterations, or wrapping up research milestones across software engineering, academic, or data analysis domains.
compatibility: Requires Python 3.8+
---

# Research Journaler

A repository-enforced research journal engine designed to prevent context drift and capture reproducible research trails across multi-agent workflows (Antigravity CLI, Gemini CLI, Gemini Spark).

---

## When to Use This Skill
- **Research Kickoff**: Initializing a new research topic, question, or architectural spike.
- **Milestone & Finding Logging**: Recording iterations, hypotheses, tested commands, and validated outcomes in `logs.md`.
- **Prompt & Model Auditing**: Tracking prompt variations, system parameters, and model outputs in `prompts.json`.
- **Session Wrapping**: Storing generated artifacts in `outputs/`, raw references in `sources/`, and synthesizing final conclusions.
- **Do not use for**: Ephemeral, one-off file edits that do not require historical documentation or multi-turn traceability.

---

## Repository Architecture

```text
research-journal/
├── .gitignore               # Ignores heavy payloads (outputs/*.json, sources/*.pdf)
├── README.md
├── docs/
│   └── templates/           # Blueprints for log files and prompt records
└── entries/
    ├── YYYY-MM/
    │   └── YYYY-MM-DD_topic-slug/
    │       ├── logs.md      # Analytical narrative, hypotheses, and conclusions
    │       ├── prompts.json # Machine-readable prompt catalog and system flags
    │       ├── outputs/     # Generated tables, flamegraphs, JSON, or scripts
    │       └── sources/     # Upstream specs, downloaded whitepapers, or RFCs
    └── archives/            # Completed research epics
```

See [Architecture & Multi-Agent Reference](references/REFERENCE.md) for global and workspace-level configuration across Antigravity and Gemini harnesses.

---

## Workflow / Procedure

Progress:
- [ ] Step 1: Ensure repository structure and templates exist
- [ ] Step 2: Scaffold the chronological entry directory
- [ ] Step 3: Record the core hypothesis and investigation baseline in `logs.md`
- [ ] Step 4: Log prompt iterations and system parameters to `prompts.json`
- [ ] Step 5: Place artifacts in `outputs/` and raw files in `sources/`
- [ ] Step 6: Synthesize final takeaways and update topic status

### Step 1: Initialize Workspace (First-Time Only)
If the repository has not been initialized with journal structures:
```bash
python3 scripts/log_research.py init-repo
```
This generates `docs/templates/`, `.gitignore`, and base directories without overwriting existing files.

### Step 2: Scaffold a New Research Entry
When beginning a new research inquiry, compute the chronological target and scaffold files:
```bash
python3 scripts/log_research.py new-entry \
  --topic "ebpf-tracing" \
  --category "software-engineering" \
  --title "Linux Kernel eBPF kprobes Latency Tracing"
```

**Supported Categories**:
- `software-engineering`: Automatically captures git branch/commit, runtime versions, and virtualenv state.
- `data-analysis`: Automatically surveys installed scientific packages (pandas, polars, numpy).
- `academic-research`: Initializes literature and hypothesis tracking sections.
- `general`: Standard multi-turn research entry.

### Step 3: Record Hypothesis & Iterations in `logs.md`
Open the generated `logs.md` (instantiated from [Research Log Template](assets/templates/research-log-template.md)):
1. Fill in **1. Objective & Hypothesis** before testing commands.
2. Under **3. Investigation Log & Iterations**, log each action, observation, and interim insight as experiments run.
3. Keep prose concise, focusing on what was learned and what surprised you.

### Step 4: Track Prompt Iterations in `prompts.json`
Whenever significant prompts, system configurations, or model responses are tested:
```bash
python3 scripts/log_research.py add-prompt \
  --topic "ebpf-tracing" \
  --prompt "Analyze kernel probe latency using bpftrace" \
  --model "gemini-3.8-flash" \
  --response-summary "Generated working probe script; verified kernel symbol availability"
```
The helper script updates `prompts.json` atomically and increments iteration counts safely.

### Step 5: Isolate Artifacts & Sources
- Place generated code, logs, and benchmark reports into `entries/YYYY-MM/YYYY-MM-DD_topic-slug/outputs/`.
- Place downloaded PDFs, vendor specs, or data samples into `entries/YYYY-MM/YYYY-MM-DD_topic-slug/sources/`.

### Step 6: Synthesize Findings
Conclude the session in `logs.md`:
- Document **Validated Insights** vs. **Disproved Assumptions**.
- Set the entry status to `Concluded` or `Active`.

---

## Gotchas & Best Practices

- **The Overwrite Trap**: Never clobber an existing `logs.md` or `prompts.json` when resuming research on an existing topic. The `log_research.py` script guards against file overwrites by default.
- **The Context Dump Anti-Pattern**: Do not paste multi-megabyte log files into `logs.md`. Save raw outputs into `outputs/` and write analytical summaries in `logs.md`.
- **Git Hygiene**: Heavy outputs (`*.pdf`, large `*.csv`, `*.parquet`) are excluded by `.gitignore`. Keep git tracking focused on markdown analyses, schemas, and lightweight scripts.
- **Credential Hygiene**: Never log API keys, session tokens, or `.env` files into `prompts.json`.
