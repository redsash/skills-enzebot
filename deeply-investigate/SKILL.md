---
name: deeply-investigate
description: >-
  Investigates complex technical topics, nascent architectural concepts, external APIs, or local documents (PDFs, specifications, data) against canonical primary sources. Use when tasked with conducting in-depth research, architectural discovery, API verification, or compiling a progressive-disclosure technical dossier, especially when delegating heavy exploration to a background subagent.
---

# Deeply Investigate

Conducts deep-dive investigations of technical domains, APIs, protocols, and architectural trade-offs against canonical primary sources. Compiles findings into a structured, progressive-disclosure Markdown dossier designed for rapid executive understanding and multi-turn iterative deep dives.

> [!TIP]
> When executing in an environment that supports subagents, delegate the investigation to a background `research` subagent (e.g. via `invoke_subagent`). This prevents high-volume document fetching, web scraping, and raw dumps from overwhelming the primary conversation context.

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

Progress:
- [ ] Step 1: Ingest seed inputs and extract local context
- [ ] Step 2: Deconstruct domain concepts and identify knowledge gaps
- [ ] Step 3: Verify claims strictly against canonical primary sources
- [ ] Step 4: Write the progressive-disclosure dossier to disk
- [ ] Step 5: Report findings with executive summary and follow-up vectors

### Step 1: Ingest Seed Inputs
1. Inspect and read all user-provided local documents, URLs, and seeds first.
2. For local PDFs or structured data, use available CLI tools (`pdftotext`, Python parsers) to extract clean text.
3. Establish the research baseline: What problem is the user solving? What constraints are known?

### Step 2: Frame Concepts & Bridge Knowledge Gaps
If the user's inquiry is open-ended or uses informal phrasing:
- **Map to canonical vocabulary**: Translate colloquial terms to formal industry terminology and official specification concepts.
- **Anticipate unasked expert questions**: Formulate the critical questions an architect in this domain would ask: failure modes, concurrency limits, state persistence, backward compatibility, performance boundaries.
- **Expose hidden assumptions**: Uncover prerequisites and dependencies that the initial seed took for granted.

### Step 3: Canonical Primary Source Verification
- **Prioritize Tier-1 Sources**:
  1. Upstream source code (GitHub/GitLab repos, commit history, issue trackers, PR discussions).
  2. Formal specifications and standards (RFCs, W3C, ISO, OpenAPI/AsyncAPI specs).
  3. Official vendor/maintainer documentation and engineering postmortems.
- **Filter Out Secondary Noise**:
  - Bypass content farms, aggregate tutorials, medium posts, and AI-generated summary blogs.
  - Trace second-hand claims back to the implementation or specification that owns the behavior.
- **Verify Version Alignment**:
  - Check the exact version of the runtime, library, or protocol. Guard against deprecated APIs or documentation drift.

### Step 4: File Placement & Naming
Check existing repository conventions for research or documentation notes (e.g., `docs/research/`, `notes/`, `architecture/decisions/`).
- If a convention exists, conform to its structure.
- If no convention exists, default to:
  `docs/research/YYYY-MM-DD-<topic-slug>.md`

### Step 5: Deliver Executive Summary & Next Vectors
Upon writing the dossier:
- Print the exact relative path of the generated markdown file.
- Provide a concise 2–3 paragraph executive brief in the main conversation.
- Present 3 concrete next-turn exploration prompts for continued work.

---

## Dossier Output Specification

The generated markdown dossier must follow this structure:

````markdown
# [Topic / System Name]: Technical Dossier

**Date:** YYYY-MM-DD  
**Status:** Completed | Iterative  
**Primary Seeds:** [List of seed URLs, files, or initial prompts ingested]

---

## 1. Executive Brief & Mental Model
- High-level synthesis (2-3 concise paragraphs) establishing the core mental model.
- High-level conceptual diagram or ASCII flow if visualizing architecture/data lifecycle clarifies the system.
- Plain-English definition of domain-specific concepts that were implicit or unfamiliar in the initial query.

## 2. Core Mechanics & Verified Findings
- Detailed breakdown of technical facts, APIs, data flows, and configurations.
- Direct inline code snippets, interface schemas, or config examples where relevant.
- Concrete trade-offs, constraints, and known edge cases discovered during investigation.

## 3. Gap Analysis & Resolved Prerequisites
- Foundational concepts, protocols, or platform dependencies uncovered that were not explicit in the original prompt.
- Misconceptions corrected (e.g., "Feature X is often described as Y, but the spec shows it operates as Z").

## 4. Primary Source Reference Index
Structured table of canonical sources consulted:

| Source / Spec / Repo | Entity / Authority | Specific Anchor / Section | Key Takeaway |
| :--- | :--- | :--- | :--- |
| `https://...` | Official Docs / RFC | `#section-name` | Core guarantee |

## 5. Next-Turn Exploration Vectors
Provide 3–5 concrete, pre-formulated subtopic prompts for subsequent agent turns:
1. **[Vector Name]**: Specific operational, architectural, or implementation angle to explore next.
   - *Suggested Follow-Up Prompt:* `"..."`
2. **[Vector Name]**: Specific operational, architectural, or implementation angle to explore next.
   - *Suggested Follow-Up Prompt:* `"..."`
````

---

## Gotchas & Failure Modes

- **The Secondary Source Echo Chamber**: Third-party tutorials frequently repeat outdated or incorrect assumptions. When behavior seems counter-intuitive, cross-reference the actual codebase or issue tracker.
- **Version Drift**: Documentation for version $N$ often differs fundamentally from version $N-1$ or $N+1$. Always explicitly note the software version being investigated.
- **The Context Dump**: Avoid pasting raw 20-page web scrapes into the dossier. Synthesize, distill, and present findings with clear headings and code snippets.
- **Marketing Bias**: Vendor documentation frequently obscures trade-offs. Look for GitHub issues, postmortems, and performance benchmarks to surface genuine limitations.
