# skills-enzebot

A collection of agent skills designed, authored, and maintained according to the [Open Skills specification](https://agentskills.io/specification.md) and [Antigravity](https://antigravity.google/docs/skills.md) guidelines.

---

## Skills Index

| Skill | Description |
| :--- | :--- |
| [skill-architect](./skill-architect/SKILL.md) | Designs, scaffolds, evaluates, and refines agent skills according to the Open Skills specification and Antigravity guidelines. |
| [human-readable](./human-readable/SKILL.md) | Removes AI cliches, robotic mannerisms, staccato phrasing, and throat-clearing from drafts to make them sound natural and human-authored. |
| [deeply-investigate](./deeply-investigate/SKILL.md) | Investigates complex technical topics, nascent architectures, APIs, or documents against primary sources to generate a structured dossier. |
| [perspectives](./perspectives/SKILL.md) | Stress-tests decisions and strategic dilemmas by simulating a multi-expert advisory panel and adversarial cross-debate. |
| [competing-hypothesis](./competing-hypothesis/SKILL.md) | Evaluates ambiguous or contradictory evidence against rival explanations using Richards Heuer's Analysis of Competing Hypotheses (ACH). |

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
