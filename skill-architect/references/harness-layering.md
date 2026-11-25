# Antigravity Harness Layering, Invocation & Model Tiers

Decision rubrics for deciding **whether** a capability should be a skill (versus another Antigravity / Gemini CLI primitive), **how** it should be invoked, and **which** model/effort tier it needs.

---

## 1. Gate 0: Should This Be a Skill?

Before scaffolding a new skill, check whether a native harness primitive is a better fit. Skills shine for **reusable, on-demand domain procedures, epistemic lenses, and verification harnesses**—not always-on repo policy or generic orchestration.

| Need / Signal | Right Primitive | Why Not a Skill? |
| :--- | :--- | :--- |
| Always-on repo rules, coding standards, forbidden commands, architecture constraints | **Persistent Rule** (`AGENTS.md`, `GEMINI.md`, `.agents/rules/*.md`, e.g., `.agents/rules/code-design-principles.md`) | Rules load deterministically by directory scope (dedicated 20k-token budget, 24 KB/file) without relying on prompt-matching triggers. |
| Interactive planning, requirements alignment, or design interviews | **Native `/plan` or `/grill-me`** | Built into Antigravity CLI with structured planning UI and decision loops; duplicating this as a skill adds prompt bloat. |
| Long-running autonomous persistence ("keep working until verified") | **Native `/goal`** | Native harness manages continuation loops and completion discipline directly. |
| Deep multi-perspective reasoning or rigorous verification on a hard one-off task | **Native `/boost`** | Uses harness-level deep thinking and verification without carrying permanent startup trigger overhead. |
| Parallel multi-agent work on a shared board or scripted agent fan-out | **Native `/swarm`, `/teamwork`, or `run_workflow`** | Orchestration topology belongs to the harness. Skills compose *inside* workers rather than re-implementing multi-agent coordination. |
| Remembering a user correction or personal workflow preference across sessions | **Native `/learn`** (or rule update) | Persists preferences cleanly without adding a new triggerable skill to startup context. |
| Scheduled or delayed recurring execution | **Native `/schedule`** | Timer/cron lifecycle is managed by the runtime. |
| Context isolation, read-only exploration sandbox, or parallel delegation | **Subagent Persona** (`define_subagent` / `invoke_subagent`) | Subagents isolate context windows and permissions. Pair a subagent *with* a skill when it needs domain expertise (e.g., `deeply-investigate`). |
| Deterministic lifecycle automation (`SessionStart`, `SessionEnd`, pre/post-tool guards) | **Hook** (`hooks.json`) | Runs deterministically with zero LLM turns or token spend. |
| Pure deterministic transform, linter, or API call needing zero judgment | **Standalone CLI Script** or **MCP Server** | If `--help` + exit codes suffice with no domain heuristics, gotchas, or review criteria, keep it as a plain CLI tool. |
| **Reusable on-demand domain procedure, invariant spec, epistemic lens, or validated tool workflow** | **Agent Skill** (`.agents/skills/<name>/SKILL.md`) | Progressive disclosure loads only `name` + `description` at startup and brings in domain knowledge, gotchas, and deterministic validators only when relevant. |

### Composition Over Duplication
Skills should **compose with** Antigravity primitives rather than re-implement them:
- A `critique` or `explore` skill can instruct the agent to delegate heavy read-only work to a subagent *when supported by the harness* (with a sequential fallback for Gemini CLI).
- A `maintain` skill can pair a CLI engine in `scripts/` with optional `hooks.json` lifecycle triggers documented in `references/` (see `engineering-log`).
- Never bundle generic multi-step progress-tracking frameworks inside a skill—Antigravity's `update_steps` and `/plan` handle live checklists natively.

---

## 2. Invocation Posture (`metadata.invocation`)

Separate **how a skill triggers** (`metadata.invocation`) from **how it behaves once active** (`taxonomy.interaction`: `interactive` vs. `autonomous`).

| Value | Meaning | Best Used For | Description Guidance |
| :--- | :--- | :--- | :--- |
| **`auto`** | Agent routes to the skill automatically from user intent. | Low blast-radius, high-precision domain tasks where silent activation adds clear value (e.g., `human-readable`, `discord-webhook-script-writer`, `cad-floorplan-designer`). | Third-person capability + concrete trigger keywords + explicit `Do not use for...` non-triggers. |
| **`manual`** | Activated explicitly via `/skill-name` or direct user request; should not hijack routine turns. | High blast-radius actions, session-end capture, heavy cognitive frameworks, or opinionated lenses that alter tone/workflow (e.g., destructive ops, `/engineering-log`, `/perspectives`). | Begin trigger clause with `"Use only when explicitly invoked via /<skill-name> or when the user directly asks for..."` plus explicit non-triggers. |
| **`hybrid`** | Primary path is `/skill-name`, with narrow, unambiguous ambient triggers. | Meta-tooling and specialized workflows that users often invoke by name but occasionally describe verbatim (e.g., `skill-architect`, `quant-edge-auditor`). | List `/<skill-name>` alongside narrow, unmistakable trigger intents and explicit exclusions. |

---

## 3. Model & Effort Tier Guidance (`metadata.model-tier`, `metadata.effort`)

Record capability-based hints—not brittle model version strings—inside the Open Skills standard `metadata` map so manifests stay valid across Antigravity CLI, Gemini CLI, and future model generations:

```yaml
metadata:
  model-tier: "standard"   # fast | standard | deep | orchestrator
  effort: "medium"         # low | medium | high
  invocation: "auto"       # auto | manual | hybrid
```

### Capability Tier Mapping (Current Roster)

| `model-tier` | Typical `effort` | Current Model Calibration | Ideal Skill Profile |
| :--- | :--- | :--- | :--- |
| **`fast`** | `low`–`medium` | Gemini 4 Hydrogen, Gemini 4 Carbon, Gemini 3.8 Flash | Scripted capture, deterministic harness runners, linting, single-pass prose cleanup (e.g., `human-readable`, `research-journaler`, scripted `engineering-log`). |
| **`standard`** | `medium` | Gemini 4 Neon (Medium), Claude 5.5 (Standard) | Standard multi-step authoring, refactoring, CLI script generation, structured reviews (`discord-webhook-script-writer`). |
| **`deep`** | `high` | Gemini 4 Neon (High), Claude 5.5 (High) | Multi-step build-and-verify, adversarial critique, high-stakes deliberation, complex invariant satisfaction (`skill-architect`, `competing-hypothesis`, `perspectives`, `cad-floorplan-designer`). |
| **`orchestrator`** | `high` | Orchestrator, or Neon High + subagents / `/swarm` | Multi-stage pipelines with parallel research/audit fan-out and synthesis (`deeply-investigate`, multi-stage `quant-edge-auditor`). |

### Dual-Harness Calibration (Antigravity + Gemini CLI Flash 3.8)
- Skills targeting `fast` or shared with **Gemini CLI (Flash 3.8)** must lean hardest on **deterministic scripts in `scripts/`**, **concrete output schemas**, and **hard exit criteria** so smaller models never improvise fragile shell pipelines or skip verification.
- Skills targeting `deep` or `orchestrator` should avoid verbose step-by-step reasoning scripts that constrain strong models; invest context budget in **non-obvious invariants, edge-case gotchas, and falsifiable verification gates**.
