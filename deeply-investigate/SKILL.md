---
name: deeply-investigate
description: >-
  Investigates complex technical topics, nascent architectures, external APIs, or local documents against canonical primary sources. Use on /deeply-investigate or when tasked with in-depth primary-source research, API verification, or compiling a technical dossier. Do not use for quick syntax lookups, repo-local lab notebooks (research-journaler), or retrospective cross-project session logging (engineering-log).
taxonomy:
  phase: [explore]
  modality: [runbook]
  domain: [software-engineering, architecture-strategy]
  interaction: autonomous
metadata:
  model-tier: "orchestrator"
  effort: "high"
  invocation: "hybrid"
---

# Deeply Investigate

Conducts deep-dive investigations of technical domains, APIs, protocols, and architectural trade-offs against canonical primary sources. Compiles findings into a structured, progressive-disclosure Markdown dossier designed for rapid executive understanding and multi-turn iterative deep dives.

> [!TIP]
> Antigravity's built-in `research` subagent runs in an **offline read-only sandbox**. Use it to ingest local repositories, PDFs, schemas, and logs without bloating main context; use the primary agent's web search or network-capable tools when fetching external RFCs, vendor docs, or upstream repositories.

---

## When to Use This Skill
- Researching an unfamiliar protocol, architectural pattern, or emerging technology.
- Ingesting heavy technical material: RFCs, whitepapers, multi-page PDFs, API specs, or raw data dumps.
- Resolving technical ambiguity or verifying external claims against upstream source code before implementing changes.
- **Do not use for**: Quick one-line syntax lookups or simple tool invocations that do not warrant a persistent research artifact.

---

## Inputs Handled
- **Local Artifacts**: PDFs, Markdown notes, architecture diagrams, schemas, spreadsheets/CSVs, or local repository source files.
- **Canonical External References**: Upstream git repositories, official vendor documentation, specification RFCs, API reference endpoints, or creator engineering blogs.
- **Nascent Seeds**: High-level problem statements, vague feature requests, or novel conceptual seeds where technical vocabulary must first be bridged.

---

## Workflow / Procedure

### Step 1: Ingest Seed Inputs & Bridge Vocabulary
1. Read user-provided local artifacts, URLs, and seeds first (extract PDFs/CSVs cleanly via CLI tools rather than dumping raw bytes).
2. Translate colloquial phrasing into canonical specification terms, surface hidden prerequisites, and frame critical architect questions (failure modes, concurrency limits, state persistence, version bounds).

### Step 2: Canonical Primary Source Verification
- **Prioritize Tier-1 Sources**:
  1. Upstream source code (GitHub/GitLab repos, commit history, issue trackers, PR discussions).
  2. Formal specifications and standards (RFCs, W3C, ISO, OpenAPI/AsyncAPI specs).
  3. Official vendor/maintainer documentation and engineering postmortems.
- **Filter Out Secondary Noise**:
  - Bypass content farms, aggregate tutorials, medium posts, and AI-generated summary blogs.
  - Trace second-hand claims back to the implementation or specification that owns the behavior.
- **Verify Version Alignment**:
  - Check the exact version of the runtime, library, or protocol. Guard against deprecated APIs or documentation drift.

### Step 3: File Placement & Naming
Conform to existing repository research doc conventions (`docs/research/`, `notes/`, `architecture/decisions/`), or default to `docs/research/YYYY-MM-DD-<topic-slug>.md`.

### Step 4: Deliver Executive Summary & Next Vectors
Print the generated dossier's path, give a concise 2–3 paragraph executive brief in chat, and propose 3 concrete next-turn exploration prompts.

---

## Dossier Output Contract

Structure dossiers for progressive disclosure (full skeleton in [Dossier Template](examples/dossier-template.md)):

```markdown
# [Topic / System Name]: Technical Dossier
**Date:** YYYY-MM-DD | **Status:** Completed | Iterative | **Seeds:** [...]

## 1. Executive Brief & Mental Model
## 2. Core Mechanics & Verified Findings
## 3. Gap Analysis & Resolved Prerequisites
## 4. Primary Source Reference Index   (table: Source | Authority | Anchor | Takeaway)
## 5. Next-Turn Exploration Vectors    (3-5 follow-up prompts)
```

---

## Gotchas & Failure Modes

- **The Secondary Source Echo Chamber**: Third-party tutorials frequently repeat outdated or incorrect assumptions. When behavior seems counter-intuitive, cross-reference the actual codebase or issue tracker.
- **Version Drift**: Documentation for version $N$ often differs fundamentally from version $N-1$ or $N+1$. Always explicitly note the software version being investigated.
- **The Context Dump**: Avoid pasting raw 20-page web scrapes into the dossier. Synthesize, distill, and present findings with clear headings and code snippets.
- **Marketing Bias**: Vendor documentation frequently obscures trade-offs. Look for GitHub issues, postmortems, and performance benchmarks to surface genuine limitations.
