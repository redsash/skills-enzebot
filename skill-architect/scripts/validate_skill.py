#!/usr/bin/env python3
"""
Validates an Agent Skill directory against the Open Skills Specification and Antigravity guidelines.

Usage:
    python3 scripts/validate_skill.py [OPTIONS] <skill-directory>

Options:
    --json       Output report as structured JSON to stdout
    --help, -h   Show this help message and exit

Checks:
    - SKILL.md exists and contains valid YAML frontmatter
    - 'name' conforms to 1-64 chars, [a-z0-9-], no consecutive hyphens, matches directory name
    - 'description' exists, non-empty, and <= 1024 characters
    - Optional fields: 'compatibility' <= 500 chars, 'metadata' is string-to-string mapping
    - SKILL.md body line count <= 500 lines (progressive disclosure recommendation)
    - Relative links in markdown reference files that exist on disk
"""

import sys
import os
import re
import argparse
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_frontmatter(content: str):
    """Extract and parse YAML frontmatter from markdown content."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, content, ["SKILL.md must begin with '---' YAML frontmatter delimiter."]

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return None, content, ["Frontmatter delimiter '---' was never closed."]

    raw_yaml = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])

    if yaml:
        try:
            data = yaml.safe_load(raw_yaml)
            if not isinstance(data, dict):
                return None, body, ["Frontmatter must be a YAML dictionary / mapping."]
            return data, body, []
        except Exception as e:
            return None, body, [f"YAML parsing error: {e}"]
    else:
        # Fallback simple parser for name & description if PyYAML is unavailable
        data = {}
        for line in raw_yaml.splitlines():
            line = line.strip()
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip("'\"")
        return data, body, []


def validate_skill(skill_dir_path: Path):
    errors = []
    warnings = []
    details = {}

    skill_dir = skill_dir_path.resolve()
    if not skill_dir.is_dir():
        errors.append(f"Directory not found: {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    dir_name = skill_dir.name
    details["dir_name"] = dir_name

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"Missing required SKILL.md file in {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Could not read SKILL.md: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    frontmatter, body, fm_errors = parse_frontmatter(content)
    if fm_errors:
        errors.extend(fm_errors)
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    # Validate name
    name = frontmatter.get("name")
    details["name"] = name
    if not name or not isinstance(name, str):
        errors.append("Frontmatter 'name' is required and must be a string.")
    else:
        if len(name) < 1 or len(name) > 64:
            errors.append(f"Skill name '{name}' must be between 1 and 64 characters (current: {len(name)}).")
        if not NAME_PATTERN.match(name):
            errors.append(f"Skill name '{name}' invalid: must be lowercase alphanumeric with hyphens, cannot start/end with hyphen or have '--'.")
        if name != dir_name:
            errors.append(f"Skill name '{name}' must match parent directory name '{dir_name}'.")

    # Validate description
    desc = frontmatter.get("description")
    details["description_length"] = len(desc) if desc else 0
    if not desc or not isinstance(desc, str) or not desc.strip():
        errors.append("Frontmatter 'description' is required and must be a non-empty string.")
    else:
        desc_len = len(desc.strip())
        if desc_len > 1024:
            errors.append(f"Description length ({desc_len} chars) exceeds maximum allowed 1024 characters.")
        if desc_len < 30:
            warnings.append(f"Description is very brief ({desc_len} chars). Consider adding triggers and context.")

    # Validate compatibility (optional)
    compat = frontmatter.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            errors.append("Optional 'compatibility' must be a string.")
        elif len(compat) > 500:
            errors.append(f"Compatibility field length ({len(compat)}) exceeds maximum allowed 500 characters.")

    # Validate metadata (optional)
    meta = frontmatter.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict):
            errors.append("Optional 'metadata' must be a key-value dictionary mapping string keys to string values.")
        else:
            for k, v in meta.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    errors.append(f"Metadata entries must be string-to-string. Invalid pair: {k}={v}")

    # Validate line count for progressive disclosure
    total_lines = len(content.splitlines())
    details["total_lines"] = total_lines
    if total_lines > 500:
        warnings.append(f"SKILL.md has {total_lines} lines (>500 lines recommended). Consider moving reference sections into references/.")

    # Validate internal relative links
    for match in MARKDOWN_LINK_PATTERN.finditer(body):
        link_target = match.group(2).strip()
        # Ignore web URLs, anchors, mailto
        if link_target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Split anchor if present
        clean_target = link_target.split("#")[0]
        if not clean_target:
            continue

        target_path = (skill_dir / clean_target).resolve()
        try:
            # Prevent directory traversal attacks
            target_path.relative_to(skill_dir)
        except ValueError:
            warnings.append(f"Relative link '{link_target}' references a path outside the skill directory.")
            continue

        if not target_path.exists():
            errors.append(f"Broken relative link in SKILL.md: '{link_target}' -> file not found.")

    # Check executable bit on scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for script_file in scripts_dir.iterdir():
            if script_file.is_file() and script_file.suffix in (".sh", ".py", ".bash"):
                if not os.access(script_file, os.X_OK):
                    warnings.append(f"Script '{script_file.name}' is not marked executable (chmod +x).")

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "details": details
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory against Open Skills and Antigravity specifications."
    )
    parser.add_argument("skill_dir", help="Path to the skill directory to validate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    skill_path = Path(args.skill_dir)

    result = validate_skill(skill_path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASSED" if result["valid"] else "FAILED"
        print(f"Validation Result: {status}")
        print(f"Skill Directory:   {skill_path.resolve()}")
        if result["details"].get("name"):
            print(f"Skill Name:        {result['details']['name']}")
        if result["details"].get("description_length"):
            print(f"Description Size:  {result['details']['description_length']} / 1024 characters")
        if result["details"].get("total_lines"):
            print(f"Line Count:        {result['details']['total_lines']} lines")

        if result["errors"]:
            print("\nErrors:")
            for err in result["errors"]:
                print(f"  [ERROR] {err}")

        if result["warnings"]:
            print("\nWarnings:")
            for warn in result["warnings"]:
                print(f"  [WARN]  {warn}")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
