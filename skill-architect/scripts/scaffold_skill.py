#!/usr/bin/env python3
"""
Scaffolds a new Agent Skill adhering to the Open Skills Specification,
Antigravity layering standards, progressive disclosure, and repo taxonomy.

Usage:
    python3 skill-architect/scripts/scaffold_skill.py <skill-name> [OPTIONS]

Options:
    --description TEXT         Third-person description with triggers & non-triggers (<=1024 chars)
    --phase PHASE              Cognitive phase (explore|deliberate|author|critique|maintain|meta)
    --modality MODALITY        Operational modality (lens|spec|runbook|harness)
    --domain SLUG              Domain vertical slug (default: software-engineering)
    --interaction MODE         Execution dialogue mode (interactive|autonomous)
    --model-tier TIER          Recommended model capability tier (fast|standard|deep|orchestrator)
    --effort LEVEL             Recommended reasoning effort (low|medium|high)
    --invocation MODE          Triggering posture (auto|manual|hybrid)
    --with-scripts             Create scripts/ directory with black-box starter run.py
    --with-references          Create references/ directory with starter REFERENCE.md
    --with-examples            Create examples/ directory with starter example.md
    --with-evals               Create evals/ directory with evals.json template
    --output-dir DIR           Target parent directory (default: current directory)
    --dry-run                  Preview files that would be created without writing to disk
    --help, -h                 Show this help message and exit

Examples:
    python3 skill-architect/scripts/scaffold_skill.py log-triage --phase explore --modality runbook --dry-run
    python3 skill-architect/scripts/scaffold_skill.py schema-guard --phase critique --modality harness --with-scripts --with-evals
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def build_skill_files(
    name: str,
    description: Optional[str],
    with_scripts: bool,
    with_references: bool,
    with_examples: bool,
    with_evals: bool,
    phase: str = "author",
    modality: str = "runbook",
    domain: str = "software-engineering",
    interaction: Optional[str] = None,
    model_tier: str = "standard",
    effort: str = "medium",
    invocation: str = "auto",
) -> Dict[str, str]:
    title = name.replace("-", " ").title()
    trigger_hint = f"Use on /{name} or when ..." if invocation in ("manual", "hybrid") else "Use when ..."
    desc_text = (
        description.strip()
        if description
        else f"Performs {title.lower()} workflows adhering to domain invariants. {trigger_hint} Do not use for unrelated tasks or always-on repo rules in AGENTS.md."
    )

    interaction_line = f"\n  interaction: {interaction}" if interaction else ""

    resource_lines = []
    if with_references:
        resource_lines.append("- **References** *(read on demand)*: [Deep-Dive Reference](references/REFERENCE.md)")
    if with_examples:
        resource_lines.append("- **Examples** *(read on demand)*: [Worked Example](examples/example.md)")
    if with_scripts:
        resource_lines.append(
            "- **Bundled Scripts (Black-Box)**: Treat `scripts/` as black boxes—run `--help` first to inspect flags and execute directly rather than reading script source into context unless debugging or modifying the script.\n"
            "  - `python3 scripts/run.py --help`"
        )

    resources_block = ""
    if resource_lines:
        resources_block = "## Quick Reference & Bundled Resources\n\n" + "\n".join(resource_lines) + "\n\n---\n\n"

    exec_example = (
        "```bash\npython3 scripts/run.py --dry-run\n```"
        if with_scripts
        else "Execute the domain procedure using the opinionated defaults above."
    )
    verify_gate = (
        "`python3 scripts/run.py --verify` exits `0`."
        if with_scripts
        else "Deterministic verification / tests exit `0`."
    )

    skill_md_content = f"""---
name: {name}
description: >-
  {desc_text}
taxonomy:
  phase: [{phase}]
  modality: [{modality}]
  domain: [{domain}]{interaction_line}
metadata:
  model-tier: "{model_tier}"
  effort: "{effort}"
  invocation: "{invocation}"
---

# {title}

[1-2 sentence orientation: exact goal state and operational scope.]

---

{resources_block}## Goal & Hard Invariants

- **Goal**: [Observable end-state that defines success.]
- **Invariant 1**: [Non-negotiable domain constraint.]
- **Invariant 2**: [Opinionated default + explicit escape hatch.]
- **Scope Boundary**: Do not use this skill for [near-miss task]; use [sibling skill / `AGENTS.md` / native workflow] instead.

---

## Decision Tree & Execution Protocol

Follow **Plan → Use/Verify with Tools → Iterate**:

1. **Inspect & Plan**: Gather concrete inputs/ground truth and check constraints before acting.
   - *If [branch condition A]* → [take path A].
   - *If [branch condition B]* → [stop and ask user / fall back].
2. **Execute**:
   {exec_example}
3. **Iterate**: Fix all reported defects from validation and re-verify until clean.

---

## Verification & Exit Criteria

Do not report completion until every gate passes:
- [ ] {verify_gate}
- [ ] All hard invariants above are satisfied with concrete evidence.
- [ ] Output conforms strictly to the Output Contract below.

---

## Gotchas & Failure Modes

- **[Gotcha 1]**: [Non-obvious environment, API, or data quirk that contradicts reasonable assumptions.]

---

## Output Contract

```markdown
# {title} Result
- **Status:** `[PASS | FAIL]`
- **Summary:** `[Concise verified result]`
```
"""

    files: Dict[str, str] = {"SKILL.md": skill_md_content}

    if with_scripts:
        files["scripts/run.py"] = '''#!/usr/bin/env python3
"""
Black-box helper script for the skill.

Runs non-interactively via CLI flags, writes structured JSON to stdout,
and writes diagnostic logs to stderr.

Examples:
    python3 scripts/run.py --dry-run
    python3 scripts/run.py --verify
"""

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute deterministic operations for this skill non-interactively."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview operations without modifying state")
    parser.add_argument("--verify", action="store_true", help="Run deterministic verification checks")
    args = parser.parse_args()

    sys.stderr.write("Starting execution...\\n")
    result = {"status": "ok", "dry_run": args.dry_run, "verified": args.verify}
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
'''

    if with_references:
        files["references/REFERENCE.md"] = f"""# {title} Reference

Detailed domain schemas, tables, and edge-case documentation loaded on demand.
"""

    if with_examples:
        files["examples/example.md"] = f"""# {title} Worked Example

Concrete input and verified output demonstrating expected behavior.
"""

    if with_evals:
        evals_json = {
            "skill_name": name,
            "evals": [
                {
                    "id": 1,
                    "prompt": f"Perform a representative {name} task with sample inputs.",
                    "expected_output": "Successful output adhering to invariants and output contract.",
                    "files": [],
                    "assertions": [
                        "The operation completed without errors",
                        "All hard invariants and output format requirements are met",
                    ],
                }
            ],
        }
        files["evals/evals.json"] = json.dumps(evals_json, indent=2) + "\n"

    return files


def scaffold_skill(
    name: str,
    description: Optional[str],
    base_dir: Path,
    with_scripts: bool,
    with_references: bool,
    with_examples: bool,
    with_evals: bool,
    phase: str = "author",
    modality: str = "runbook",
    domain: str = "software-engineering",
    interaction: Optional[str] = None,
    model_tier: str = "standard",
    effort: str = "medium",
    invocation: str = "auto",
    dry_run: bool = False,
) -> None:
    if len(name) < 1 or len(name) > 64:
        sys.stderr.write(f"Error: Skill name must be 1-64 characters. Received: {name}\n")
        sys.exit(1)

    if not NAME_PATTERN.match(name):
        sys.stderr.write(
            f"Error: Skill name '{name}' must be lowercase alphanumeric with hyphens, "
            "cannot start/end with hyphen, and cannot have consecutive hyphens.\n"
        )
        sys.exit(1)

    if not NAME_PATTERN.match(domain):
        sys.stderr.write(f"Error: Domain '{domain}' must be lowercase kebab-case.\n")
        sys.exit(1)

    skill_dir = base_dir / name
    if skill_dir.exists():
        sys.stderr.write(f"Error: Destination directory already exists: {skill_dir}\n")
        sys.exit(1)

    files = build_skill_files(
        name=name,
        description=description,
        with_scripts=with_scripts,
        with_references=with_references,
        with_examples=with_examples,
        with_evals=with_evals,
        phase=phase,
        modality=modality,
        domain=domain,
        interaction=interaction,
        model_tier=model_tier,
        effort=effort,
        invocation=invocation,
    )

    if dry_run:
        print(f"[DRY-RUN] Would scaffold skill at: {skill_dir.resolve()}")
        for rel_path in files:
            print(f"  - {rel_path}")
        return

    skill_dir.mkdir(parents=True, exist_ok=False)
    for rel_path, content in files.items():
        target = skill_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if rel_path.startswith("scripts/") and target.suffix in (".py", ".sh", ".bash"):
            os.chmod(target, 0o755)

    print(f"Successfully scaffolded skill: {skill_dir.resolve()}")
    for rel_path in files:
        print(f"  - {rel_path} created")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Agent Skill adhering to Open Skills and Antigravity standards."
    )
    parser.add_argument("name", help="Unique skill name (lowercase, hyphens)")
    parser.add_argument("--description", help="Third-person description with triggers & non-triggers (<=1024 chars)")
    parser.add_argument("--with-scripts", action="store_true", help="Create scripts/ directory with black-box starter run.py")
    parser.add_argument("--with-references", action="store_true", help="Create references/ directory")
    parser.add_argument("--with-examples", action="store_true", help="Create examples/ directory")
    parser.add_argument("--with-evals", action="store_true", help="Create evals/ directory with evals.json template")
    parser.add_argument(
        "--phase",
        default="author",
        choices=["explore", "deliberate", "author", "critique", "maintain", "meta"],
        help="Cognitive phase (default: author)",
    )
    parser.add_argument(
        "--modality",
        default="runbook",
        choices=["lens", "spec", "runbook", "harness"],
        help="Operational modality (default: runbook)",
    )
    parser.add_argument("--domain", default="software-engineering", help="Domain vertical slug (default: software-engineering)")
    parser.add_argument("--interaction", choices=["interactive", "autonomous"], default=None, help="Optional execution dialogue mode")
    parser.add_argument(
        "--model-tier",
        default="standard",
        choices=["fast", "standard", "deep", "orchestrator"],
        help="Recommended model capability tier (default: standard)",
    )
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high"], help="Recommended reasoning effort (default: medium)")
    parser.add_argument("--invocation", default="auto", choices=["auto", "manual", "hybrid"], help="Triggering posture (default: auto)")
    parser.add_argument("--output-dir", default=".", help="Target output directory (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="Preview files without writing to disk")

    args = parser.parse_args()
    scaffold_skill(
        name=args.name,
        description=args.description,
        base_dir=Path(args.output_dir),
        with_scripts=args.with_scripts,
        with_references=args.with_references,
        with_examples=args.with_examples,
        with_evals=args.with_evals,
        phase=args.phase,
        modality=args.modality,
        domain=args.domain,
        interaction=args.interaction,
        model_tier=args.model_tier,
        effort=args.effort,
        invocation=args.invocation,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
