#!/usr/bin/env python3
"""
Scaffolds a new Agent Skill adhering to the Open Skills Specification and Antigravity conventions.

Usage:
    python3 scripts/scaffold_skill.py <skill-name> [OPTIONS]

Options:
    --description TEXT       Initial skill description (imperative, <=1024 chars)
    --with-scripts           Create a scripts/ directory with a starter script
    --with-references        Create a references/ directory with a starter markdown file
    --with-evals             Create an evals/ directory with evals.json template
    --output-dir DIR         Target directory to scaffold into (default: current directory)
    --help, -h               Show this help message and exit
"""

import sys
import os
import re
import argparse
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def scaffold_skill(name: str, description: str, base_dir: Path, with_scripts: bool, with_references: bool, with_evals: bool):
    if len(name) < 1 or len(name) > 64:
        sys.stderr.write(f"Error: Skill name must be 1-64 characters. Received: {name}\n")
        sys.exit(1)

    if not NAME_PATTERN.match(name):
        sys.stderr.write(f"Error: Skill name '{name}' must be lowercase alphanumeric with hyphens, cannot start/end with hyphen, and cannot have consecutive hyphens.\n")
        sys.exit(1)

    skill_dir = base_dir / name
    if skill_dir.exists():
        sys.stderr.write(f"Error: Destination directory already exists: {skill_dir}\n")
        sys.exit(1)

    skill_dir.mkdir(parents=True, exist_ok=False)

    desc_text = description if description else f"Describe what {name} does and exact conditions when the agent should activate it. Use imperative phrasing."

    skill_md_content = f"""---
name: {name}
description: >-
  {desc_text}
---

# {name.replace('-', ' ').title()}

Provide concise, actionable instructions for the agent here.

## When to Use This Skill
- Use when the user requests ...
- Do not use when ...

---

## Workflow / Procedure

Progress:
- [ ] Step 1: Analyze inputs
- [ ] Step 2: Execute task
- [ ] Step 3: Validate results

### Step 1: Preparation
Specify concrete inspection or parameter validation steps.

### Step 2: Execution
Run required commands or procedures. Specify opinionated defaults.

### Step 3: Validation
Verify output against schema, tests, or success criteria before reporting completion.

---

## Gotchas & Edge Cases
- Document repository or domain-specific quirks that defy standard assumptions.

---

## Output Format
Provide an exact markdown or structured template when output consistency is required.
"""

    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    if with_scripts:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        starter_script = scripts_dir / "run.py"
        script_code = """#!/usr/bin/env python3
\"\"\"
Helper script for the skill.

Accepts CLI arguments, runs non-interactively, writes structured output to stdout
and diagnostic/logging info to stderr.
\"\"\"

import sys
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Process tasks for the skill non-interactively.")
    parser.add_argument("--dry-run", action="store_true", help="Preview operations without making changes")
    args = parser.parse_args()

    # Diagnostics to stderr
    sys.stderr.write("Starting execution...\\n")

    # Structured result to stdout
    result = {"status": "ok", "dry_run": args.dry_run}
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
"""
        starter_script.write_text(script_code, encoding="utf-8")
        os.chmod(starter_script, 0o755)

    if with_references:
        ref_dir = skill_dir / "references"
        ref_dir.mkdir(exist_ok=True)
        (ref_dir / "REFERENCE.md").write_text(f"""# {name.replace('-', ' ').title()} Reference

Detailed documentation and edge-case guides loaded on-demand.
""", encoding="utf-8")

    if with_evals:
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir(exist_ok=True)
        evals_json = {
            "skill_name": name,
            "evals": [
                {
                    "id": 1,
                    "prompt": f"Perform a representative {name} task with sample inputs.",
                    "expected_output": "Successful output adhering to the format specifications.",
                    "files": [],
                    "assertions": [
                        "The operation completed without errors",
                        "The output adheres to required structure"
                    ]
                }
            ]
        }
        import json
        (evals_dir / "evals.json").write_text(json.dumps(evals_json, indent=2), encoding="utf-8")

    print(f"Successfully scaffolded skill: {skill_dir}")
    print(f"  - SKILL.md created")
    if with_scripts:
        print(f"  - scripts/run.py created")
    if with_references:
        print(f"  - references/REFERENCE.md created")
    if with_evals:
        print(f"  - evals/evals.json created")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new Agent Skill.")
    parser.add_argument("name", help="Unique skill name (lowercase, hyphens)")
    parser.add_argument("--description", help="Initial skill description (imperative, <=1024 chars)")
    parser.add_argument("--with-scripts", action="store_true", help="Create scripts/ directory with starter run.py")
    parser.add_argument("--with-references", action="store_true", help="Create references/ directory")
    parser.add_argument("--with-evals", action="store_true", help="Create evals/ directory with evals.json template")
    parser.add_argument("--output-dir", default=".", help="Target output directory (default: .)")

    args = parser.parse_args()
    scaffold_skill(
        name=args.name,
        description=args.description,
        base_dir=Path(args.output_dir),
        with_scripts=args.with_scripts,
        with_references=args.with_references,
        with_evals=args.with_evals
    )


if __name__ == "__main__":
    main()
