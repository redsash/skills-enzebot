# skills-enzebot

A collection of agent skills designed, authored, and maintained according to the [Open Skills specification](https://agentskills.io/specification.md) and [Antigravity](https://antigravity.google/docs/skills.md) guidelines.

```bash
npx skills add redsash/skills-enzebot
```

---

## Skills Index

| Skill | Description |
| :--- | :--- |
| [competing-hypothesis](./competing-hypothesis/SKILL.md) | Evaluates ambiguous or contradictory evidence against rival explanations using Richards Heuer's Analysis of Competing Hypotheses (ACH). |
| [deeply-investigate](./deeply-investigate/SKILL.md) | Investigates complex technical topics, nascent architectures, APIs, or documents against primary sources to generate a structured dossier. |
| [human-readable](./human-readable/SKILL.md) | Removes AI cliches, robotic mannerisms, staccato phrasing, and throat-clearing from drafts to make them sound natural and human-authored. |
| [perspectives](./perspectives/SKILL.md) | Stress-tests decisions and strategic dilemmas by simulating a multi-expert advisory panel and adversarial cross-debate. |
| [research-journaler](./research-journaler/SKILL.md) | Initializes, structures, and logs reproducible research sessions into chronological journal entries. |
| [skill-architect](./skill-architect/SKILL.md) | Designs, scaffolds, evaluates, and refines agent skills according to the Open Skills specification and Antigravity guidelines. |
| [strategic-thinking-5d](./strategic-thinking-5d/SKILL.md) | Applies 5D Thinking (AQAL, Kegan stages, holarchies) to diagnose bottlenecks, stress-test POCs, and eliminate one-dimensional slop. |

---

## Skills Wishlist & Brainstorming

Candidate skills planned for development, generated through the `perspectives` advisory panel and edited with `human-readable`:

| Candidate Skill | Proposed Description |
| :--- | :--- |
| `adr-synthesizer` | Synthesizes scattered design threads, PR reviews, and RFC notes into structured Architecture Decision Records. |
| `blast-radius-audit` | Audits proposed code and infrastructure changes before execution to map dependency knock-on effects, migration risks, and rollback steps. |
| `dead-code-pruner` | Identifies and verifies unused exports, obsolete feature flags, and abandoned routes for safe deletion. |
| `flaky-test-hunter` | Isolates and reproduces non-deterministic test failures caused by race conditions, state leaks, and timing sensitivities. |
| `incident-postmortem` | Assembles incident timelines, isolates contributing system factors, and drafts blameless postmortems with concrete remediation items. |

---

## Creating & Validating Skills

To scaffold a new skill using the `skill-architect` meta-skill:

```bash
python3 skill-architect/scripts/scaffold_skill.py <skill-name> --description "<one-line description>"
```

To validate an existing skill:

```bash
python3 skill-architect/scripts/validate_skill.py <path-to-skill>
```
